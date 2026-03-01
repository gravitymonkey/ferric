from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class PlaybackSession(Base):
    __tablename__ = "playback_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    queue_track_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
    current_track_id: Mapped[str] = mapped_column(String(64), nullable=False)
    position_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shuffle: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    repeat_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="off")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    artist: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="published")
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class TrackArtwork(Base):
    __tablename__ = "track_artwork"

    track_id: Mapped[str] = mapped_column(String(64), ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    square_512_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class TrackStream(Base):
    __tablename__ = "track_streams"

    track_id: Mapped[str] = mapped_column(String(64), ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    protocol: Mapped[str] = mapped_column(String(16), nullable=False, default="hls")
    playlist_path: Mapped[str] = mapped_column(String(512), nullable=False)
    fallback_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ListeningEvent(Base):
    __tablename__ = "listening_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    track_id: Mapped[str] = mapped_column(String(64), ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    position_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)


class TrackMetadata(Base):
    __tablename__ = "track_metadata"

    track_id: Mapped[str] = mapped_column(String(64), ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    analysis_version: Mapped[str] = mapped_column(String(32), nullable=False, default="librosa_v1")
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    sample_rate_hz: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, nullable=False)
    tempo_bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    beat_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    onset_strength_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    rms_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    rms_std: Mapped[float | None] = mapped_column(Float, nullable=True)
    spectral_centroid_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    spectral_centroid_std: Mapped[float | None] = mapped_column(Float, nullable=True)
    spectral_bandwidth_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    spectral_rolloff_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    spectral_flatness_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    zero_crossing_rate_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    mfcc_mean_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    chroma_mean_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    tonnetz_mean_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
