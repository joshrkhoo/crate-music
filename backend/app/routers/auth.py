from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import (
    FRONTEND_URL,
    SPOTIFY_AUTHORIZE_URL,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
)
from app.spotify import (
    access_token_expired,
    exchange_code,
    fetch_me,
    generate_pkce,
    generate_state,
    refresh_access_token,
    session_tokens_from_spotify,
)

router = APIRouter()


def _frontend_redirect(error: str | None = None) -> RedirectResponse:
    url = FRONTEND_URL if not error else f"{FRONTEND_URL}/?error={error}"
    return RedirectResponse(url, status_code=302)


async def valid_access_token(request: Request) -> str | None:
    tokens = request.session.get("spotify")
    if not tokens:
        return None

    if not access_token_expired(tokens):
        return tokens["access_token"]

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        request.session.pop("spotify", None)
        return None

    try:
        payload = await refresh_access_token(refresh_token)
    except httpx.HTTPError:
        request.session.pop("spotify", None)
        return None

    request.session["spotify"] = session_tokens_from_spotify(
        payload, previous_refresh=refresh_token
    )
    return request.session["spotify"]["access_token"]


@router.get("/auth/spotify/login")
async def spotify_login(request: Request) -> RedirectResponse:
    verifier, challenge = generate_pkce()
    state = generate_state()
    request.session["oauth_state"] = state
    request.session["code_verifier"] = verifier

    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SPOTIFY_SCOPES,
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    }
    return RedirectResponse(
        f"{SPOTIFY_AUTHORIZE_URL}?{urlencode(params)}",
        status_code=302,
    )


@router.get("/auth/spotify/callback")
async def spotify_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    if error:
        return _frontend_redirect(error)

    expected_state = request.session.get("oauth_state")
    verifier = request.session.pop("code_verifier", None)
    request.session.pop("oauth_state", None)

    if not code or not verifier or state != expected_state:
        return _frontend_redirect("invalid_state")

    try:
        payload = await exchange_code(code, verifier)
    except httpx.HTTPError:
        return _frontend_redirect("token_exchange_failed")

    request.session["spotify"] = session_tokens_from_spotify(payload)
    return _frontend_redirect()


@router.get("/auth/me")
async def me(request: Request) -> JSONResponse:
    access_token = await valid_access_token(request)
    if not access_token:
        return JSONResponse({"authenticated": False})

    try:
        profile = await fetch_me(access_token)
    except httpx.HTTPError:
        request.session.pop("spotify", None)
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
    request.session.clear()
    return JSONResponse({"ok": True})
