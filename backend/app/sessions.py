import json
import secrets
import time
from pathlib import Path
from typing import Any

SESSION_COOKIE = "crate_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 14
PENDING_OAUTH_TTL = 60 * 10
PLAYLIST_CACHE_PATH = Path(__file__).resolve().parent.parent / ".cache" / "last_playlist.json"

_sessions: dict[str, dict[str, Any]] = {}
_pending_oauth: dict[str, float] = {}
_last_playlists: dict[str, dict[str, Any]] = {}
_latest_playlist: dict[str, Any] | None = None


def _write_playlist_cache(playlist: dict[str, Any]) -> None:
    PLAYLIST_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLAYLIST_CACHE_PATH.write_text(json.dumps(playlist))


def _read_playlist_cache() -> dict[str, Any] | None:
    if not PLAYLIST_CACHE_PATH.exists():
        return None
    try:
        payload = json.loads(PLAYLIST_CACHE_PATH.read_text())
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
    if session_id:
        _sessions.pop(session_id, None)
        _last_playlists.pop(session_id, None)


def store_last_playlist(session_id: str | None, playlist: dict[str, Any]) -> None:
    global _latest_playlist
    _latest_playlist = playlist
    if session_id:
        _last_playlists[session_id] = playlist
    _write_playlist_cache(playlist)


def get_last_playlist(session_id: str | None) -> dict[str, Any] | None:
    global _latest_playlist
    if session_id and session_id in _last_playlists:
        return _last_playlists[session_id]
    if _latest_playlist is not None:
        return _latest_playlist
    cached = _read_playlist_cache()
    if cached is not None:
        _latest_playlist = cached
    return _latest_playlist


def remember_oauth_state(state: str) -> None:
    _pending_oauth[state] = time.time()


def consume_oauth_state(state: str | None) -> bool:
    if not state:
        return False
    created_at = _pending_oauth.pop(state, None)
    if created_at is None:
        return False
    return time.time() - created_at <= PENDING_OAUTH_TTL
