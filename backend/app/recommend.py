import asyncio
from urllib.parse import quote

# import httpx

from app.embed import embed_tracks
from app.enrich import enrich_tracks
from app.lastfm import candidate_track_refs, lastfm_api_key
from app.similarity import max_similarity_to_playlist
# from app.spotify import SpotifySearchLimiter, search_track
from app.timing import log_call, log_stage, stage_elapsed, stage_start

MAX_TRY = 50
# MIN_RESOLVED = 10
# RESOLVE_SECONDS = 60
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


def _lastfm_track(name: str, artist: str) -> dict:
    return {
        "id": f"lfm:{quote(name, safe='')}|{quote(artist, safe='')}",
        "name": name,
        "artists": [{"id": f"lfm-artist:{quote(artist, safe='')}", "name": artist}],
        "album": "",
        "image_url": None,
        "release_date": None,
    }


def _lastfm_fallback(
    refs: list[tuple[str, str]],
    owned_names: set[tuple[str, str]],
    owned_ids: set[str],
    *,
    limit: int,
) -> list[dict]:
    resolved: list[dict] = []
    for name, artist in refs:
        if (name.strip().lower(), artist.strip().lower()) in owned_names:
            continue
        mapped = _lastfm_track(name, artist)
        if mapped["id"] in owned_ids:
            continue
        owned_ids.add(mapped["id"])
        resolved.append(mapped)
        if len(resolved) >= limit:
            break
    return resolved


async def recommend_new_tracks(access_token: str, playlist_tracks: list[dict]) -> list[dict]:
    if not lastfm_api_key():
        raise RuntimeError(
            "Add LASTFM_API_KEY to backend/.env from https://www.last.fm/api/account/create"
        )

    total_start = stage_start()
    owned_ids, owned_names = _owned_keys(playlist_tracks)
    log_call(
        "recommend start",
        playlist_tracks=len(playlist_tracks),
        owned_ids=len(owned_ids),
    )

    lastfm_start = stage_start()
    refs = await candidate_track_refs(playlist_tracks)
    log_stage("recommend lastfm", stage_elapsed(lastfm_start), refs=len(refs))

    to_try: list[tuple[str, str]] = []
    skipped_in_playlist = 0
    for name, artist in refs:
        if (name.strip().lower(), artist.strip().lower()) in owned_names:
            skipped_in_playlist += 1
            continue
        to_try.append((name, artist))
        if len(to_try) >= MAX_TRY:
            break

    resolve_start = stage_start()
    resolve_source = "lastfm"

    # Spotify search disabled while Dev Mode search quota is exhausted.
    # Uncomment to resolve Last.fm names → Spotify track IDs (album art, direct links).
    #
    # limiter = SpotifySearchLimiter()
    # resolved: list[dict] = []
    # skipped_owned = 0
    # resolve_source = "spotify"
    #
    # async with httpx.AsyncClient(timeout=10) as client:
    #     for name, artist in to_try:
    #         if len(resolved) >= MIN_RESOLVED:
    #             break
    #         if limiter.quota_exceeded:
    #             break
    #         if stage_elapsed(resolve_start) >= RESOLVE_SECONDS:
    #             log_call("recommend resolve_timeout", resolved=len(resolved))
    #             break
    #
    #         mapped = await search_track(
    #             access_token,
    #             name,
    #             artist,
    #             client,
    #             limiter=limiter,
    #         )
    #         if not mapped:
    #             continue
    #         if mapped["id"] in owned_ids:
    #             skipped_owned += 1
    #             log_call(
    #                 "recommend skip_owned",
    #                 track=repr(mapped.get("name")),
    #                 id=mapped["id"],
    #             )
    #             continue
    #         owned_ids.add(mapped["id"])
    #         resolved.append(mapped)
    #         log_call(
    #             "recommend resolved",
    #             count=len(resolved),
    #             source="spotify",
    #             track=repr(mapped.get("name")),
    #             artist=repr((mapped.get("artists") or [{}])[0].get("name")),
    #         )
    #
    # if len(resolved) < MIN_RESOLVED:
    #     resolve_source = "lastfm" if limiter.quota_exceeded else "lastfm_partial"
    #     fallback = _lastfm_fallback(
    #         refs,
    #         owned_names,
    #         owned_ids,
    #         limit=MAX_TRY,
    #     )
    #     if fallback:
    #         log_call(
    #             "recommend fallback",
    #             reason="QUOTA_EXCEEDED" if limiter.quota_exceeded else "insufficient_spotify",
    #             spotify_resolved=len(resolved),
    #             lastfm_added=len(fallback),
    #         )
    #         resolved.extend(fallback)

    resolved = _lastfm_fallback(refs, owned_names, owned_ids, limit=MAX_TRY)
    log_call(
        "recommend candidates",
        lastfm_refs=len(refs),
        already_in_playlist=skipped_in_playlist,
        to_try=len(to_try),
        resolved=len(resolved),
        source=resolve_source,
    )

    log_stage(
        "recommend resolve",
        stage_elapsed(resolve_start),
        source=resolve_source,
        resolved=len(resolved),
        already_in_playlist=skipped_in_playlist,
    )

    if not resolved:
        log_stage("recommend total", stage_elapsed(total_start), returned=0)
        return []

    enrich_start = stage_start()
    enriched = await enrich_tracks(access_token, resolved, fetch_artists=False)
    log_stage("recommend enrich", stage_elapsed(enrich_start), tracks=len(enriched))

    embed_start = stage_start()
    embedded = await asyncio.to_thread(embed_tracks, enriched)
    log_stage("recommend embed", stage_elapsed(embed_start), tracks=len(embedded))

    rank_start = stage_start()
    ranked = max_similarity_to_playlist(playlist_tracks, embedded, limit=TOP_N)
    log_stage("recommend rank", stage_elapsed(rank_start), returned=len(ranked))
    log_stage("recommend total", stage_elapsed(total_start), returned=len(ranked))
    return [
        {**track, "similarity": round(score, 4)}
        for score, track in ranked
    ]
