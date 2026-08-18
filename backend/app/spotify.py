import asyncio
import secrets
import time

import httpx

from app.config import (
    SPOTIFY_API_BASE,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_ME_URL,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_TOKEN_URL,
)
from app.timing import log_call, stage_elapsed, stage_start

##### Auth #####

def generate_state() -> str:
    return secrets.token_urlsafe(24)


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def fetch_me(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            SPOTIFY_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


def tokens_from_spotify(payload: dict, previous_refresh: str | None = None) -> dict:
    expires_in = int(payload.get("expires_in", 3600))
    return {
        "access_token": payload["access_token"],
        "refresh_token": payload.get("refresh_token") or previous_refresh,
        "expires_at": time.time() + expires_in - 30,
    }


def access_token_expired(tokens: dict | None) -> bool:
    if not tokens or "access_token" not in tokens:
        return True
    return time.time() >= float(tokens.get("expires_at", 0))
##### Get playlists #####

def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def _logged_get(
    http: httpx.AsyncClient,
    url: str,
    *,
    headers: dict[str, str],
    params: dict | None = None,
    label: str,
) -> httpx.Response:
    start = stage_start()
    rate_limits = 0
    response: httpx.Response | None = None
    for attempt in range(3):
        response = await http.get(url, headers=headers, params=params)
        if response.status_code != 429:
            log_call(
                label,
                status=response.status_code,
                elapsed=f"{stage_elapsed(start):.2f}s",
                rate_limits=rate_limits,
            )
            return response
        rate_limits += 1
        retry_after = float(response.headers.get("Retry-After", "1"))
        log_call(
            label,
            status=429,
            attempt=attempt + 1,
            reason=_spotify_error_reason(response) or "none",
            retry_after=retry_after,
        )
        await asyncio.sleep(min(retry_after, 5))
    assert response is not None
    log_call(
        label,
        status=response.status_code,
        elapsed=f"{stage_elapsed(start):.2f}s",
        rate_limits=rate_limits,
    )
    return response


async def fetch_playlist(
    access_token: str,
    playlist_id: str,
    client: httpx.AsyncClient | None = None,
) -> httpx.Response:
    async def _get(http: httpx.AsyncClient) -> httpx.Response:
        return await _logged_get(
            http,
            f"{SPOTIFY_API_BASE}/playlists/{playlist_id}",
            headers=_auth_headers(access_token),
            params={"fields": "id,name,images,owner(id),collaborative"},
            label=f"analyse playlist_meta id={playlist_id}",
        )

    if client is None:
        async with httpx.AsyncClient(timeout=20) as owned:
            return await _get(owned)
    return await _get(client)


async def fetch_playlist_items_page(
    access_token: str,
    playlist_id: str,
    offset: int = 0,
    limit: int = 50,
    client: httpx.AsyncClient | None = None,
) -> httpx.Response:
    async def _get(http: httpx.AsyncClient) -> httpx.Response:
        return await _logged_get(
            http,
            f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/items",
            headers=_auth_headers(access_token),
            params={
                "limit": limit,
                "offset": offset,
            },
            label=f"analyse playlist_page offset={offset} limit={limit}",
        )

    if client is None:
        async with httpx.AsyncClient(timeout=20) as owned:
            return await _get(owned)
    return await _get(client)


async def fetch_my_playlists_page(
    access_token: str,
    offset: int = 0,
    limit: int = 50,
) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{SPOTIFY_API_BASE}/me/playlists",
            headers=_auth_headers(access_token),
            params={"limit": limit, "offset": offset},
        )
        response.raise_for_status()
        return response.json()


def spotify_images_url(images: list | None) -> str | None:
    if not images:
        return None
    best: dict | None = None
    best_width = -1
    for image in images:
        if not isinstance(image, dict) or not image.get("url"):
            continue
        width = int(image.get("width") or 0)
        if width >= best_width:
            best = image
            best_width = width
    if best:
        return best["url"]
    first = images[0]
    return first.get("url") if isinstance(first, dict) else None


def album_image_url(album: dict) -> str | None:
    return spotify_images_url(album.get("images"))


def playlist_image_url(playlist: dict) -> str | None:
    return spotify_images_url(playlist.get("images"))


