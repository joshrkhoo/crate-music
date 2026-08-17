from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


SPOTIFY_CLIENT_ID = _require("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = _require("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = _require("SPOTIFY_REDIRECT_URI")
FRONTEND_URL = _require("FRONTEND_URL").rstrip("/")
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
