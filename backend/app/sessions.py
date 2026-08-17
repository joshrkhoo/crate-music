import secrets
import time
from typing import Any

SESSION_COOKIE = "crate_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 14
PENDING_OAUTH_TTL = 60 * 10

_sessions: dict[str, dict[str, Any]] = {}
_pending_oauth: dict[str, float] = {}
_last_playlists: dict[str, dict[str, Any]] = {}
_latest_playlist: dict[str, Any] | None = None


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


def get_last_playlist(session_id: str | None) -> dict[str, Any] | None:
    if session_id and session_id in _last_playlists:
        return _last_playlists[session_id]
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
