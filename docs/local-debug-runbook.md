# Local Startup and Debug Runbook

## Start Services

Preferred (single command):

```bash
make run
```

Manual split:

```bash
make backend
make frontend
```

Optional shell-based tail while developing:

```bash
make logs-tail
```

Apply DB migrations explicitly (optional; `make run` and `make backend` already do this):

```bash
make db-upgrade
```

Open:

`http://localhost:8080/public/index.html`

## Quick Health Checks

Backend health:

```bash
curl -s http://127.0.0.1:8000/api/v1/health
```

Catalog via backend:

```bash
curl -s http://127.0.0.1:8000/api/v1/catalog | head
```

Catalog via frontend proxy:

```bash
curl -s http://127.0.0.1:8080/api/v1/catalog | head
```

## Request ID Debugging

Send an explicit request id:

```bash
curl -i -H "x-request-id: req_manual_001" http://127.0.0.1:8000/api/v1/tracks/track_missing
```

Expected:

- Response header includes `x-request-id: req_manual_001`
- Error payload includes:
  - `error.code = "TRACK_NOT_FOUND"`
  - `error.request_id = "req_manual_001"`

## Common Local Failures

`EADDRINUSE` / port already in use:

- Change frontend port:
  - `make frontend FRONTEND_PORT=8090`
- Change backend port:
  - `make backend BACKEND_PORT=8010`
- If backend port changes, point frontend proxy at it:
  - `make frontend FRONTEND_PORT=8090 BACKEND_ORIGIN=http://127.0.0.1:8010`

DB errors (`no such table: playback_sessions` or migration mismatch):

- Run:
  - `make db-upgrade`
- If switching DB backends, set `DATABASE_URL` and re-run migrations:
  - `DATABASE_URL=sqlite:///./backend/ferric.db make db-upgrade`
  - `DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/ferric make db-upgrade`

Frontend shows load error / catalog not loading:

- Confirm backend is running (`/api/v1/health`)
- Confirm frontend proxy can hit backend (`/api/v1/catalog` on port 8080)
- Check backend terminal logs for request path/status

Playback works in Safari/WebKit but not Chromium/Firefox:

- Confirm `/api/v1/playback/resolve` returns both:
  - `stream.url` (HLS playlist)
  - `stream.fallback_url` (MP3 path)

Admin auth failures:

- Ensure `FERRIC_ADMIN_USER` / `FERRIC_ADMIN_PASSWORD` match what you enter in browser prompt.
- Defaults are `admin` / `admin` if env vars are unset.

Tail logs page empty:

- Open `http://127.0.0.1:8000/admin/logs`
- Ensure services were started via `make run`/`make run-hot`/`make backend`/`make frontend` so file logs are emitted.
- Confirm files exist:
  - `backend/logs/backend.log`
  - `backend/logs/frontend.log`

Listening stats look empty:

- Verify frontend has a `ferric_user_id` cookie after pressing play.
- Verify event ingest works:
  - `curl -s -X POST http://127.0.0.1:8000/api/v1/events/listen -H "Content-Type: application/json" -d '{"user_id":"user_debug","track_id":"track_001","action":"start","position_sec":0}'`
- Check admin stats endpoint with basic auth:
  - `curl -s -u admin:admin http://127.0.0.1:8000/api/v1/admin/stats/tracks`

Track metadata missing after audio upload:

- Ensure `librosa` is installed in your backend runtime:
  - `python3 -m pip install librosa`
- Re-upload audio and check:
  - `curl -s -u admin:admin http://127.0.0.1:8000/api/v1/admin/tracks/<track_id>/metadata`

Upload interrupted by navigation:

- While upload is in-flight, admin UI prompts before leaving:
  - `Are you sure? You will cancel your upload and processing.`
- If you leave anyway, re-open the track editor and confirm:
  - audio fallback URL exists in track response (`GET /api/v1/admin/tracks/<track_id>`)
  - HLS playlist exists on disk (`public/generated/hls/<track_id>/playlist.m3u8`)

## Regression Commands for Debug Sessions

Backend unit tests:

```bash
make test-backend
```

Backend integration flow:

```bash
make smoke
```

Complete suite:

```bash
make test
```
