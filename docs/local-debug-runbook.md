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

Frontend shows load error / catalog not loading:

- Confirm backend is running (`/api/v1/health`)
- Confirm frontend proxy can hit backend (`/api/v1/catalog` on port 8080)
- Check backend terminal logs for request path/status

Playback works in Safari/WebKit but not Chromium/Firefox:

- Confirm `/api/v1/playback/resolve` returns both:
  - `stream.url` (HLS playlist)
  - `stream.fallback_url` (MP3 path)

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
