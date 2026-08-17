from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException
import httpx

from app.playlist_url import extract_playlist_id
from app.routers.auth import require_access_token
from app.spotify import (
    fetch_me,
    fetch_my_playlists_page,
    fetch_playlist,
    fetch_playlist_items_page,
    map_track,
)

router = APIRouter()

OWNERSHIP_ERROR = (
    "Spotify will only return tracks for playlists you own or collaborate on."
)


class PlaylistImportRequest(BaseModel):
    url: str = Field(min_length=1)


async def load_owned_playlists(access_token: str) -> list[dict]:
    me = await fetch_me(access_token)
    user_id = me.get("id")
    playlists: list[dict] = []
    offset = 0

    while True:
        payload = await fetch_my_playlists_page(access_token, offset=offset)
        items = payload.get("items") or []
        for playlist in items:
            owner_id = (playlist.get("owner") or {}).get("id")
            if owner_id != user_id and not playlist.get("collaborative"):
                continue
            playlists.append(
                {
                    "id": playlist.get("id"),
                    "name": playlist.get("name") or "Untitled playlist",
                    "track_count": (
                        (playlist.get("items") or playlist.get("tracks") or {}).get("total")
                        or 0
                    ),
                }
            )

        offset += len(items)
        if not payload.get("next") or not items:
            break

    return playlists


async def load_playlist_tracks(access_token: str, playlist_id: str) -> tuple[str, list[dict]]:
    meta = await fetch_playlist(access_token, playlist_id)
    if meta.status_code == 404:
        raise HTTPException(status_code=404, detail="Playlist not found.")
    if meta.status_code == 403:
        raise HTTPException(status_code=403, detail=OWNERSHIP_ERROR)
    if meta.status_code >= 400:
        raise HTTPException(status_code=502, detail="Could not read that playlist from Spotify.")

    playlist = meta.json()
    name = playlist.get("name") or "Untitled playlist"
    tracks: list[dict] = []
    offset = 0

    while True:
        page = await fetch_playlist_items_page(access_token, playlist_id, offset=offset)
        if page.status_code == 403:
            raise HTTPException(status_code=403, detail=OWNERSHIP_ERROR)
        if page.status_code >= 400:
            raise HTTPException(status_code=502, detail="Could not read playlist tracks from Spotify.")

        payload = page.json()
        for item in payload.get("items") or []:
            mapped = map_track(item)
            if mapped:
                tracks.append(mapped)

        offset += len(payload.get("items") or [])
        if not payload.get("next"):
            break

    return name, tracks


@router.get("/spotify/playlists")
async def list_playlists(access_token: str = Depends(require_access_token)) -> dict:
    try:
        playlists = await load_owned_playlists(access_token)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not list playlists from Spotify.")

    return {"playlists": playlists}


@router.post("/spotify/playlist")
async def import_playlist(
    body: PlaylistImportRequest,
    access_token: str = Depends(require_access_token),
) -> dict:
    playlist_id = extract_playlist_id(body.url)
    if not playlist_id:
        raise HTTPException(status_code=400, detail="That is not a Spotify playlist URL.")

    try:
        name, tracks = await load_playlist_tracks(access_token, playlist_id)
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not read that playlist from Spotify.")

    return {
        "id": playlist_id,
        "name": name,
        "tracks": tracks,
    }
