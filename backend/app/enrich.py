import asyncio
import json
from pathlib import Path

import httpx

from app.config import SPOTIFY_API_BASE
from app.embed import CACHE_DIR
from app.spotify import _auth_headers

CONCURRENCY = 4
ARTIST_FETCH_TIMEOUT = 4.0
ARTIST_CACHE_DIR = CACHE_DIR / "artists"


def release_year(value: str | None) -> int | None:
    if not value or len(value) < 4 or not value[:4].isdigit():
        return None
    year = int(value[:4])
    if year < 1000 or year > 2100:
        return None
    return year


def unique_ids(values: list[str | None]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _artist_cache_path(artist_id: str) -> Path:
    return ARTIST_CACHE_DIR / f"{artist_id}.json"


def _load_cached_artists(artist_ids: list[str]) -> dict[str, dict]:
    cached: dict[str, dict] = {}
    for artist_id in artist_ids:
        path = _artist_cache_path(artist_id)
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            cached[artist_id] = payload
    return cached


def _save_cached_artist(artist_id: str, payload: dict) -> None:
    ARTIST_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _artist_cache_path(artist_id).write_text(
        json.dumps(
            {
                "id": artist_id,
                "genres": [
                    genre
                    for genre in payload.get("genres") or []
                    if isinstance(genre, str) and genre
                ],
            }
        )
    )


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
) -> dict | None:
    for _ in range(2):
        response = await client.get(url, headers=headers)
        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", "1"))
            await asyncio.sleep(min(retry_after, 2))
            continue
        if response.status_code >= 400:
            return None
        payload = response.json()
        return payload if isinstance(payload, dict) else None
    return None


async def _fetch_artists(
    access_token: str,
    artist_ids: list[str],
    timeout: float | None,
) -> dict[str, dict]:
    if not artist_ids:
        return {}

    headers = _auth_headers(access_token)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    results: dict[str, dict] = {}

    async with httpx.AsyncClient(timeout=10) as client:

        async def fetch_one(artist_id: str) -> None:
            async with semaphore:
                payload = await _get_json(
                    client,
                    f"{SPOTIFY_API_BASE}/artists/{artist_id}",
                    headers,
                )
                if not payload:
                    return
                results[artist_id] = payload
                _save_cached_artist(artist_id, payload)

        tasks = [asyncio.create_task(fetch_one(artist_id)) for artist_id in artist_ids]
        if timeout is None:
            await asyncio.gather(*tasks, return_exceptions=True)
            return results

        done, pending = await asyncio.wait(tasks, timeout=timeout)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        return results


def _merge_genres(artists: list[dict], artist_payloads: dict[str, dict]) -> list[str]:
    genres: list[str] = []
    seen: set[str] = set()
    for artist in artists:
        payload = artist_payloads.get(artist["id"]) or {}
        for genre in payload.get("genres") or []:
            if isinstance(genre, str) and genre and genre not in seen:
                seen.add(genre)
                genres.append(genre)
    return genres


async def enrich_tracks(
    access_token: str,
    tracks: list[dict],
    *,
    fetch_timeout: float | None = ARTIST_FETCH_TIMEOUT,
) -> list[dict]:
    artist_ids = unique_ids(
        [artist["id"] for track in tracks for artist in track.get("artists") or []]
    )
    artist_payloads = _load_cached_artists(artist_ids)
    missing_ids = [artist_id for artist_id in artist_ids if artist_id not in artist_payloads]
    if missing_ids and fetch_timeout != 0:
        artist_payloads.update(
            await _fetch_artists(access_token, missing_ids, timeout=fetch_timeout)
        )

    enriched: list[dict] = []
    for track in tracks:
        enriched.append(
            {
                "track": {
                    "id": track["id"],
                    "name": track["name"],
                    "artists": track["artists"],
                    "album": track["album"],
                },
                "release_year": release_year(track.get("release_date")),
                "genres": _merge_genres(track.get("artists") or [], artist_payloads),
            }
        )

    return enriched
