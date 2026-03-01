from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    time: str


class AppMetadata(BaseModel):
    title: str


class Artwork(BaseModel):
    square_512: str | None = None


class TrackMetadata(BaseModel):
    id: str
    title: str
    artist: str
    duration_sec: int
    artwork: Artwork = Field(default_factory=Artwork)


class CatalogPage(BaseModel):
    limit: int
    offset: int
    total: int


class CatalogResponse(BaseModel):
    schema_version: str
    app: AppMetadata
    tracks: list[TrackMetadata]
    page: CatalogPage


class ErrorDetail(BaseModel):
    code: Literal["BAD_REQUEST", "TRACK_NOT_FOUND", "SESSION_NOT_FOUND", "INTERNAL_ERROR"]
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ResolveClient(BaseModel):
    model_config = ConfigDict(extra="forbid")
    platform: str
    app_version: str


class ResolvePlaybackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    track_id: str = Field(min_length=1)
    client: ResolveClient


class ResolvedStream(BaseModel):
    protocol: str
    url: str
    fallback_url: str | None = None
    expires_at: str
    requires_auth: bool


class ResolvePlaybackResponse(BaseModel):
    track_id: str
    stream: ResolvedStream


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    queue_track_ids: list[str]
    current_track_id: str
    position_sec: int = Field(ge=0)
    shuffle: bool
    repeat_mode: Literal["off", "one", "all"]


class CreateSessionResponse(BaseModel):
    session_id: str
    created_at: str


class UpdateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    queue_track_ids: list[str] | None = None
    current_track_id: str | None = None
    position_sec: int | None = Field(default=None, ge=0)
    shuffle: bool | None = None
    repeat_mode: Literal["off", "one", "all"] | None = None


class UpdateSessionResponse(BaseModel):
    session_id: str
    updated_at: str


class SessionStateResponse(BaseModel):
    session_id: str
    queue_track_ids: list[str]
    current_track_id: str
    position_sec: int
    shuffle: bool
    repeat_mode: Literal["off", "one", "all"]


class AdminTrackCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = Field(default=None, min_length=1, max_length=64)
    title: str = Field(min_length=1)
    artist: str = Field(min_length=1)
    duration_sec: int = Field(default=0, ge=0)
    status: Literal["draft", "published", "archived"] = "draft"


class AdminTrackUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = None
    artist: str | None = None
    duration_sec: int | None = Field(default=None, ge=0)
    status: Literal["draft", "published", "archived"] | None = None


class AdminTrackStream(BaseModel):
    protocol: str
    url: str
    fallback_url: str | None = None


class AdminTrackMetadataResponse(BaseModel):
    track_id: str
    analysis_version: str
    analyzed_at: str
    sample_rate_hz: int
    duration_sec: float
    tempo_bpm: float | None = None
    beat_count: int | None = None
    onset_strength_mean: float | None = None
    rms_mean: float | None = None
    rms_std: float | None = None
    spectral_centroid_mean: float | None = None
    spectral_centroid_std: float | None = None
    spectral_bandwidth_mean: float | None = None
    spectral_rolloff_mean: float | None = None
    spectral_flatness_mean: float | None = None
    zero_crossing_rate_mean: float | None = None
    mfcc_mean_json: str | None = None
    chroma_mean_json: str | None = None
    tonnetz_mean_json: str | None = None
    metadata_json: str | None = None


class AdminTrackResponse(BaseModel):
    id: str
    title: str
    artist: str
    duration_sec: int
    status: Literal["draft", "published", "archived"]
    uploaded_at: str | None
    updated_at: str
    artwork: Artwork = Field(default_factory=Artwork)
    stream: AdminTrackStream | None = None


class AdminTrackListResponse(BaseModel):
    tracks: list[AdminTrackResponse]


class AdminPublishResponse(BaseModel):
    id: str
    status: Literal["published"]


ListenAction = Literal["start", "pause", "seek", "skip_next", "skip_previous", "finish"]


class ListenEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(min_length=1, max_length=128)
    track_id: str = Field(min_length=1, max_length=64)
    action: ListenAction
    position_sec: int | None = Field(default=None, ge=0)


class ListenEventResponse(BaseModel):
    accepted: bool


class TrackStatsItem(BaseModel):
    track_id: str
    starts: int
    finishes: int
    pauses: int
    seeks: int
    skips: int
    total_events: int
    unique_users: int


class TrackStatsResponse(BaseModel):
    tracks: list[TrackStatsItem]


class UserTrackStatsItem(BaseModel):
    track_id: str
    starts: int
    finishes: int
    pauses: int
    seeks: int
    skips: int
    total_events: int


class UserStatsResponse(BaseModel):
    user_id: str
    total_events: int
    tracks: list[UserTrackStatsItem]


class AdminLogsResponse(BaseModel):
    source: str
    lines: list[str]
    line_count: int
    generated_at: str
