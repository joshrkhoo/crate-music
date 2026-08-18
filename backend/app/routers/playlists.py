from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
import httpx
import asyncio
import json
import logging

from app.recommend import recommend_new_tracks
from app.embed import embed_tracks, public_tracks
from app.enrich import enrich_tracks
from app.playlist_url import extract_playlist_id
from app.routers.auth import require_access_token, session_id_from_request
from app.sessions import (
    embeddings_ready,
    get_debug_playlist,
    get_last_playlist,
    store_last_playlist,
)
from app.similarity import nearest_in_playlist
from app.spotify import (
    fetch_me,
    fetch_my_playlists_page,
    fetch_playlist,
    fetch_playlist_items_page,
    map_track,
)
from app.timing import log_stage, stage_elapsed, stage_start

log = logging.getLogger("crate.timing")

router = APIRouter()

OWNERSHIP_ERROR = (
    "Spotify will only return tracks for playlists you own or collaborate on."
)

INDEXING_ERROR = "Still building similarity index. Try again in a moment."

_embedding_tasks: dict[str, asyncio.Task] = {}


async def _finish_embedding(
    session_id: str | None,
    playlist_id: str,
    tracks: list[dict],
) -> None:
    start = stage_start()
    try:
        embedded = await asyncio.to_thread(embed_tracks, tracks)
    except Exception:
        log.exception("crate analyse embedding failed tracks=%d", len(tracks))
        current = get_last_playlist(session_id)
        if current and current.get("id") == playlist_id:
            current["embeddings_ready"] = False
            current["embedding_error"] = True
            store_last_playlist(session_id, current)
        return

    log_stage("analyse embedding", stage_elapsed(start), tracks=len(tracks))

    current = get_last_playlist(session_id)
    if not current or current.get("id") != playlist_id:
        return
    current["tracks"] = embedded
    current["embeddings_ready"] = True
    current.pop("embedding_error", None)
    store_last_playlist(session_id, current)


def _start_embedding(session_id: str | None, playlist_id: str, tracks: list[dict]) -> None:
    if not session_id:
        return
    existing = _embedding_tasks.pop(session_id, None)
    if existing and not existing.done():
        existing.cancel()
    task = asyncio.create_task(_finish_embedding(session_id, playlist_id, tracks))
    _embedding_tasks[session_id] = task


def _require_indexed_playlist(session_id: str | None) -> dict:
    playlist = get_last_playlist(session_id)
    if not playlist:
        raise HTTPException(
            status_code=404,
            detail="No playlist in memory. Analyse a playlist first.",
        )
    if not embeddings_ready(playlist):
        raise HTTPException(status_code=409, detail=INDEXING_ERROR)
    return playlist


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
    start = stage_start()
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

    async with httpx.AsyncClient(timeout=20) as client:
        first = await fetch_playlist_items_page(
            access_token,
            playlist_id,
            offset=0,
            limit=100,
            client=client,
        )
        if first.status_code == 403:
            raise HTTPException(status_code=403, detail=OWNERSHIP_ERROR)
        if first.status_code >= 400:
            raise HTTPException(status_code=502, detail="Could not read playlist tracks from Spotify.")

        payload = first.json()
        for item in payload.get("items") or []:
            mapped = map_track(item)
            if mapped:
                tracks.append(mapped)

        total = int(payload.get("total") or 0)
        page_size = 100
        extra_offsets = list(range(page_size, total, page_size)) if total > page_size else []
        if extra_offsets:
            pages = await asyncio.gather(
                *(
                    fetch_playlist_items_page(
                        access_token,
                        playlist_id,
                        offset=offset,
                        limit=page_size,
                        client=client,
                    )
                    for offset in extra_offsets
                )
            )
            for page in pages:
                if page.status_code == 403:
                    raise HTTPException(status_code=403, detail=OWNERSHIP_ERROR)
                if page.status_code >= 400:
                    raise HTTPException(
                        status_code=502,
                        detail="Could not read playlist tracks from Spotify.",
                    )
                for item in (page.json().get("items") or []):
                    mapped = map_track(item)
                    if mapped:
                        tracks.append(mapped)

    log_stage("analyse playlist_fetch", stage_elapsed(start), tracks=len(tracks))
    return name, await enrich_tracks(access_token, tracks)


