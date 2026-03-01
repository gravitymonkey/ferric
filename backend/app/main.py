import contextvars
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.app.admin_api import admin_v1
from backend.app.admin_ui import admin_ui
from backend.app.catalog_repository import (
    get_catalog_page,
    get_track_by_id,
    get_track_stream_by_id,
)
from backend.app.db import get_db
from backend.app.listening_repository import record_listening_event
from backend.app.schemas import (
    CatalogResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    ErrorResponse,
    HealthResponse,
    ListenEventRequest,
    ListenEventResponse,
    ResolvePlaybackRequest,
    ResolvePlaybackResponse,
    SessionStateResponse,
    TrackMetadata,
    UpdateSessionRequest,
    UpdateSessionResponse,
)
from backend.app.session_repository import (
    create_playback_session,
    get_playback_session,
    update_playback_session,
)


api_v1 = APIRouter(prefix="/api/v1")
REQUEST_ID_CTX: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
logger = logging.getLogger("ferric.api")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _ensure_file_logger() -> None:
    default_path = str(Path(__file__).resolve().parents[2] / "backend" / "logs" / "backend.log")
    log_path = Path(os.getenv("FERRIC_BACKEND_LOG_PATH", default_path))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    resolved = str(log_path.resolve())
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == resolved:
            return
    file_handler = logging.FileHandler(resolved, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(file_handler)


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


def _request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


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
    db: Session = Depends(get_db),
) -> CatalogResponse:
    return get_catalog_page(db, limit=limit, offset=offset, q=q)


@api_v1.get(
    "/tracks/{track_id}",
    response_model=TrackMetadata,
    responses={404: {"model": ErrorResponse}},
)
def get_track(track_id: str, db: Session = Depends(get_db)) -> TrackMetadata:
    track = get_track_by_id(db, track_id)
    if track is None:
        return _not_found_track_error()
    return TrackMetadata.model_validate(track)


@api_v1.post(
    "/playback/resolve",
    response_model=ResolvePlaybackResponse,
    responses={404: {"model": ErrorResponse}},
)
def resolve_playback(payload: ResolvePlaybackRequest, db: Session = Depends(get_db)) -> ResolvePlaybackResponse:
    track_id = payload.track_id
    stream = get_track_stream_by_id(db, track_id)
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
def create_session(payload: CreateSessionRequest, db: Session = Depends(get_db)) -> CreateSessionResponse:
    session_id = f"session_{uuid4().hex[:12]}"
    created = create_playback_session(db, session_id=session_id, payload=payload)
    return CreateSessionResponse(session_id=created["session_id"], created_at=created["created_at"])


@api_v1.patch(
    "/sessions/{session_id}",
    response_model=UpdateSessionResponse,
    responses={404: {"model": ErrorResponse}},
)
def update_session(
    session_id: str, payload: UpdateSessionRequest, db: Session = Depends(get_db)
) -> UpdateSessionResponse:
    updated = update_playback_session(db, session_id=session_id, payload=payload)
    if updated is None:
        return _not_found_session_error()

    return UpdateSessionResponse(
        session_id=updated["session_id"],
        updated_at=updated["updated_at"],
    )


@api_v1.get(
    "/sessions/{session_id}",
    response_model=SessionStateResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionStateResponse:
    session = get_playback_session(db, session_id=session_id)
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


@api_v1.post("/events/listen", response_model=ListenEventResponse)
def post_listen_event(
    payload: ListenEventRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ListenEventResponse:
    accepted = record_listening_event(
        db,
        user_id=payload.user_id,
        track_id=payload.track_id,
        action=payload.action,
        position_sec=payload.position_sec,
        ip_address=_request_ip(request),
    )
    if not accepted:
        return _not_found_track_error()
    return ListenEventResponse(accepted=True)


def create_app() -> FastAPI:
    _ensure_file_logger()
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
    app.include_router(admin_v1)
    app.include_router(admin_ui)
    return app


app = create_app()

REPO_ROOT = Path(__file__).resolve().parents[2]
app.mount("/images", StaticFiles(directory=REPO_ROOT / "public" / "images"), name="images")
