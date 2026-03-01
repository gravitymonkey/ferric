from __future__ import annotations

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from backend.app.models import ListeningEvent, Track


def record_listening_event(
    db: Session,
    *,
    user_id: str,
    track_id: str,
    action: str,
    position_sec: int | None,
    ip_address: str | None,
) -> bool:
    track_exists = db.get(Track, track_id) is not None
    if not track_exists:
        return False

    event = ListeningEvent(
        user_id=user_id,
        track_id=track_id,
        action=action,
        position_sec=position_sec,
        ip_address=ip_address,
    )
    db.add(event)
    db.commit()
    return True


def get_track_stats(db: Session) -> list[dict]:
    stmt = (
        select(
            ListeningEvent.track_id,
            func.sum(case((ListeningEvent.action == "start", 1), else_=0)).label("starts"),
            func.sum(case((ListeningEvent.action == "finish", 1), else_=0)).label("finishes"),
            func.sum(case((ListeningEvent.action == "pause", 1), else_=0)).label("pauses"),
            func.sum(case((ListeningEvent.action == "seek", 1), else_=0)).label("seeks"),
            func.sum(
                case(
                    (
                        ListeningEvent.action.in_(["skip_next", "skip_previous"]),
                        1,
                    ),
                    else_=0,
                )
            ).label("skips"),
            func.count(ListeningEvent.id).label("total_events"),
            func.count(distinct(ListeningEvent.user_id)).label("unique_users"),
        )
        .group_by(ListeningEvent.track_id)
        .order_by(ListeningEvent.track_id)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "track_id": row[0],
            "starts": int(row[1] or 0),
            "finishes": int(row[2] or 0),
            "pauses": int(row[3] or 0),
            "seeks": int(row[4] or 0),
            "skips": int(row[5] or 0),
            "total_events": int(row[6] or 0),
            "unique_users": int(row[7] or 0),
        }
        for row in rows
    ]


def get_user_stats(db: Session, user_id: str) -> dict:
    total_stmt = select(func.count(ListeningEvent.id)).where(ListeningEvent.user_id == user_id)
    total_events = int(db.scalar(total_stmt) or 0)

    per_track_stmt = (
        select(
            ListeningEvent.track_id,
            func.sum(case((ListeningEvent.action == "start", 1), else_=0)).label("starts"),
            func.sum(case((ListeningEvent.action == "finish", 1), else_=0)).label("finishes"),
            func.sum(case((ListeningEvent.action == "pause", 1), else_=0)).label("pauses"),
            func.sum(case((ListeningEvent.action == "seek", 1), else_=0)).label("seeks"),
            func.sum(
                case(
                    (
                        ListeningEvent.action.in_(["skip_next", "skip_previous"]),
                        1,
                    ),
                    else_=0,
                )
            ).label("skips"),
            func.count(ListeningEvent.id).label("total_events"),
        )
        .where(ListeningEvent.user_id == user_id)
        .group_by(ListeningEvent.track_id)
        .order_by(ListeningEvent.track_id)
    )
    rows = db.execute(per_track_stmt).all()

    tracks = [
        {
            "track_id": row[0],
            "starts": int(row[1] or 0),
            "finishes": int(row[2] or 0),
            "pauses": int(row[3] or 0),
            "seeks": int(row[4] or 0),
            "skips": int(row[5] or 0),
            "total_events": int(row[6] or 0),
        }
        for row in rows
    ]
    return {"user_id": user_id, "total_events": total_events, "tracks": tracks}
