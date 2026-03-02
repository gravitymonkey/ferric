# Ferric Backend

## Run (dev)

```bash
make deps
make backend
```

Dependency manifest:

- `backend/requirements.txt`

Admin credentials are required (backend startup fails if either is unset/empty):

- `FERRIC_ADMIN_USER`
- `FERRIC_ADMIN_PASSWORD`

App-level auth throttling env vars (optional, defaults shown):

- `FERRIC_ADMIN_MAX_FAILED_ATTEMPTS=5`
- `FERRIC_ADMIN_MAX_FAILED_IP_ATTEMPTS=30`
- `FERRIC_ADMIN_FAIL_WINDOW_SEC=600`
- `FERRIC_ADMIN_LOCKOUT_SEC=900`

Upload limits env vars (optional, defaults shown):

- `FERRIC_MAX_AUDIO_UPLOAD_MB=100`
- `FERRIC_MAX_ARTWORK_UPLOAD_MB=8`

Admin UI:

- `http://127.0.0.1:8000/admin`

Listening event ingest:

- `POST /api/v1/events/listen`
  - body: `user_id`, `track_id`, `action`, optional `position_sec`

Admin stats endpoints:

- `GET /api/v1/admin/stats/tracks`
- `GET /api/v1/admin/stats/users/{user_id}`

Admin log tail endpoint:

- `GET /api/v1/admin/logs?source=backend|frontend&lines=200`

Track metadata endpoint:

- `GET /api/v1/admin/tracks/{track_id}/metadata`

Optional extraction dependency:

- Install `librosa` to enable upload-time audio feature extraction.
- If `librosa` is not installed, uploads still succeed and metadata extraction is skipped.
- `Pillow` is used for artwork-content validation on upload.

## Tests

```bash
make test-backend
```

## Migrations

```bash
make db-upgrade
make db-downgrade
make db-seed
```

## Local Debug Runbook

See:

- `docs/local-debug-runbook.md`
