# Development Guide

## Build Media Assets

Generate HLS assets from local source audio:

```bash
npm run build:hls
```

Defaults:

- Source audio: `assets/raw-audio/`
- Generated output: `public/generated/hls/`
- Catalog source of track IDs: `public/catalog.json`

## Run Locally

Preferred:

```bash
make run
```

Config via `.env`:

- Copy `.env.example` to `.env` at repo root.
- `Makefile` auto-loads `.env` values for local commands.
- Common overrides:
- `BACKEND_HOST`
- `BACKEND_PORT`
- `FRONTEND_PORT`
- `BACKEND_ORIGIN` (frontend proxy target, usually `http://127.0.0.1:<BACKEND_PORT>`)

Dependency bootstrap (also invoked by `make run`, `make run-hot`, `make backend`, and `make backend-hot`):

```bash
make deps
```

Manual split (if needed):

```bash
make backend
make frontend
```

## Database Migrations (Alembic)

Apply latest migration:

```bash
make db-upgrade
```

Seed catalog rows from `public/catalog.json`:

```bash
make db-seed
```

Rollback one migration:

```bash
make db-downgrade
```

Set DB backend via `DATABASE_URL`:

- SQLite default: `sqlite:///./backend/ferric.db`
- Postgres example:
  - `DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/ferric make db-upgrade`

## Admin UI + API

Admin UI route:

- `http://127.0.0.1:8000/admin`
- Tail logs page: `http://127.0.0.1:8000/admin/logs`
- Listings columns: `Title`, `Artist`, `Status`, `Uploaded`, `Updated`, `Plays`
- Listings timestamp display format: `MM/DD/YY HH:MM AM/PM`
- Edit page save control shows inline status (`Saving...`, `Saved`, `Save failed`)

Auth:

- HTTP Basic auth (lightweight POC)
- Defaults: `admin` / `admin`
- Override:
- `FERRIC_ADMIN_USER`
- `FERRIC_ADMIN_PASSWORD`

Log config (safe file-backed admin tail endpoint):

- `FERRIC_LOG_DIR` (default `./backend/logs`)
- `FERRIC_BACKEND_LOG_PATH` (default `./backend/logs/backend.log`)
- `FERRIC_FRONTEND_LOG_PATH` (default `./backend/logs/frontend.log`)

Admin log API:

- `GET /api/v1/admin/logs?source=backend|frontend&lines=1..1000`
- Source is allowlisted and file-backed; no shell command execution.

Listening analytics:

- Frontend creates `ferric_user_id` cookie on first listening interaction.
- Frontend posts actions to `POST /api/v1/events/listen` (`start`, `pause`, `seek`, `skip_next`, `skip_previous`, `finish`).
- Aggregate stats available in admin API:
  - `GET /api/v1/admin/stats/tracks`
  - `GET /api/v1/admin/stats/users/{user_id}`

Upload-time track metadata extraction:

- Backend attempts to extract features with `librosa` on admin audio upload.
- Backend attempts immediate HLS generation with `ffmpeg` on admin audio upload.
- If `librosa` is unavailable, backend falls back to probing audio duration via `ffprobe` so track duration still updates.
- Metadata is persisted in `track_metadata`.
- New track create no longer requires manual `duration_sec`; default is `0` until audio upload extraction updates duration.
- During in-flight upload, admin UI prompts before navigation/unload to reduce accidental interruption.
- Metadata view endpoint:
  - `GET /api/v1/admin/tracks/{track_id}/metadata`
- Optional dependency install:
  - `python3 -m pip install librosa`
- Ensure `ffmpeg` is installed in PATH for upload-to-publish media readiness.

For startup troubleshooting and request-id debugging commands, see:

- `docs/local-debug-runbook.md`

## Test Commands

Full automated validation:

```bash
make test
```

Core playback and UI regressions:

```bash
npm run test:playback-play-pause
npm run test:view-continuity
npm run test:golden-flow
npm run test:phase2-integration
npm run test:browsers
```

Full local suite:

```bash
npm run test:catalog
npm run test:api-seams
npm run test:queue
npm run test:media-engine
npm run test:playback-play-pause
npm run test:view-continuity
npm run test:golden-flow
npm run test:phase2-integration
npm run test:hls-assets
npm run test:catalog-media
npm run test:browsers
```

## Repo Layout

- `docs/` requirements, plans, and runbooks
- `src/` core app/playback/data logic
- `public/` static app files and generated media outputs
- `tests/` unit and regression tests
- `scripts/` local utility scripts
- `assets/raw-audio/` local source media inputs (ignored in git)
