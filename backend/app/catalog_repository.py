from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.catalog_seed import CATALOG_PATH, load_catalog
from backend.app.models import Track, TrackArtwork, TrackStream
from backend.app.schemas import AdminTrackCreateRequest, AdminTrackUpdateRequest


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _upsert_track(db: Session, raw: dict[str, Any]) -> None:
    now = datetime.now(UTC)
    track = db.get(Track, raw["id"])
    if track is None:
        track = Track(
            id=raw["id"],
            title=raw["title"],
            artist=raw["artist"],
            duration_sec=int(raw["duration_sec"]),
            status="published",
            created_at=now,
            updated_at=now,
        )
        db.add(track)
    else:
        track.title = raw["title"]
        track.artist = raw["artist"]
        track.duration_sec = int(raw["duration_sec"])
        track.updated_at = now

    artwork_path = raw.get("artwork", {}).get("square_512")
    if artwork_path:
        artwork = db.get(TrackArtwork, raw["id"])
        if artwork is None:
            artwork = TrackArtwork(
                track_id=raw["id"],
                square_512_path=artwork_path,
                created_at=now,
                updated_at=now,
            )
            db.add(artwork)
        else:
            artwork.square_512_path = artwork_path
            artwork.updated_at = now

    stream = raw.get("stream", {})
    playlist_path = stream.get("url")
    if playlist_path:
        stream_row = db.get(TrackStream, raw["id"])
        if stream_row is None:
            stream_row = TrackStream(
                track_id=raw["id"],
                protocol=stream.get("protocol", "hls"),
                playlist_path=playlist_path,
                fallback_path=stream.get("fallback_url"),
                created_at=now,
                updated_at=now,
            )
            db.add(stream_row)
        else:
            stream_row.protocol = stream.get("protocol", "hls")
            stream_row.playlist_path = playlist_path
            stream_row.fallback_path = stream.get("fallback_url")
            stream_row.updated_at = now


def seed_catalog_from_file(db: Session, path: Path = CATALOG_PATH) -> int:
    catalog = load_catalog(path)
    tracks = list(catalog.get("tracks", []))
    for raw in tracks:
        _upsert_track(db, raw)
    db.commit()
    return len(tracks)


def ensure_catalog_seeded(db: Session, path: Path = CATALOG_PATH) -> int:
    count_stmt = select(func.count()).select_from(Track)
    total = db.scalar(count_stmt) or 0
    if total > 0:
        return total
    return seed_catalog_from_file(db, path)


def get_catalog_page(db: Session, limit: int, offset: int, q: str | None) -> dict[str, Any]:
    ensure_catalog_seeded(db)

    stmt = (
        select(Track, TrackArtwork.square_512_path)
        .outerjoin(TrackArtwork, TrackArtwork.track_id == Track.id)
        .where(Track.status == "published")
    )
    if q:
        needle = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Track.title).like(needle), func.lower(Track.artist).like(needle)))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(db.scalar(count_stmt) or 0)

    rows = db.execute(stmt.order_by(Track.id).offset(offset).limit(limit)).all()
    tracks = [
        {
            "id": row[0].id,
            "title": row[0].title,
            "artist": row[0].artist,
            "duration_sec": row[0].duration_sec,
            "artwork": {"square_512": row[1]} if row[1] else {},
        }
        for row in rows
    ]

    return {
        "schema_version": "1.0",
        "app": {"title": "Ferric POC"},
        "tracks": tracks,
        "page": {"limit": limit, "offset": offset, "total": total},
    }


def get_track_by_id(db: Session, track_id: str) -> dict[str, Any] | None:
    ensure_catalog_seeded(db)
    row = db.execute(
        select(Track, TrackArtwork.square_512_path)
        .outerjoin(TrackArtwork, TrackArtwork.track_id == Track.id)
        .where(Track.id == track_id, Track.status == "published")
    ).first()
    if row is None:
        return None

    track, artwork_path = row
    return {
        "id": track.id,
        "title": track.title,
        "artist": track.artist,
        "duration_sec": track.duration_sec,
        "artwork": {"square_512": artwork_path} if artwork_path else {},
    }


def get_track_stream_by_id(db: Session, track_id: str) -> dict[str, Any] | None:
    ensure_catalog_seeded(db)
    row = db.execute(
        select(TrackStream.protocol, TrackStream.playlist_path, TrackStream.fallback_path)
        .join(Track, Track.id == TrackStream.track_id)
        .where(TrackStream.track_id == track_id, Track.status == "published")
    ).first()
    if row is None:
        return None

    return {"protocol": row[0], "url": row[1], "fallback_url": row[2]}


def list_admin_tracks(db: Session, q: str | None, status: str | None) -> list[dict[str, Any]]:
    ensure_catalog_seeded(db)
    stmt = (
        select(
            Track,
            TrackArtwork.square_512_path,
            TrackStream.protocol,
            TrackStream.playlist_path,
            TrackStream.fallback_path,
        )
        .outerjoin(TrackArtwork, TrackArtwork.track_id == Track.id)
        .outerjoin(TrackStream, TrackStream.track_id == Track.id)
    )
    if status:
        stmt = stmt.where(Track.status == status)
    if q:
        needle = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Track.title).like(needle), func.lower(Track.artist).like(needle)))

    rows = db.execute(stmt.order_by(Track.id)).all()
    result: list[dict[str, Any]] = []
    for track, artwork_path, protocol, playlist_path, fallback_path in rows:
        item: dict[str, Any] = {
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "duration_sec": track.duration_sec,
            "status": track.status,
            "uploaded_at": _to_iso(track.uploaded_at) if track.uploaded_at else None,
            "updated_at": _to_iso(track.updated_at),
            "artwork": {"square_512": artwork_path} if artwork_path else {},
            "stream": None,
        }
        if playlist_path:
            item["stream"] = {
                "protocol": protocol or "hls",
                "url": playlist_path,
                "fallback_url": fallback_path,
            }
        result.append(item)
    return result


