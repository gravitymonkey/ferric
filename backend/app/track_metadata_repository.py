from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models import TrackMetadata


def upsert_track_metadata(db: Session, track_id: str, metadata: dict[str, Any]) -> None:
    row = db.get(TrackMetadata, track_id)
    now = datetime.now(UTC)
    if row is None:
        row = TrackMetadata(
            track_id=track_id,
            analysis_version=metadata.get("analysis_version", "librosa_v1"),
            analyzed_at=now,
            sample_rate_hz=int(metadata["sample_rate_hz"]),
            duration_sec=float(metadata["duration_sec"]),
            tempo_bpm=metadata.get("tempo_bpm"),
            beat_count=metadata.get("beat_count"),
            onset_strength_mean=metadata.get("onset_strength_mean"),
            rms_mean=metadata.get("rms_mean"),
            rms_std=metadata.get("rms_std"),
            spectral_centroid_mean=metadata.get("spectral_centroid_mean"),
            spectral_centroid_std=metadata.get("spectral_centroid_std"),
            spectral_bandwidth_mean=metadata.get("spectral_bandwidth_mean"),
            spectral_rolloff_mean=metadata.get("spectral_rolloff_mean"),
            spectral_flatness_mean=metadata.get("spectral_flatness_mean"),
            zero_crossing_rate_mean=metadata.get("zero_crossing_rate_mean"),
            mfcc_mean_json=metadata.get("mfcc_mean_json"),
            chroma_mean_json=metadata.get("chroma_mean_json"),
            tonnetz_mean_json=metadata.get("tonnetz_mean_json"),
            metadata_json=metadata.get("metadata_json"),
        )
    else:
        row.analysis_version = metadata.get("analysis_version", row.analysis_version)
        row.analyzed_at = now
        row.sample_rate_hz = int(metadata["sample_rate_hz"])
        row.duration_sec = float(metadata["duration_sec"])
        row.tempo_bpm = metadata.get("tempo_bpm")
        row.beat_count = metadata.get("beat_count")
        row.onset_strength_mean = metadata.get("onset_strength_mean")
        row.rms_mean = metadata.get("rms_mean")
        row.rms_std = metadata.get("rms_std")
        row.spectral_centroid_mean = metadata.get("spectral_centroid_mean")
        row.spectral_centroid_std = metadata.get("spectral_centroid_std")
        row.spectral_bandwidth_mean = metadata.get("spectral_bandwidth_mean")
        row.spectral_rolloff_mean = metadata.get("spectral_rolloff_mean")
        row.spectral_flatness_mean = metadata.get("spectral_flatness_mean")
        row.zero_crossing_rate_mean = metadata.get("zero_crossing_rate_mean")
        row.mfcc_mean_json = metadata.get("mfcc_mean_json")
        row.chroma_mean_json = metadata.get("chroma_mean_json")
        row.tonnetz_mean_json = metadata.get("tonnetz_mean_json")
        row.metadata_json = metadata.get("metadata_json")

    db.add(row)
    db.commit()


def get_track_metadata(db: Session, track_id: str) -> dict[str, Any] | None:
    row = db.get(TrackMetadata, track_id)
    if row is None:
        return None
    return {
        "track_id": row.track_id,
        "analysis_version": row.analysis_version,
        "analyzed_at": row.analyzed_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "sample_rate_hz": row.sample_rate_hz,
        "duration_sec": row.duration_sec,
        "tempo_bpm": row.tempo_bpm,
        "beat_count": row.beat_count,
        "onset_strength_mean": row.onset_strength_mean,
        "rms_mean": row.rms_mean,
        "rms_std": row.rms_std,
        "spectral_centroid_mean": row.spectral_centroid_mean,
        "spectral_centroid_std": row.spectral_centroid_std,
        "spectral_bandwidth_mean": row.spectral_bandwidth_mean,
        "spectral_rolloff_mean": row.spectral_rolloff_mean,
        "spectral_flatness_mean": row.spectral_flatness_mean,
        "zero_crossing_rate_mean": row.zero_crossing_rate_mean,
        "mfcc_mean_json": row.mfcc_mean_json,
        "chroma_mean_json": row.chroma_mean_json,
        "tonnetz_mean_json": row.tonnetz_mean_json,
        "metadata_json": row.metadata_json,
    }
