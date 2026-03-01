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
