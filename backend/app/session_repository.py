from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.app.models import PlaybackSession
from backend.app.schemas import CreateSessionRequest, UpdateSessionRequest


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def create_playback_session(db: Session, session_id: str, payload: CreateSessionRequest) -> dict[str, str]:
    now = datetime.now(UTC)
    row = PlaybackSession(
        session_id=session_id,
        queue_track_ids_json=json.dumps(payload.queue_track_ids),
        current_track_id=payload.current_track_id,
        position_sec=payload.position_sec,
        shuffle=payload.shuffle,
        repeat_mode=payload.repeat_mode,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    return {"session_id": row.session_id, "created_at": _to_iso(row.created_at)}


def update_playback_session(db: Session, session_id: str, payload: UpdateSessionRequest) -> dict[str, str] | None:
    row = db.get(PlaybackSession, session_id)
    if row is None:
        return None

    if payload.queue_track_ids is not None:
        row.queue_track_ids_json = json.dumps(payload.queue_track_ids)
    if payload.current_track_id is not None:
        row.current_track_id = payload.current_track_id
    if payload.position_sec is not None:
        row.position_sec = payload.position_sec
    if payload.shuffle is not None:
        row.shuffle = payload.shuffle
    if payload.repeat_mode is not None:
        row.repeat_mode = payload.repeat_mode

    row.updated_at = datetime.now(UTC)
    db.add(row)
    db.commit()
    return {"session_id": row.session_id, "updated_at": _to_iso(row.updated_at)}


def get_playback_session(db: Session, session_id: str) -> dict | None:
    row = db.get(PlaybackSession, session_id)
    if row is None:
        return None

    return {
        "session_id": row.session_id,
        "queue_track_ids": json.loads(row.queue_track_ids_json),
        "current_track_id": row.current_track_id,
        "position_sec": row.position_sec,
        "shuffle": row.shuffle,
        "repeat_mode": row.repeat_mode,
    }
