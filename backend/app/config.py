from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


SPOTIFY_CLIENT_ID = _require("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = _require("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = _require("SPOTIFY_REDIRECT_URI")
FRONTEND_URL = _require("FRONTEND_URL").rstrip("/")
COOKIE_SECURE = _env_bool(
    "COOKIE_SECURE",
    default=FRONTEND_URL.startswith("https://"),
)

LOCAL_FRONTEND_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def cors_allow_origins() -> list[str]:
    origins = [FRONTEND_URL]
    if FRONTEND_URL.startswith("https://"):
        return origins
    for origin in LOCAL_FRONTEND_ORIGINS:
        if origin not in origins:
            origins.append(origin)
    return origins


SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_ME_URL = "https://api.spotify.com/v1/me"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_SCOPES = " ".join(
    [
        "playlist-read-private",
        "playlist-read-collaborative",
        "user-read-private",
    ]
)
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "").strip()
LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"
