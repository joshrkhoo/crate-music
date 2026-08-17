import asyncio
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from app.config import LASTFM_API_URL

SEED_ARTISTS = 8
SIMILAR_ARTISTS = 5
TOP_TRACKS = 4


def lastfm_api_key() -> str:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
    return os.getenv("LASTFM_API_KEY", "").strip()


def _as_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


async def _lastfm_get(client: httpx.AsyncClient, method: str, artist: str, extra: dict) -> dict:
    api_key = lastfm_api_key()
    if not api_key:
        return {}
    response = await client.get(
        LASTFM_API_URL,
        params={
            "method": method,
            "artist": artist,
            "api_key": api_key,
            "format": "json",
            **extra,
        },
        headers={"User-Agent": "crate-music/0.1"},
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError:
        return {}
    if not isinstance(payload, dict) or payload.get("error"):
        return {}
    return payload


def _similar_names(payload: dict) -> list[str]:
    artists = _as_list((payload.get("similarartists") or {}).get("artist"))
    names = []
    for item in artists:
        name = item.get("name") if isinstance(item, dict) else None
        if name:
            names.append(name)
    return names


def _top_tracks(payload: dict, artist: str) -> list[tuple[str, str]]:
    tracks = _as_list((payload.get("toptracks") or {}).get("track"))
    results: list[tuple[str, str]] = []
    for item in tracks:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        artist_name = ((item.get("artist") or {}).get("name") if isinstance(item.get("artist"), dict) else artist)
        if name and artist_name:
            results.append((name, artist_name))
    return results


async def similar_artist_names(
    artist: str,
    client: httpx.AsyncClient | None = None,
) -> list[str]:
    if client is None:
        async with httpx.AsyncClient(timeout=20) as owned:
            payload = await _lastfm_get(
                owned,
                "artist.getsimilar",
                artist,
                {"limit": str(SIMILAR_ARTISTS)},
            )
        return _similar_names(payload)
    payload = await _lastfm_get(
        client,
        "artist.getsimilar",
        artist,
        {"limit": str(SIMILAR_ARTISTS)},
    )
    return _similar_names(payload)


async def top_track_names(
    artist: str,
    client: httpx.AsyncClient | None = None,
) -> list[tuple[str, str]]:
    if client is None:
        async with httpx.AsyncClient(timeout=20) as owned:
            payload = await _lastfm_get(
                owned,
                "artist.gettoptracks",
                artist,
                {"limit": str(TOP_TRACKS)},
            )
        return _top_tracks(payload, artist)
    payload = await _lastfm_get(
        client,
        "artist.gettoptracks",
        artist,
        {"limit": str(TOP_TRACKS)},
    )
    return _top_tracks(payload, artist)


def seed_artist_names(playlist_tracks: list[dict], limit: int = SEED_ARTISTS) -> list[str]:
    counts: dict[str, int] = {}
    order: list[str] = []
    for item in playlist_tracks:
        for artist in item.get("track", {}).get("artists") or []:
            name = artist.get("name")
            if not name:
                continue
            if name not in counts:
                order.append(name)
            counts[name] = counts.get(name, 0) + 1
    order.sort(key=lambda name: counts[name], reverse=True)
    return order[:limit]


async def candidate_track_refs(playlist_tracks: list[dict]) -> list[tuple[str, str]]:
    seeds = seed_artist_names(playlist_tracks)
    if not seeds:
        return []

    similar: list[str] = []
    semaphore = asyncio.Semaphore(4)

    async with httpx.AsyncClient(timeout=20) as client:

        async def fetch_similar(artist: str) -> list[str]:
            async with semaphore:
                try:
                    return await similar_artist_names(artist, client)
                except httpx.HTTPError:
                    return []

        for names in await asyncio.gather(*(fetch_similar(artist) for artist in seeds)):
            similar.extend(names)

        unique_artists: list[str] = []
        seen_artists: set[str] = {name.lower() for name in seeds}
        for name in similar:
            key = name.lower()
            if key in seen_artists:
                continue
            seen_artists.add(key)
            unique_artists.append(name)

        refs: list[tuple[str, str]] = []
        seen_tracks: set[tuple[str, str]] = set()

        async def fetch_top(artist: str) -> list[tuple[str, str]]:
            async with semaphore:
                try:
                    return await top_track_names(artist, client)
                except httpx.HTTPError:
                    return []

        for tracks in await asyncio.gather(*(fetch_top(artist) for artist in unique_artists)):
            for name, artist in tracks:
                key = (name.lower(), artist.lower())
                if key in seen_tracks:
                    continue
                seen_tracks.add(key)
                refs.append((name, artist))

        return refs