@router.get("/spotify/playlists")
async def list_playlists(access_token: str = Depends(require_access_token)) -> dict:
    try:
        playlists = await load_owned_playlists(access_token)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not list playlists from Spotify.")

    return {"playlists": playlists}


@router.get("/spotify/playlist/status")
async def playlist_status(request: Request) -> dict:
    session_id = session_id_from_request(request)
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    playlist = get_last_playlist(session_id)
    if not playlist:
        raise HTTPException(
            status_code=404,
            detail="No playlist in memory. Analyse a playlist first.",
        )

    return {
        "id": playlist.get("id"),
        "name": playlist.get("name"),
        "track_count": len(playlist.get("tracks") or []),
        "embeddings_ready": embeddings_ready(playlist),
        "embedding_error": bool(playlist.get("embedding_error")),
    }


@router.get("/embeddings")
async def view_embeddings() -> Response:
    playlist = get_debug_playlist()
    if not playlist:
        raise HTTPException(
            status_code=404,
            detail="No playlist in memory. Analyse a playlist first.",
        )

    payload = {
        "id": playlist["id"],
        "name": playlist["name"],
        "tracks": [
            {
                "id": item["track"]["id"],
                "name": item["track"]["name"],
                "artists": [artist["name"] for artist in item["track"]["artists"]],
                "dim": len(item.get("metadata_embedding") or []),
                "embedding": item.get("metadata_embedding"),
            }
            for item in playlist["tracks"]
        ],
    }
    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
    )


def _public_neighbor(score: float, item: dict) -> dict:
    public = public_tracks([item])[0]
    public["similarity"] = round(score, 4)
    return public


@router.get("/spotify/similar/{track_id}")
async def similar_tracks(
    request: Request,
    track_id: str,
    limit: int = 5,
) -> dict:
    session_id = session_id_from_request(request)
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    playlist = _require_indexed_playlist(session_id_from_request(request))

    try:
        query, neighbors = nearest_in_playlist(playlist["tracks"], track_id, limit=limit)
    except KeyError:
        raise HTTPException(status_code=404, detail="That track is not in the analysed playlist.")

    return {
        "track": public_tracks([query])[0],
        "neighbors": [_public_neighbor(score, item) for score, item in neighbors],
    }


@router.post("/spotify/recommend")
async def recommend_tracks(
    request: Request,
    access_token: str = Depends(require_access_token),
) -> dict:
    session_id = session_id_from_request(request)
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    playlist = _require_indexed_playlist(session_id)

    try:
        ranked = await recommend_new_tracks(access_token, playlist["tracks"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not fetch recommendations.")

    return {
        "recommendations": [
            _public_neighbor(item["similarity"], item) for item in ranked
        ]
    }


@router.post("/spotify/playlist")
async def import_playlist(
    request: Request,
    body: PlaylistImportRequest,
    access_token: str = Depends(require_access_token),
) -> dict:
    playlist_id = extract_playlist_id(body.url)
    if not playlist_id:
        raise HTTPException(status_code=400, detail="That is not a Spotify playlist URL.")

    try:
        total_start = stage_start()
        name, tracks = await load_playlist_tracks(access_token, playlist_id)
        log_stage("analyse total_sync", stage_elapsed(total_start), tracks=len(tracks))
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not read that playlist from Spotify.")

    session_id = session_id_from_request(request)
    payload = {
        "id": playlist_id,
        "name": name,
        "tracks": tracks,
        "embeddings_ready": False,
    }
    store_last_playlist(session_id, payload)
    _start_embedding(session_id, playlist_id, tracks)

    return {
        "id": playlist_id,
        "name": name,
        "tracks": public_tracks(tracks),
        "embeddings_ready": False,
    }
