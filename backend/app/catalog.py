from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "public" / "catalog.json"


def _load_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_catalog_page(limit: int, offset: int, q: str | None) -> dict[str, Any]:
    catalog = _load_catalog()
    tracks: list[dict[str, Any]] = list(catalog.get("tracks", []))

    if q:
        needle = q.strip().lower()
        tracks = [
            track
            for track in tracks
            if needle in str(track.get("title", "")).lower()
            or needle in str(track.get("artist", "")).lower()
        ]

    total = len(tracks)
    paged = tracks[offset : offset + limit]

    response_tracks = [
        {
            "id": track["id"],
            "title": track["title"],
            "artist": track["artist"],
            "artwork": track.get("artwork", {}),
            "duration_sec": track["duration_sec"],
        }
        for track in paged
    ]

    return {
        "schema_version": catalog.get("schema_version", "1.0"),
        "app": catalog.get("app", {"title": "Ferric POC"}),
        "tracks": response_tracks,
        "page": {
            "limit": limit,
            "offset": offset,
            "total": total,
        },
    }


def get_track_by_id(track_id: str) -> dict[str, Any] | None:
    catalog = _load_catalog()
    tracks: list[dict[str, Any]] = list(catalog.get("tracks", []))
    for track in tracks:
        if str(track.get("id")) == track_id:
            return {
                "id": track["id"],
                "title": track["title"],
                "artist": track["artist"],
                "duration_sec": track["duration_sec"],
                "artwork": track.get("artwork", {}),
            }
    return None


def get_track_stream_by_id(track_id: str) -> dict[str, Any] | None:
    catalog = _load_catalog()
    tracks: list[dict[str, Any]] = list(catalog.get("tracks", []))
    for track in tracks:
        if str(track.get("id")) == track_id:
            stream = track.get("stream", {})
            return {
                "protocol": stream.get("protocol", "hls"),
                "url": stream.get("url", ""),
                "fallback_url": stream.get("fallback_url"),
            }
    return None
