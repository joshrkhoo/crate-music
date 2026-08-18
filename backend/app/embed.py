from functools import lru_cache
from pathlib import Path
import os

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
os.environ.setdefault("HF_HOME", str(CACHE_DIR / "huggingface"))
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(CACHE_DIR / "sentence-transformers"))

MODEL_NAME = "all-MiniLM-L6-v2"


def metadata_text(enriched: dict) -> str:
    track = enriched["track"]
    artists = ", ".join(artist["name"] for artist in track.get("artists") or [])
    year = enriched.get("release_year")
    genres = ", ".join(enriched.get("genres") or [])
    return "\n".join(
        [
            f"artist: {artists}",
            f"track: {track.get('name') or ''}",
            f"album: {track.get('album') or ''}",
            f"year: {'' if year is None else year}",
            f"genres: {genres}",
        ]
    )


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def warmup_model() -> None:
    _model()


def embed_tracks(tracks: list[dict]) -> list[dict]:
    if not tracks:
        return []

    vectors = _model().encode(
        [metadata_text(track) for track in tracks],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    embedded: list[dict] = []
    for track, vector in zip(tracks, vectors, strict=True):
        embedded.append({**track, "metadata_embedding": vector.tolist()})
    return embedded


def public_tracks(tracks: list[dict]) -> list[dict]:
    return [
        {
            "track": track["track"],
            "release_year": track["release_year"],
            "genres": track["genres"],
        }
        for track in tracks
    ]
