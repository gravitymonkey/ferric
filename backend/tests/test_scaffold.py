from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_app_scaffold_boots() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["info"]["title"] == "ferric-api"
    assert payload["info"]["version"] == "0.1.0"


def test_health_endpoint_schema() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "ferric-api"
    assert payload["time"].endswith("Z")
    assert "T" in payload["time"]
    assert response.headers["x-request-id"].startswith("req_")


def test_catalog_endpoint_schema() -> None:
    app = create_app()
    client = TestClient(app)
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


def test_catalog_endpoint_query_params() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/catalog", params={"q": "scars", "limit": 1, "offset": 0})
    assert response.status_code == 200
    payload = response.json()
    assert payload["page"]["limit"] == 1
    assert payload["page"]["offset"] == 0
    assert payload["page"]["total"] >= 1
    assert len(payload["tracks"]) == 1
    assert payload["tracks"][0]["title"].lower() == "scars"


def test_track_endpoint_schema() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/tracks/track_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "track_001"
    assert payload["title"] == "Scars"
    assert payload["artist"] == "Example Artist"
    assert isinstance(payload["duration_sec"], int)
    assert "square_512" in payload["artwork"]


def test_track_endpoint_not_found_schema() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/tracks/track_does_not_exist")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "TRACK_NOT_FOUND"
    assert payload["error"]["message"] == "Track does not exist"
    assert payload["error"]["request_id"].startswith("req_")


def test_request_id_propagates_to_error_payload() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/tracks/track_does_not_exist", headers={"x-request-id": "req_client_123"})

    assert response.status_code == 404
    assert response.headers["x-request-id"] == "req_client_123"
    payload = response.json()
    assert payload["error"]["request_id"] == "req_client_123"


def test_playback_resolve_schema() -> None:
    app = create_app()
    client = TestClient(app)
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


def test_playback_resolve_not_found_schema() -> None:
    app = create_app()
    client = TestClient(app)
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


def test_sessions_create_update_get_flow() -> None:
    app = create_app()
    client = TestClient(app)

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


def test_sessions_not_found_schema() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/sessions/session_does_not_exist")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "SESSION_NOT_FOUND"
    assert payload["error"]["message"] == "Session does not exist"
    assert payload["error"]["request_id"].startswith("req_")


def test_playback_resolve_bad_request_schema() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/playback/resolve",
        json={"track_id": "track_001"},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "BAD_REQUEST"
    assert payload["error"]["message"] == "Request validation failed"
    assert payload["error"]["request_id"].startswith("req_")


def test_sessions_create_bad_request_schema() -> None:
    app = create_app()
    client = TestClient(app)

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
