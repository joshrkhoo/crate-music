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


async def fetch_playlist(access_token: str, playlist_id: str) -> httpx.Response:
    async with httpx.AsyncClient(timeout=20) as client:
        return await client.get(
            f"{SPOTIFY_API_BASE}/playlists/{playlist_id}",
            headers=_auth_headers(access_token),
            params={"fields": "id,name,owner(id),collaborative"},
        )


async def fetch_playlist_items_page(
    access_token: str,
    playlist_id: str,
    offset: int = 0,
    limit: int = 50,
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=20) as client:
        return await client.get(
            f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/items",
            headers=_auth_headers(access_token),
            params={
                "limit": limit,
                "offset": offset,
            },
        )


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


def map_track(item: dict) -> dict | None:
    track = item.get("item") or item.get("track")
    if not isinstance(track, dict):
        return None
    if track.get("type") not in (None, "track") or not track.get("id"):
        return None

    artists = []
    for artist in track.get("artists") or []:
        if artist.get("id") and artist.get("name"):
            artists.append({"id": artist["id"], "name": artist["name"]})

    album = track.get("album") or {}
    return {
        "id": track["id"],
        "name": track.get("name") or "Unknown track",
        "artists": artists,
        "album": album.get("name") or "",
    }
