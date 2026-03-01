import contextvars
import logging
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.catalog import get_catalog_page, get_track_by_id, get_track_stream_by_id
from backend.app.schemas import (
    CatalogResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    ErrorResponse,
    HealthResponse,
    ResolvePlaybackRequest,
    ResolvePlaybackResponse,
    SessionStateResponse,
    TrackMetadata,
    UpdateSessionRequest,
    UpdateSessionResponse,
)


api_v1 = APIRouter(prefix="/api/v1")
SESSION_STORE: dict[str, dict] = {}
REQUEST_ID_CTX: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
logger = logging.getLogger("ferric.api")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _get_request_id() -> str:
    request_id = REQUEST_ID_CTX.get()
    if request_id:
        return request_id
    return f"req_{uuid4().hex[:12]}"


def _error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": _get_request_id(),
            },
        },
    )


def _not_found_track_error() -> JSONResponse:
    return _error_response(code="TRACK_NOT_FOUND", message="Track does not exist", status_code=404)


def _not_found_session_error() -> JSONResponse:
    return _error_response(code="SESSION_NOT_FOUND", message="Session does not exist", status_code=404)


@api_v1.get("/health")
def get_health() -> HealthResponse:
    now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return HealthResponse(
        status="ok",
        service="ferric-api",
        time=now_utc,
    )


@api_v1.get("/catalog", response_model=CatalogResponse)
def get_catalog(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
) -> CatalogResponse:
    return get_catalog_page(limit=limit, offset=offset, q=q)


@api_v1.get(
    "/tracks/{track_id}",
    response_model=TrackMetadata,
    responses={404: {"model": ErrorResponse}},
)
def get_track(track_id: str) -> TrackMetadata:
    track = get_track_by_id(track_id)
    if track is None:
        return _not_found_track_error()
    return TrackMetadata.model_validate(track)


@api_v1.post(
    "/playback/resolve",
    response_model=ResolvePlaybackResponse,
    responses={404: {"model": ErrorResponse}},
)
def resolve_playback(payload: ResolvePlaybackRequest) -> ResolvePlaybackResponse:
    track_id = payload.track_id
    stream = get_track_stream_by_id(track_id)
    if stream is None:
        return _not_found_track_error()

    expires_at = (datetime.now(UTC) + timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
    return ResolvePlaybackResponse(
        track_id=track_id,
        stream={
            "protocol": stream["protocol"],
            "url": stream["url"],
            "fallback_url": stream.get("fallback_url"),
            "expires_at": expires_at,
            "requires_auth": False,
        },
    )


@api_v1.post("/sessions", response_model=CreateSessionResponse, status_code=201)
def create_session(payload: CreateSessionRequest) -> CreateSessionResponse:
    session_id = f"session_{uuid4().hex[:12]}"
    now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    session = {
        "session_id": session_id,
        "queue_track_ids": payload.queue_track_ids,
        "current_track_id": payload.current_track_id,
        "position_sec": payload.position_sec,
        "shuffle": payload.shuffle,
        "repeat_mode": payload.repeat_mode,
        "created_at": now_utc,
        "updated_at": now_utc,
    }
    SESSION_STORE[session_id] = session

    return CreateSessionResponse(session_id=session_id, created_at=now_utc)


@api_v1.patch(
    "/sessions/{session_id}",
    response_model=UpdateSessionResponse,
    responses={404: {"model": ErrorResponse}},
)
def update_session(session_id: str, payload: UpdateSessionRequest) -> UpdateSessionResponse:
    session = SESSION_STORE.get(session_id)
    if session is None:
        return _not_found_session_error()

    updatable_keys = {"queue_track_ids", "current_track_id", "position_sec", "shuffle", "repeat_mode"}
    for key in updatable_keys:
        value = getattr(payload, key)
        if value is not None:
            if key == "queue_track_ids":
                session[key] = list(value)
            else:
                session[key] = value

    now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    session["updated_at"] = now_utc

    return UpdateSessionResponse(
        session_id=session_id,
        updated_at=now_utc,
    )


@api_v1.get(
    "/sessions/{session_id}",
    response_model=SessionStateResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_session(session_id: str) -> SessionStateResponse:
    session = SESSION_STORE.get(session_id)
    if session is None:
        return _not_found_session_error()

    return SessionStateResponse(
        session_id=session["session_id"],
        queue_track_ids=session["queue_track_ids"],
        current_track_id=session["current_track_id"],
        position_sec=session["position_sec"],
        shuffle=session["shuffle"],
        repeat_mode=session["repeat_mode"],
    )


def create_app() -> FastAPI:
    app = FastAPI(title="ferric-api", version="0.1.0")

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex[:12]}"
        token = REQUEST_ID_CTX.set(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_error method=%s path=%s duration_ms=%.2f request_id=%s",
                request.method,
                request.url.path,
                elapsed_ms,
                request_id,
            )
            REQUEST_ID_CTX.reset(token)
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["x-request-id"] = request_id
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        REQUEST_ID_CTX.reset(token)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return _error_response(code="BAD_REQUEST", message="Request validation failed", status_code=400)

    app.include_router(api_v1)
    return app


app = create_app()
