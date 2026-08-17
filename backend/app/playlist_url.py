import re

PLAYLIST_URL_RE = re.compile(
    r"(?:open\.spotify\.com/(?:intl-[a-z]+/)?playlist/|spotify:playlist:)([A-Za-z0-9]+)"
)
PLAYLIST_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")


def extract_playlist_id(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None

    match = PLAYLIST_URL_RE.search(text)
    if match:
        return match.group(1)

    if PLAYLIST_ID_RE.fullmatch(text):
        return text

    return None
