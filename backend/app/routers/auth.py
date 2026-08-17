from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import (
    COOKIE_SECURE,
    FRONTEND_URL,
    SPOTIFY_AUTHORIZE_URL,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
)
from app.sessions import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    consume_oauth_state,
    create_session,
    delete_session,
    get_session,
    remember_oauth_state,
    update_session,
)
from app.spotify import (
    access_token_expired,
    exchange_code,
    fetch_me,
    generate_state,
    refresh_access_token,
    tokens_from_spotify,
)

router = APIRouter()


def _frontend_redirect(
    *,
    error: str | None = None,
    session_id: str | None = None,
) -> RedirectResponse:
    params: dict[str, str] = {}
    if error:
        params["error"] = error
    if session_id:
        params["sid"] = session_id
    url = FRONTEND_URL if not params else f"{FRONTEND_URL}/?{urlencode(params)}"
    return RedirectResponse(url, status_code=302)


def session_id_from_request(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token:
            return token
    return request.cookies.get(SESSION_COOKIE)


def _set_session_cookie(response: RedirectResponse | JSONResponse, session_id: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )


def _clear_session_cookie(response: JSONResponse) -> None:
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )


async def valid_access_token(request: Request) -> str | None:
    session_id = session_id_from_request(request)
    tokens = get_session(session_id)
    if not tokens:
        return None

    if not access_token_expired(tokens):
        return tokens["access_token"]

    refresh_token = tokens.get("refresh_token")
    if not session_id or not refresh_token:
        delete_session(session_id)
        return None

    try:
        payload = await refresh_access_token(refresh_token)
    except httpx.HTTPError:
        delete_session(session_id)
        return None

    updated = tokens_from_spotify(payload, previous_refresh=refresh_token)
    update_session(session_id, updated)
    return updated["access_token"]


async def require_access_token(request: Request) -> str:
    token = await valid_access_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token


@router.get("/auth/spotify/login")
async def spotify_login() -> RedirectResponse:
    state = generate_state()
    remember_oauth_state(state)

    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SPOTIFY_SCOPES,
        "state": state,
        "show_dialog": "true",
    }
    return RedirectResponse(
        f"{SPOTIFY_AUTHORIZE_URL}?{urlencode(params)}",
        status_code=302,
    )


@router.get("/auth/spotify/callback")
async def spotify_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    if error:
        return _frontend_redirect(error=error)

    if not code or not consume_oauth_state(state):
        return _frontend_redirect(error="invalid_state")

    try:
        payload = await exchange_code(code)
    except httpx.HTTPError:
        return _frontend_redirect(error="token_exchange_failed")

    session_id = create_session(tokens_from_spotify(payload))
    response = _frontend_redirect(session_id=session_id)
    _set_session_cookie(response, session_id)
    return response


@router.get("/auth/me")
async def me(request: Request) -> JSONResponse:
    access_token = await valid_access_token(request)
    if not access_token:
        return JSONResponse({"authenticated": False})

    try:
        profile = await fetch_me(access_token)
    except httpx.HTTPError:
        delete_session(session_id_from_request(request))
        return JSONResponse({"authenticated": False})

    return JSONResponse(
        {
            "authenticated": True,
            "id": profile.get("id"),
            "display_name": profile.get("display_name"),
            "country": profile.get("country"),
        }
    )


@router.post("/auth/logout")
async def logout(request: Request) -> JSONResponse:
    delete_session(session_id_from_request(request))
    response = JSONResponse({"ok": True})
    _clear_session_cookie(response)
    return response
