import json
import secrets
import time
from pathlib import Path
from typing import Any

SESSION_COOKIE = "crate_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 14
PENDING_OAUTH_TTL = 60 * 10
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
DEBUG_PLAYLIST_PATH = CACHE_DIR / "last_playlist.json"
SESSION_PLAYLIST_DIR = CACHE_DIR / "playlists"

_sessions: dict[str, dict[str, Any]] = {}
_pending_oauth: dict[str, float] = {}
_last_playlists: dict[str, dict[str, Any]] = {}
_debug_playlist: dict[str, Any] | None = None


def _is_session_id(session_id: str) -> bool:
    return bool(session_id) and all(ch.isalnum() or ch in "-_" for ch in session_id)


def _session_playlist_path(session_id: str) -> Path:
    return SESSION_PLAYLIST_DIR / f"{session_id}.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def create_session(data: dict[str, Any]) -> str:
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = data
    return session_id


def get_session(session_id: str | None) -> dict[str, Any] | None:
    if not session_id:
        return None
    return _sessions.get(session_id)


def update_session(session_id: str, data: dict[str, Any]) -> None:
    _sessions[session_id] = data


def delete_session(session_id: str | None) -> None:
    if not session_id:
        return
    _sessions.pop(session_id, None)
    _last_playlists.pop(session_id, None)
    if _is_session_id(session_id):
        _session_playlist_path(session_id).unlink(missing_ok=True)


def store_last_playlist(session_id: str | None, playlist: dict[str, Any]) -> None:
    global _debug_playlist
    _debug_playlist = playlist
    _write_json(DEBUG_PLAYLIST_PATH, playlist)
    if session_id:
        _last_playlists[session_id] = playlist
        if _is_session_id(session_id):
            _write_json(_session_playlist_path(session_id), playlist)


def get_last_playlist(session_id: str | None) -> dict[str, Any] | None:
    if not session_id:
        return None
    cached = _last_playlists.get(session_id)
    if cached is not None:
        return cached
    if not _is_session_id(session_id):
        return None
    playlist = _read_json(_session_playlist_path(session_id))
    if playlist is not None:
        _last_playlists[session_id] = playlist
    return playlist


def get_debug_playlist() -> dict[str, Any] | None:
    global _debug_playlist
    if _debug_playlist is not None:
        return _debug_playlist
    _debug_playlist = _read_json(DEBUG_PLAYLIST_PATH)
    return _debug_playlist


def embeddings_ready(playlist: dict[str, Any] | None) -> bool:
    if not playlist:
        return False
    flag = playlist.get("embeddings_ready")
    if flag is True:
        return True
    if flag is False:
        return False
    tracks = playlist.get("tracks") or []
    if not tracks:
        return False
    return bool(tracks[0].get("metadata_embedding"))


def remember_oauth_state(state: str) -> None:
    _pending_oauth[state] = time.time()


def consume_oauth_state(state: str | None) -> bool:
    if not state:
        return False
    created_at = _pending_oauth.pop(state, None)
    if created_at is None:
        return False
    return time.time() - created_at <= PENDING_OAUTH_TTL
