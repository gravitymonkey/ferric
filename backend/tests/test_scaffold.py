import pytest
from base64 import b64encode
from datetime import datetime
import os
from pathlib import Path
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import get_db
from backend.app import admin_api
from backend.app.main import create_app
from backend.app.models import Base

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_app_scaffold_boots(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["info"]["title"] == "ferric-api"
    assert payload["info"]["version"] == "0.1.0"


def test_health_endpoint_schema(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "ferric-api"
    assert payload["time"].endswith("Z")
    assert "T" in payload["time"]
    assert response.headers["x-request-id"].startswith("req_")


def test_catalog_endpoint_schema(client: TestClient) -> None:
    response = client.get("/api/v1/catalog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "1.0"
    assert payload["app"]["title"] == "Ferric POC"
    assert isinstance(payload["tracks"], list)
    assert "limit" in payload["page"]
    assert "offset" in payload["page"]
    assert "total" in payload["page"]

    first = payload["tracks"][0]
    assert {"id", "title", "artist", "artwork", "duration_sec"} <= set(first.keys())


def test_catalog_endpoint_query_params(client: TestClient) -> None:
    response = client.get("/api/v1/catalog", params={"q": "scars", "limit": 1, "offset": 0})
    assert response.status_code == 200
    payload = response.json()
    assert payload["page"]["limit"] == 1
    assert payload["page"]["offset"] == 0
    assert payload["page"]["total"] >= 1
    assert len(payload["tracks"]) == 1
    assert payload["tracks"][0]["title"].lower() == "scars"


def test_track_endpoint_schema(client: TestClient) -> None:
    response = client.get("/api/v1/tracks/track_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "track_001"
    assert payload["title"] == "Scars"
    assert payload["artist"] == "Example Artist"
    assert isinstance(payload["duration_sec"], int)
    assert "square_512" in payload["artwork"]


def test_track_endpoint_not_found_schema(client: TestClient) -> None:
    response = client.get("/api/v1/tracks/track_does_not_exist")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "TRACK_NOT_FOUND"
    assert payload["error"]["message"] == "Track does not exist"
    assert payload["error"]["request_id"].startswith("req_")


def test_request_id_propagates_to_error_payload(client: TestClient) -> None:
    response = client.get("/api/v1/tracks/track_does_not_exist", headers={"x-request-id": "req_client_123"})

    assert response.status_code == 404
    assert response.headers["x-request-id"] == "req_client_123"
    payload = response.json()
    assert payload["error"]["request_id"] == "req_client_123"


def test_playback_resolve_schema(client: TestClient) -> None:
    response = client.post(
        "/api/v1/playback/resolve",
        json={
            "track_id": "track_001",
            "client": {"platform": "web", "app_version": "0.1.0"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["track_id"] == "track_001"
    assert payload["stream"]["protocol"] == "hls"
    assert payload["stream"]["url"] == "/generated/hls/track_001/playlist.m3u8"
    assert payload["stream"]["fallback_url"] == "/assets/raw-audio/MagneticHands.mp3"
    assert payload["stream"]["requires_auth"] is False
    assert payload["stream"]["expires_at"].endswith("Z")


def test_playback_resolve_not_found_schema(client: TestClient) -> None:
    response = client.post(
        "/api/v1/playback/resolve",
        json={
            "track_id": "track_does_not_exist",
            "client": {"platform": "web", "app_version": "0.1.0"},
        },
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "TRACK_NOT_FOUND"
    assert payload["error"]["message"] == "Track does not exist"
    assert payload["error"]["request_id"].startswith("req_")


def test_sessions_create_update_get_flow(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/sessions",
        json={
            "queue_track_ids": ["track_001", "track_002"],
            "current_track_id": "track_001",
            "position_sec": 0,
            "shuffle": False,
            "repeat_mode": "off",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["session_id"].startswith("session_")
    assert created["created_at"].endswith("Z")

    session_id = created["session_id"]
    patch_response = client.patch(
        f"/api/v1/sessions/{session_id}",
        json={
            "current_track_id": "track_002",
            "position_sec": 11,
            "shuffle": True,
            "repeat_mode": "all",
        },
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["session_id"] == session_id
    assert patched["updated_at"].endswith("Z")

    get_response = client.get(f"/api/v1/sessions/{session_id}")
    assert get_response.status_code == 200
    restored = get_response.json()
    assert restored["session_id"] == session_id
    assert restored["queue_track_ids"] == ["track_001", "track_002"]
    assert restored["current_track_id"] == "track_002"
    assert restored["position_sec"] == 11
    assert restored["shuffle"] is True
    assert restored["repeat_mode"] == "all"


def test_sessions_not_found_schema(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/session_does_not_exist")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "SESSION_NOT_FOUND"
    assert payload["error"]["message"] == "Session does not exist"
    assert payload["error"]["request_id"].startswith("req_")


def test_playback_resolve_bad_request_schema(client: TestClient) -> None:
    response = client.post(
        "/api/v1/playback/resolve",
        json={"track_id": "track_001"},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "BAD_REQUEST"
    assert payload["error"]["message"] == "Request validation failed"
    assert payload["error"]["request_id"].startswith("req_")


def test_sessions_create_bad_request_schema(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sessions",
        json={
            "queue_track_ids": ["track_001"],
            "current_track_id": "track_001",
            "position_sec": -1,
            "shuffle": False,
            "repeat_mode": "off",
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "BAD_REQUEST"
    assert payload["error"]["message"] == "Request validation failed"
    assert payload["error"]["request_id"].startswith("req_")


def _admin_headers(user: str = "admin", password: str = "admin") -> dict[str, str]:
    token = b64encode(f"{user}:{password}".encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {token}"}


def test_admin_requires_basic_auth(client: TestClient) -> None:
    response = client.get("/api/v1/admin/tracks")
    assert response.status_code == 401


def test_admin_track_create_update_publish_flow(client: TestClient) -> None:
    headers = _admin_headers()
    create_response = client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "id": "track_admin_001",
            "title": "Admin Song",
            "artist": "Admin Artist",
            "duration_sec": 222,
            "status": "draft",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["id"] == "track_admin_001"
    assert created["status"] == "draft"
    assert created["uploaded_at"] is None
    assert created["updated_at"].endswith("Z")
    created_updated_at = datetime.fromisoformat(created["updated_at"].replace("Z", "+00:00"))

    update_response = client.patch(
        "/api/v1/admin/tracks/track_admin_001",
        headers=headers,
        json={"title": "Admin Song Updated", "status": "draft"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Admin Song Updated"
    assert updated["updated_at"].endswith("Z")
    assert datetime.fromisoformat(updated["updated_at"].replace("Z", "+00:00")) >= created_updated_at

    # Attach stream metadata so publish is allowed.
    upload_audio_response = client.post(
        "/api/v1/admin/tracks/track_admin_001/upload/audio",
        headers=headers,
        files={"file": ("sample.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )
    assert upload_audio_response.status_code == 200
    stream_payload = upload_audio_response.json()
    assert stream_payload["stream"]["fallback_url"].startswith("/assets/raw-audio/managed/track_admin_001/")
    assert stream_payload["updated_at"].endswith("Z")

    # Fake upload bytes are not valid media; create a placeholder playlist for publish-readiness.
    playlist = REPO_ROOT / "public" / "generated" / "hls" / "track_admin_001" / "playlist.m3u8"
    playlist.parent.mkdir(parents=True, exist_ok=True)
    playlist.write_text("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-ENDLIST\n", encoding="utf-8")

    publish_response = client.post("/api/v1/admin/tracks/track_admin_001/publish", headers=headers)
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    published_track_response = client.get("/api/v1/admin/tracks/track_admin_001", headers=headers)
    assert published_track_response.status_code == 200
    published_track = published_track_response.json()
    assert published_track["uploaded_at"].endswith("Z")

    catalog_response = client.get("/api/v1/catalog", params={"q": "admin song updated"})
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    ids = [track["id"] for track in catalog["tracks"]]
    assert "track_admin_001" in ids


def test_admin_track_create_generates_uuid_when_id_omitted(client: TestClient) -> None:
    headers = _admin_headers()
    create_response = client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "title": "UUID Song",
            "artist": "UUID Artist",
            "status": "draft",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    parsed = UUID(created["id"])
    assert str(parsed) == created["id"]
    assert created["duration_sec"] == 0


def test_admin_get_track_by_id(client: TestClient) -> None:
    headers = _admin_headers()
    create_response = client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "title": "Lookup Song",
            "artist": "Lookup Artist",
            "duration_sec": 145,
            "status": "draft",
        },
    )
    assert create_response.status_code == 200
    track_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/admin/tracks/{track_id}", headers=headers)
    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload["id"] == track_id
    assert payload["title"] == "Lookup Song"
    assert payload["artist"] == "Lookup Artist"
    assert payload["uploaded_at"] is None
    assert payload["updated_at"].endswith("Z")


def test_uploaded_at_set_once_on_first_publish_transition(client: TestClient) -> None:
    headers = _admin_headers()
    create_response = client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "title": "Upload Stamp Song",
            "artist": "Stamp Artist",
            "duration_sec": 111,
            "status": "draft",
        },
    )
    assert create_response.status_code == 200
    track_id = create_response.json()["id"]
    assert create_response.json()["uploaded_at"] is None

    first_publish = client.patch(
        f"/api/v1/admin/tracks/{track_id}",
        headers=headers,
        json={"status": "published"},
    )
    assert first_publish.status_code == 400
    assert "not ready for publish" in first_publish.json()["error"]["message"]

    upload_audio_response = client.post(
        f"/api/v1/admin/tracks/{track_id}/upload/audio",
        headers=headers,
        files={"file": ("sample.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )
    assert upload_audio_response.status_code == 200
    playlist = REPO_ROOT / "public" / "generated" / "hls" / track_id / "playlist.m3u8"
    playlist.parent.mkdir(parents=True, exist_ok=True)
    playlist.write_text("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-ENDLIST\n", encoding="utf-8")

    ok_publish = client.patch(
        f"/api/v1/admin/tracks/{track_id}",
        headers=headers,
        json={"status": "published"},
    )
    assert ok_publish.status_code == 200
    first_uploaded_at = ok_publish.json()["uploaded_at"]
    assert first_uploaded_at is not None

    archive = client.patch(
        f"/api/v1/admin/tracks/{track_id}",
        headers=headers,
        json={"status": "archived"},
    )
    assert archive.status_code == 200
    assert archive.json()["uploaded_at"] == first_uploaded_at

    republish = client.patch(
        f"/api/v1/admin/tracks/{track_id}",
        headers=headers,
        json={"status": "published"},
    )
    assert republish.status_code == 200
    assert republish.json()["uploaded_at"] == first_uploaded_at


def test_admin_update_rejects_published_status_when_media_not_ready(client: TestClient) -> None:
    headers = _admin_headers()
    create_response = client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "title": "Not Ready Song",
            "artist": "Not Ready Artist",
            "duration_sec": 140,
            "status": "draft",
        },
    )
    assert create_response.status_code == 200
    track_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/admin/tracks/{track_id}",
        headers=headers,
        json={"status": "published"},
    )
    assert update_response.status_code == 400
    assert "not ready for publish" in update_response.json()["error"]["message"]


def test_admin_publish_rejects_when_media_not_ready(client: TestClient) -> None:
    headers = _admin_headers()
    create_response = client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "title": "Publish Guard Song",
            "artist": "Publish Guard Artist",
            "duration_sec": 150,
            "status": "draft",
        },
    )
    assert create_response.status_code == 200
    track_id = create_response.json()["id"]

    publish_response = client.post(f"/api/v1/admin/tracks/{track_id}/publish", headers=headers)
    assert publish_response.status_code == 400
    assert "not ready for publish" in publish_response.json()["error"]["message"]


def test_admin_logs_endpoint_reads_allowlisted_files(client: TestClient, tmp_path: Path) -> None:
    headers = _admin_headers()
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "backend.log").write_text("line1\nline2\nline3\n", encoding="utf-8")
    (log_dir / "frontend.log").write_text("f1\nf2\n", encoding="utf-8")
    old = os.environ.get("FERRIC_LOG_DIR")
    os.environ["FERRIC_LOG_DIR"] = str(log_dir)
    try:
        response = client.get("/api/v1/admin/logs", headers=headers, params={"source": "backend", "lines": 2})
        assert response.status_code == 200
        payload = response.json()
        assert payload["source"] == "backend"
        assert payload["line_count"] == 2
        assert payload["lines"] == ["line2", "line3"]

        bad = client.get("/api/v1/admin/logs", headers=headers, params={"source": "system", "lines": 2})
        assert bad.status_code == 400
    finally:
        if old is None:
            os.environ.pop("FERRIC_LOG_DIR", None)
        else:
            os.environ["FERRIC_LOG_DIR"] = old


def test_admin_logs_endpoint_frontend_source(client: TestClient, tmp_path: Path) -> None:
    headers = _admin_headers()
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "backend.log").write_text("b1\n", encoding="utf-8")
    (log_dir / "frontend.log").write_text("f1\nf2\nf3\n", encoding="utf-8")
    old = os.environ.get("FERRIC_LOG_DIR")
    os.environ["FERRIC_LOG_DIR"] = str(log_dir)
    try:
        response = client.get("/api/v1/admin/logs", headers=headers, params={"source": "frontend", "lines": 2})
        assert response.status_code == 200
        payload = response.json()
        assert payload["source"] == "frontend"
        assert payload["line_count"] == 2
        assert payload["lines"] == ["f2", "f3"]
    finally:
        if old is None:
            os.environ.pop("FERRIC_LOG_DIR", None)
        else:
            os.environ["FERRIC_LOG_DIR"] = old


def test_admin_logs_endpoint_missing_file_returns_empty(client: TestClient, tmp_path: Path) -> None:
    headers = _admin_headers()
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    old = os.environ.get("FERRIC_LOG_DIR")
    os.environ["FERRIC_LOG_DIR"] = str(log_dir)
    try:
        response = client.get("/api/v1/admin/logs", headers=headers, params={"source": "backend", "lines": 50})
        assert response.status_code == 200
        payload = response.json()
        assert payload["source"] == "backend"
        assert payload["line_count"] == 0
        assert payload["lines"] == []
    finally:
        if old is None:
            os.environ.pop("FERRIC_LOG_DIR", None)
        else:
            os.environ["FERRIC_LOG_DIR"] = old


def test_admin_upload_artwork(client: TestClient) -> None:
    headers = _admin_headers()
    client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "id": "track_admin_002",
            "title": "Artwork Song",
            "artist": "Visual Artist",
            "duration_sec": 180,
            "status": "draft",
        },
    )

    response = client.post(
        "/api/v1/admin/tracks/track_admin_002/upload/artwork",
        headers=headers,
        files={"file": ("cover.jpg", b"fake-jpeg-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["artwork"]["square_512"].startswith("/images/managed/")


def test_admin_upload_audio_persists_track_metadata(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _admin_headers()
    client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "id": "track_meta_001",
            "title": "Meta Song",
            "artist": "Meta Artist",
            "duration_sec": 123,
            "status": "draft",
        },
    )

    monkeypatch.setattr(
        admin_api,
        "extract_track_metadata",
        lambda _path: {
            "analysis_version": "librosa_v1",
            "sample_rate_hz": 44100,
            "duration_sec": 123.45,
            "tempo_bpm": 120.1,
            "beat_count": 256,
            "onset_strength_mean": 0.4,
            "rms_mean": 0.2,
            "rms_std": 0.05,
            "spectral_centroid_mean": 2100.0,
            "spectral_centroid_std": 300.0,
            "spectral_bandwidth_mean": 1400.0,
            "spectral_rolloff_mean": 5200.0,
            "spectral_flatness_mean": 0.09,
            "zero_crossing_rate_mean": 0.12,
            "mfcc_mean_json": "[0.1,0.2]",
            "chroma_mean_json": "[0.3,0.4]",
            "tonnetz_mean_json": "[0.5,0.6]",
            "metadata_json": '{"extractor":"test"}',
        },
    )

    upload_response = client.post(
        "/api/v1/admin/tracks/track_meta_001/upload/audio",
        headers=headers,
        files={"file": ("sample.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )
    assert upload_response.status_code == 200

    metadata_response = client.get("/api/v1/admin/tracks/track_meta_001/metadata", headers=headers)
    assert metadata_response.status_code == 200
    payload = metadata_response.json()
    assert payload["track_id"] == "track_meta_001"
    assert payload["sample_rate_hz"] == 44100
    assert payload["tempo_bpm"] == 120.1


def test_admin_upload_audio_updates_track_duration_from_metadata(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _admin_headers()
    client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "id": "track_meta_duration_001",
            "title": "Duration Song",
            "artist": "Duration Artist",
            "duration_sec": 10,
            "status": "draft",
        },
    )

    monkeypatch.setattr(
        admin_api,
        "extract_track_metadata",
        lambda _path: {
            "analysis_version": "librosa_v1",
            "sample_rate_hz": 44100,
            "duration_sec": 245.4,
        },
    )

    upload_response = client.post(
        "/api/v1/admin/tracks/track_meta_duration_001/upload/audio",
        headers=headers,
        files={"file": ("sample.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )
    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["duration_sec"] == 245

    get_response = client.get("/api/v1/admin/tracks/track_meta_duration_001", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["duration_sec"] == 245


def test_admin_upload_audio_updates_track_duration_via_ffprobe_fallback(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _admin_headers()
    client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "id": "track_probe_duration_001",
            "title": "Probe Song",
            "artist": "Probe Artist",
            "duration_sec": 10,
            "status": "draft",
        },
    )

    monkeypatch.setattr(admin_api, "extract_track_metadata", lambda _path: None)
    monkeypatch.setattr(admin_api, "_probe_duration_sec", lambda _path: 301.7)

    upload_response = client.post(
        "/api/v1/admin/tracks/track_probe_duration_001/upload/audio",
        headers=headers,
        files={"file": ("sample.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )
    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["duration_sec"] == 302

    get_response = client.get("/api/v1/admin/tracks/track_probe_duration_001", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["duration_sec"] == 302


def test_listen_events_ingest_and_stats(client: TestClient) -> None:
    headers = _admin_headers()
    client.post(
        "/api/v1/admin/tracks",
        headers=headers,
        json={
            "id": "track_stats_001",
            "title": "Stats Song",
            "artist": "Data Artist",
            "duration_sec": 200,
            "status": "published",
        },
    )

    event1 = client.post(
        "/api/v1/events/listen",
        json={"user_id": "user_alpha", "track_id": "track_stats_001", "action": "start", "position_sec": 0},
        headers={"x-forwarded-for": "203.0.113.10"},
    )
    assert event1.status_code == 200
    assert event1.json()["accepted"] is True

    event2 = client.post(
        "/api/v1/events/listen",
        json={"user_id": "user_alpha", "track_id": "track_stats_001", "action": "finish", "position_sec": 200},
    )
    assert event2.status_code == 200

    event3 = client.post(
        "/api/v1/events/listen",
        json={"user_id": "user_beta", "track_id": "track_stats_001", "action": "skip_next", "position_sec": 42},
    )
    assert event3.status_code == 200

    track_stats = client.get("/api/v1/admin/stats/tracks", headers=headers)
    assert track_stats.status_code == 200
    payload = track_stats.json()
    row = next((item for item in payload["tracks"] if item["track_id"] == "track_stats_001"), None)
    assert row is not None
    assert row["starts"] == 1
    assert row["finishes"] == 1
    assert row["skips"] == 1
    assert row["unique_users"] == 2
    assert row["total_events"] == 3

    user_stats = client.get("/api/v1/admin/stats/users/user_alpha", headers=headers)
    assert user_stats.status_code == 200
    up = user_stats.json()
    assert up["user_id"] == "user_alpha"
    assert up["total_events"] == 2
    assert up["tracks"][0]["track_id"] == "track_stats_001"


def test_listen_event_missing_track_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/events/listen",
        json={"user_id": "user_alpha", "track_id": "track_missing", "action": "start", "position_sec": 0},
    )
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "TRACK_NOT_FOUND"
