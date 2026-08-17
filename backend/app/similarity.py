import numpy as np


def nearest_in_playlist(
    tracks: list[dict],
    track_id: str,
    limit: int = 5,
) -> tuple[dict, list[tuple[float, dict]]]:
    query = next((track for track in tracks if track["track"]["id"] == track_id), None)
    if query is None or not query.get("metadata_embedding"):
        raise KeyError(track_id)

    query_vector = np.array(query["metadata_embedding"], dtype=np.float64)
    scored: list[tuple[float, dict]] = []

    for track in tracks:
        if track["track"]["id"] == track_id:
            continue
        embedding = track.get("metadata_embedding")
        if not embedding:
            continue
        similarity = float(np.dot(query_vector, np.array(embedding, dtype=np.float64)))
        scored.append((max(-1.0, min(1.0, similarity)), track))

    scored.sort(key=lambda item: item[0], reverse=True)
    return query, scored[:limit]
