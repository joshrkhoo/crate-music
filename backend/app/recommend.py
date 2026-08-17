import asyncio

import httpx

from app.embed import embed_tracks
from app.enrich import enrich_tracks
from app.lastfm import candidate_track_refs, lastfm_api_key
from app.similarity import max_similarity_to_playlist
from app.spotify import search_track

MAX_RESOLVE = 80
TOP_N = 10


def _owned_keys(playlist_tracks: list[dict]) -> tuple[set[str], set[tuple[str, str]]]:
    ids: set[str] = set()
    names: set[tuple[str, str]] = set()
    for item in playlist_tracks:
        track = item.get("track") or {}
        if track.get("id"):
            ids.add(track["id"])
        title = (track.get("name") or "").strip().lower()
        for artist in track.get("artists") or []:
            artist_name = (artist.get("name") or "").strip().lower()
            if title and artist_name:
                names.add((title, artist_name))
    return ids, names


async def recommend_new_tracks(access_token: str, playlist_tracks: list[dict]) -> list[dict]:
    if not lastfm_api_key():
        raise RuntimeError(
            "Add LASTFM_API_KEY to backend/.env from https://www.last.fm/api/account/create"
        )

    owned_ids, owned_names = _owned_keys(playlist_tracks)
    refs = await candidate_track_refs(playlist_tracks)

    filtered: list[tuple[str, str]] = []
    for name, artist in refs:
        if (name.strip().lower(), artist.strip().lower()) in owned_names:
            continue
        filtered.append((name, artist))
        if len(filtered) >= MAX_RESOLVE:
            break

    semaphore = asyncio.Semaphore(4)
    resolved: list[dict] = []

    async with httpx.AsyncClient(timeout=20) as client:

        async def resolve(name: str, artist: str) -> dict | None:
            async with semaphore:
                return await search_track(access_token, name, artist, client)

        for mapped in await asyncio.gather(*(resolve(name, artist) for name, artist in filtered)):
            if not mapped or mapped["id"] in owned_ids:
                continue
            owned_ids.add(mapped["id"])
            resolved.append(mapped)

    if not resolved:
        return []

    enriched = await enrich_tracks(access_token, resolved)
    embedded = await asyncio.to_thread(embed_tracks, enriched)
    ranked = max_similarity_to_playlist(playlist_tracks, embedded, limit=TOP_N)
    return [
        {**track, "similarity": round(score, 4)}
        for score, track in ranked
    ]