def create_admin_track(db: Session, payload: AdminTrackCreateRequest) -> dict[str, Any]:
    now = datetime.now(UTC)
    track_id = payload.id
    if track_id is None:
        track_id = str(uuid4())
    while db.get(Track, track_id) is not None:
        if payload.id is not None:
            raise ValueError("track already exists")
        track_id = str(uuid4())
    track = Track(
        id=track_id,
        title=payload.title,
        artist=payload.artist,
        duration_sec=payload.duration_sec,
        status=payload.status,
        uploaded_at=now if payload.status == "published" else None,
        created_at=now,
        updated_at=now,
    )
    db.add(track)
    db.commit()
    return {
        "id": track.id,
        "title": track.title,
        "artist": track.artist,
        "duration_sec": track.duration_sec,
        "status": track.status,
        "uploaded_at": _to_iso(track.uploaded_at) if track.uploaded_at else None,
        "updated_at": _to_iso(track.updated_at),
        "artwork": {},
        "stream": None,
    }


def update_admin_track(db: Session, track_id: str, payload: AdminTrackUpdateRequest) -> dict[str, Any] | None:
    track = db.get(Track, track_id)
    if track is None:
        return None

    if payload.title is not None:
        track.title = payload.title
    if payload.artist is not None:
        track.artist = payload.artist
    if payload.duration_sec is not None:
        track.duration_sec = payload.duration_sec
    previous_status = track.status
    if payload.status is not None:
        track.status = payload.status
        if payload.status == "published" and previous_status != "published" and track.uploaded_at is None:
            track.uploaded_at = datetime.now(UTC)
    track.updated_at = datetime.now(UTC)
    db.add(track)
    db.commit()
    return get_admin_track(db, track_id)


def get_admin_track(db: Session, track_id: str) -> dict[str, Any] | None:
    row = db.execute(
        select(
            Track,
            TrackArtwork.square_512_path,
            TrackStream.protocol,
            TrackStream.playlist_path,
            TrackStream.fallback_path,
        )
        .outerjoin(TrackArtwork, TrackArtwork.track_id == Track.id)
        .outerjoin(TrackStream, TrackStream.track_id == Track.id)
        .where(Track.id == track_id)
    ).first()
    if row is None:
        return None
    track, artwork_path, protocol, playlist_path, fallback_path = row
    result = {
        "id": track.id,
        "title": track.title,
        "artist": track.artist,
        "duration_sec": track.duration_sec,
        "status": track.status,
        "uploaded_at": _to_iso(track.uploaded_at) if track.uploaded_at else None,
        "updated_at": _to_iso(track.updated_at),
        "artwork": {"square_512": artwork_path} if artwork_path else {},
        "stream": None,
    }
    if playlist_path:
        result["stream"] = {"protocol": protocol or "hls", "url": playlist_path, "fallback_url": fallback_path}
    return result


def set_track_artwork_path(db: Session, track_id: str, artwork_path: str) -> dict[str, Any] | None:
    track = db.get(Track, track_id)
    if track is None:
        return None

    now = datetime.now(UTC)
    artwork = db.get(TrackArtwork, track_id)
    if artwork is None:
        artwork = TrackArtwork(
            track_id=track_id,
            square_512_path=artwork_path,
            created_at=now,
            updated_at=now,
        )
    else:
        artwork.square_512_path = artwork_path
        artwork.updated_at = now
    db.add(artwork)
    track.updated_at = now
    db.add(track)
    db.commit()
    return get_admin_track(db, track_id)


def set_track_audio_fallback(db: Session, track_id: str, fallback_path: str) -> dict[str, Any] | None:
    track = db.get(Track, track_id)
    if track is None:
        return None

    now = datetime.now(UTC)
    stream = db.get(TrackStream, track_id)
    default_playlist = f"/generated/hls/{track_id}/playlist.m3u8"
    if stream is None:
        stream = TrackStream(
            track_id=track_id,
            protocol="hls",
            playlist_path=default_playlist,
            fallback_path=fallback_path,
            created_at=now,
            updated_at=now,
        )
    else:
        stream.fallback_path = fallback_path
        if not stream.playlist_path:
            stream.playlist_path = default_playlist
        stream.updated_at = now

    db.add(stream)
    track.updated_at = now
    db.add(track)
    db.commit()
    return get_admin_track(db, track_id)


def publish_track(db: Session, track_id: str) -> dict[str, Any] | None:
    track = db.get(Track, track_id)
    if track is None:
        return None
    now = datetime.now(UTC)
    track.status = "published"
    if track.uploaded_at is None:
        track.uploaded_at = now
    track.updated_at = now
    db.add(track)
    db.commit()
    return {"id": track.id, "status": "published"}
