from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
import logging
import os
from pathlib import Path
import subprocess
import json
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.app.admin_auth import require_admin
from backend.app.catalog_repository import (
    create_admin_track,
    get_admin_track,
    list_admin_tracks,
    publish_track,
    set_track_artwork_path,
    set_track_audio_fallback,
    update_admin_track,
)
from backend.app.db import get_db
from backend.app.listening_repository import get_track_stats, get_user_stats
from backend.app.metadata_extractor import extract_track_metadata
from backend.app.schemas import (
    AdminPublishResponse,
    AdminTrackCreateRequest,
    AdminTrackListResponse,
    AdminLogsResponse,
    AdminTrackMetadataResponse,
    AdminTrackResponse,
    AdminTrackUpdateRequest,
    TrackStatsResponse,
    UserStatsResponse,
)
from backend.app.track_metadata_repository import get_track_metadata, upsert_track_metadata


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_AUDIO_ROOT = REPO_ROOT / "assets" / "raw-audio" / "managed"
IMAGES_ROOT = REPO_ROOT / "public" / "images" / "managed"
HLS_ROOT = REPO_ROOT / "public" / "generated" / "hls"
logger = logging.getLogger("ferric.admin")

admin_v1 = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _bad_request(message: str) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": message}})


def _track_not_found() -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": {"code": "TRACK_NOT_FOUND", "message": "Track does not exist"}})


def _log_sources() -> dict[str, Path]:
    log_dir = Path(os.getenv("FERRIC_LOG_DIR", str(REPO_ROOT / "backend" / "logs"))).resolve()
    return {
        "backend": log_dir / "backend.log",
        "frontend": log_dir / "frontend.log",
    }


def _tail_lines(path: Path, max_lines: int) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    lines: deque[str] = deque(maxlen=max_lines)
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            lines.append(line.rstrip("\n"))
    return list(lines)


def _repo_path_from_public_path(path: str | None) -> Path | None:
    if not path:
        return None
    if path.startswith("/generated/"):
        return REPO_ROOT / "public" / path.lstrip("/")
    if path.startswith("/assets/raw-audio/"):
        return REPO_ROOT / path.lstrip("/")
    if path.startswith("/images/"):
        return REPO_ROOT / "public" / path.lstrip("/")
    return None


def _is_stream_ready(row: dict) -> bool:
    stream = row.get("stream")
    if not stream:
        return False
    playlist_path = _repo_path_from_public_path(stream.get("url"))
    fallback_path = _repo_path_from_public_path(stream.get("fallback_url"))
    has_playlist = bool(playlist_path and playlist_path.exists())
    has_fallback = bool(fallback_path and fallback_path.exists())
    return has_playlist and has_fallback


def _generate_hls(track_id: str, audio_path: Path) -> bool:
    out_dir = HLS_ROOT / track_id
    out_dir.mkdir(parents=True, exist_ok=True)
    playlist = out_dir / "playlist.m3u8"
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(audio_path),
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-f",
                "hls",
                "-hls_time",
                "10",
                "-hls_playlist_type",
                "vod",
                "-hls_segment_type",
                "mpegts",
                "-hls_segment_filename",
                str(out_dir / "seg_%03d.ts"),
                str(playlist),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return playlist.exists()
    except FileNotFoundError:
        logger.warning("ffmpeg not installed; skipping HLS generation for %s", track_id)
        return False
    except subprocess.CalledProcessError as exc:
        logger.warning("ffmpeg failed for %s: %s", track_id, exc.stderr.strip())
        return False


def _probe_duration_sec(audio_path: Path) -> float | None:
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(proc.stdout or "{}")
        duration = payload.get("format", {}).get("duration")
        if duration is None:
            return None
        return float(duration)
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError, TypeError, json.JSONDecodeError):
        return None


