import asyncio

import httpx

from app.config import SPOTIFY_API_BASE
from app.spotify import _auth_headers

CONCURRENCY = 6


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


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
) -> dict | None:
    for _ in range(2):
        response = await client.get(url, headers=headers)
        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", "1"))
            await asyncio.sleep(min(retry_after, 3))
            continue
        if response.status_code >= 400:
            return None
        payload = response.json()
        return payload if isinstance(payload, dict) else None
    return None


async def _fetch_by_ids(
    access_token: str,
    resource: str,
    ids: list[str],
) -> dict[str, dict]:
    headers = _auth_headers(access_token)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    results: dict[str, dict] = {}

    async with httpx.AsyncClient(timeout=20) as client:

        async def fetch_one(item_id: str) -> None:
            async with semaphore:
                payload = await _get_json(
                    client,
                    f"{SPOTIFY_API_BASE}/{resource}/{item_id}",
                    headers,
                )
                if payload:
                    results[item_id] = payload

        await asyncio.gather(*(fetch_one(item_id) for item_id in ids))

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


async def enrich_tracks(access_token: str, tracks: list[dict]) -> list[dict]:
    artist_ids = unique_ids(
        [artist["id"] for track in tracks for artist in track.get("artists") or []]
    )
    missing_year_album_ids = unique_ids(
        [
            track.get("album_id")
            for track in tracks
            if release_year(track.get("release_date")) is None
        ]
    )

    artist_payloads = await _fetch_by_ids(access_token, "artists", artist_ids)
    album_payloads = await _fetch_by_ids(access_token, "albums", missing_year_album_ids)

    enriched: list[dict] = []
    for track in tracks:
        year = release_year(track.get("release_date"))
        if year is None:
            album = album_payloads.get(track.get("album_id") or "") or {}
            year = release_year(album.get("release_date"))

        enriched.append(
            {
                "track": {
                    "id": track["id"],
                    "name": track["name"],
                    "artists": track["artists"],
                    "album": track["album"],
                },
                "release_year": year,
                "genres": _merge_genres(track.get("artists") or [], artist_payloads),
            }
        )

    return enriched
