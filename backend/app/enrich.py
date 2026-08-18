import asyncio
import json
import logging
from pathlib import Path

import httpx

from app.config import SPOTIFY_API_BASE
from app.embed import CACHE_DIR
from app.spotify import _auth_headers
from app.timing import log_stage, stage_elapsed, stage_start

log = logging.getLogger("crate.timing")

ARTIST_BATCH_SIZE = 50
ARTIST_CACHE_DIR = CACHE_DIR / "artists"

_memory_artists: dict[str, dict] = {}
_batch_artists_blocked: bool | None = None


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
        memory = _memory_artists.get(artist_id)
        if memory:
            cached[artist_id] = memory
            continue
        path = _artist_cache_path(artist_id)
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            _memory_artists[artist_id] = payload
            cached[artist_id] = payload
    return cached


def _save_cached_artist(artist_id: str, payload: dict) -> None:
    stored = {
        "id": artist_id,
        "genres": [
            genre
            for genre in payload.get("genres") or []
            if isinstance(genre, str) and genre
        ],
    }
    _memory_artists[artist_id] = stored
    ARTIST_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _artist_cache_path(artist_id).write_text(json.dumps(stored))


async def _spotify_get(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    *,
    params: dict | None = None,
) -> tuple[int, dict | None]:
    for attempt in range(3):
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", "1"))
            await asyncio.sleep(min(retry_after, 5))
            continue
        if response.status_code >= 400:
            return response.status_code, None
        payload = response.json()
        return response.status_code, payload if isinstance(payload, dict) else None
    return 429, None


def _store_batch_artists(results: dict[str, dict], payload: dict) -> None:
    for artist in payload.get("artists") or []:
        if not isinstance(artist, dict) or not artist.get("id"):
            continue
        artist_id = artist["id"]
        results[artist_id] = artist
        _save_cached_artist(artist_id, artist)


async def _fetch_artists_batch(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    artist_ids: list[str],
) -> tuple[dict[str, dict], str]:
    global _batch_artists_blocked

    if not artist_ids:
        return {}, "none"

    if _batch_artists_blocked:
        return {}, "batch_blocked"

    chunks = [
        artist_ids[index : index + ARTIST_BATCH_SIZE]
        for index in range(0, len(artist_ids), ARTIST_BATCH_SIZE)
    ]
    results: dict[str, dict] = {}

    for chunk in chunks:
        status, payload = await _spotify_get(
            client,
            f"{SPOTIFY_API_BASE}/artists",
            headers,
            params={"ids": ",".join(chunk)},
        )
        if status in (403, 404):
            _batch_artists_blocked = True
            log.warning(
                "crate batch GET /artists blocked (status=%d); "
                "using cached genres only — no per-id fallback",
                status,
            )
            return results, "batch_blocked"
        if payload is None:
            log.warning("crate batch GET /artists failed status=%d chunk=%d", status, len(chunk))
            continue
        _store_batch_artists(results, payload)

    if not results and _batch_artists_blocked:
        return {}, "batch_blocked"
    return results, "batch"


async def _fetch_artists(
    access_token: str,
    artist_ids: list[str],
) -> tuple[dict[str, dict], str]:
    if not artist_ids:
        return {}, "none"

    headers = _auth_headers(access_token)
    start = stage_start()

    async with httpx.AsyncClient(timeout=20) as client:
        results, mode = await _fetch_artists_batch(client, headers, artist_ids)

    log_stage(
        "analyse artist_fetch",
        stage_elapsed(start),
        mode=mode,
        requested=len(artist_ids),
        fetched=len(results),
        batches=(len(artist_ids) + ARTIST_BATCH_SIZE - 1) // ARTIST_BATCH_SIZE,
    )
    return results, mode


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
    fetch_artists: bool = True,
) -> list[dict]:
    start = stage_start()
    artist_ids = unique_ids(
        [artist["id"] for track in tracks for artist in track.get("artists") or []]
    )
    artist_payloads = _load_cached_artists(artist_ids)
    cache_hits = len(artist_payloads)
    missing_ids = [artist_id for artist_id in artist_ids if artist_id not in artist_payloads]

    fetch_mode = "cache_only"
    if missing_ids and fetch_artists:
        fetched, fetch_mode = await _fetch_artists(access_token, missing_ids)
        artist_payloads.update(fetched)

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

    log_stage(
        "analyse enrichment",
        stage_elapsed(start),
        tracks=len(tracks),
        artists_unique=len(artist_ids),
        cache_hits=cache_hits,
        fetched=len(missing_ids) if fetch_mode != "cache_only" else 0,
        mode=fetch_mode,
    )
    return enriched