@admin_v1.get("/tracks", response_model=AdminTrackListResponse)
def admin_list_tracks(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AdminTrackListResponse:
    rows = list_admin_tracks(db, q=q, status=status)
    return AdminTrackListResponse(tracks=[AdminTrackResponse.model_validate(row) for row in rows])


@admin_v1.get("/tracks/{track_id}", response_model=AdminTrackResponse)
def admin_get_track(track_id: str, db: Session = Depends(get_db)) -> AdminTrackResponse:
    row = get_admin_track(db, track_id)
    if row is None:
        return _track_not_found()
    return AdminTrackResponse.model_validate(row)


@admin_v1.post("/tracks", response_model=AdminTrackResponse)
def admin_create_track(payload: AdminTrackCreateRequest, db: Session = Depends(get_db)) -> AdminTrackResponse:
    try:
        row = create_admin_track(db, payload)
    except ValueError as exc:
        return _bad_request(str(exc))
    return AdminTrackResponse.model_validate(row)


@admin_v1.patch("/tracks/{track_id}", response_model=AdminTrackResponse)
def admin_update_track(track_id: str, payload: AdminTrackUpdateRequest, db: Session = Depends(get_db)) -> AdminTrackResponse:
    if payload.status == "published":
        existing = get_admin_track(db, track_id)
        if existing is None:
            return _track_not_found()
        if not _is_stream_ready(existing):
            return _bad_request("track media is not ready for publish (missing playlist or fallback)")
    row = update_admin_track(db, track_id, payload)
    if row is None:
        return _track_not_found()
    return AdminTrackResponse.model_validate(row)


@admin_v1.post("/tracks/{track_id}/upload/audio", response_model=AdminTrackResponse)
def admin_upload_audio(
    track_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AdminTrackResponse:
    if not file.filename:
        return _bad_request("missing filename")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".mp3", ".wav", ".m4a", ".aac"}:
        return _bad_request("unsupported audio file type")

    track_dir = RAW_AUDIO_ROOT / track_id
    track_dir.mkdir(parents=True, exist_ok=True)
    output = track_dir / f"source{suffix}"
    output.write_bytes(file.file.read())
    rel_path = f"/assets/raw-audio/managed/{track_id}/{output.name}"
    row = set_track_audio_fallback(db, track_id, rel_path)
    if row is None:
        return _track_not_found()
    _generate_hls(track_id, output)

    extracted = extract_track_metadata(output)
    if extracted is not None:
        upsert_track_metadata(db, track_id=track_id, metadata=extracted)
        extracted_duration = extracted.get("duration_sec")
        if extracted_duration is not None:
            seconds = max(0, int(round(float(extracted_duration))))
            updated = update_admin_track(
                db,
                track_id,
                AdminTrackUpdateRequest(duration_sec=seconds),
            )
            if updated is not None:
                row = updated
    else:
        probed_duration = _probe_duration_sec(output)
        if probed_duration is not None:
            seconds = max(0, int(round(probed_duration)))
            updated = update_admin_track(
                db,
                track_id,
                AdminTrackUpdateRequest(duration_sec=seconds),
            )
            if updated is not None:
                row = updated
    return AdminTrackResponse.model_validate(row)


@admin_v1.post("/tracks/{track_id}/upload/artwork", response_model=AdminTrackResponse)
def admin_upload_artwork(
    track_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AdminTrackResponse:
    if not file.filename:
        return _bad_request("missing filename")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        return _bad_request("unsupported artwork file type")

    IMAGES_ROOT.mkdir(parents=True, exist_ok=True)
    output = IMAGES_ROOT / f"{track_id}_{uuid4().hex[:8]}{suffix}"
    output.write_bytes(file.file.read())
    rel_path = f"/images/managed/{output.name}"
    row = set_track_artwork_path(db, track_id, rel_path)
    if row is None:
        return _track_not_found()
    return AdminTrackResponse.model_validate(row)


@admin_v1.post("/tracks/{track_id}/publish", response_model=AdminPublishResponse)
def admin_publish_track(track_id: str, db: Session = Depends(get_db)) -> AdminPublishResponse:
    row = get_admin_track(db, track_id)
    if row is None:
        return _track_not_found()
    if row["stream"] is None or not _is_stream_ready(row):
        return _bad_request("track media is not ready for publish (missing playlist or fallback)")
    published = publish_track(db, track_id)
    if published is None:
        return _track_not_found()
    return AdminPublishResponse.model_validate(published)


@admin_v1.get("/tracks/{track_id}/metadata", response_model=AdminTrackMetadataResponse)
def admin_track_metadata(track_id: str, db: Session = Depends(get_db)) -> AdminTrackMetadataResponse:
    row = get_track_metadata(db, track_id)
    if row is None:
        return _track_not_found()
    return AdminTrackMetadataResponse.model_validate(row)


@admin_v1.get("/stats/tracks", response_model=TrackStatsResponse)
def admin_track_stats(db: Session = Depends(get_db)) -> TrackStatsResponse:
    return TrackStatsResponse(tracks=get_track_stats(db))


@admin_v1.get("/stats/users/{user_id}", response_model=UserStatsResponse)
def admin_user_stats(user_id: str, db: Session = Depends(get_db)) -> UserStatsResponse:
    return UserStatsResponse.model_validate(get_user_stats(db, user_id))


@admin_v1.get("/logs", response_model=AdminLogsResponse)
def admin_logs(
    source: str = Query(default="backend"),
    lines: int = Query(default=200, ge=1, le=1000),
) -> AdminLogsResponse:
    sources = _log_sources()
    if source not in sources:
        return _bad_request("invalid log source")
    selected = sources[source]
    content = _tail_lines(selected, lines)
    return AdminLogsResponse(
        source=source,
        lines=content,
        line_count=len(content),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