def map_spotify_track(track: dict) -> dict | None:
    if not isinstance(track, dict):
        return None
    if track.get("type") not in (None, "track") or not track.get("id"):
        return None

    artists = []
    for artist in track.get("artists") or []:
        if artist.get("id") and artist.get("name"):
            artists.append({"id": artist["id"], "name": artist["name"]})

    album = track.get("album") or {}
    release_date = album.get("release_date") or track.get("release_date")
    return {
        "id": track["id"],
        "name": track.get("name") or "Unknown track",
        "artists": artists,
        "album": album.get("name") or "",
        "album_id": album.get("id"),
        "image_url": album_image_url(album),
        "release_date": release_date,
    }


def map_track(item: dict) -> dict | None:
    if not isinstance(item, dict):
        return None
    payload = item.get("item") or item.get("track") or item
    if isinstance(payload, dict) and not payload.get("id"):
        nested = payload.get("item") or payload.get("track")
        if isinstance(nested, dict):
            payload = nested
    return map_spotify_track(payload if isinstance(payload, dict) else {})


##### Search #####


class SpotifySearchLimiter:
    def __init__(self) -> None:
        self._pause_until = 0.0
        self.rate_limits = 0
        self.requests = 0
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.exhausted = False
        self.quota_exceeded = False

    def remaining(self) -> float:
        return max(0.0, self._pause_until - time.monotonic())

    async def wait(self) -> None:
        delay = self._pause_until - time.monotonic()
        if delay > 0:
            await asyncio.sleep(delay)

    def backoff(self, seconds: float) -> None:
        self.rate_limits += 1
        self._pause_until = max(self._pause_until, time.monotonic() + seconds)


def _retry_after_seconds(response: httpx.Response) -> float:
    raw = response.headers.get("Retry-After", "1")
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 1.0


def _spotify_error_reason(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return ""
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return ""
    return str(error.get("reason") or error.get("message") or "")


async def search_track(
    access_token: str,
    name: str,
    artist: str,
    client: httpx.AsyncClient | None = None,
    *,
    limiter: SpotifySearchLimiter | None = None,
) -> dict | None:
    name = name.replace('"', " ").strip()
    artist = artist.replace('"', " ").strip()
    if not name or not artist:
        return None
    query = f"track:{name} artist:{artist}"

    async def _search(http: httpx.AsyncClient) -> dict | None:
        for attempt in range(4):
            if limiter and limiter.exhausted:
                return None
            if limiter:
                await limiter.wait()
            start = stage_start()
            if limiter:
                limiter.requests += 1
            response = await http.get(
                f"{SPOTIFY_API_BASE}/search",
                headers=_auth_headers(access_token),
                params={"q": query, "type": "track", "limit": 1},
            )
            if response.status_code == 429:
                retry_after = _retry_after_seconds(response)
                reason = _spotify_error_reason(response) or "none"
                if reason == "QUOTA_EXCEEDED" or retry_after > 300:
                    if limiter:
                        limiter.quota_exceeded = True
                        limiter.exhausted = True
                    log_call(
                        "recommend search",
                        track=repr(name),
                        artist=repr(artist),
                        status=429,
                        reason=reason,
                        retry_after=retry_after,
                        action="fallback",
                    )
                    return None
                wait = min(retry_after, 30)
                if limiter:
                    limiter.backoff(wait)
                log_call(
                    "recommend search",
                    track=repr(name),
                    artist=repr(artist),
                    status=429,
                    reason=reason,
                    retry_after=retry_after,
                    wait=wait,
                    attempt=attempt + 1,
                )
                await asyncio.sleep(wait)
                continue
            items = (
                ((response.json().get("tracks") or {}).get("items") or [])
                if response.status_code < 400
                else []
            )
            hit = bool(items) and response.status_code < 400
            if limiter:
                if response.status_code >= 400:
                    limiter.errors += 1
                elif hit:
                    limiter.hits += 1
                else:
                    limiter.misses += 1
            log_call(
                "recommend search",
                track=repr(name),
                artist=repr(artist),
                status=response.status_code,
                hit=int(hit),
                elapsed=f"{stage_elapsed(start):.2f}s",
            )
            if not hit:
                return None
            return map_spotify_track(items[0])
        return None

    if client is None:
        async with httpx.AsyncClient(timeout=10) as owned:
            return await _search(owned)
    return await _search(client)
