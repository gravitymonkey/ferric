# Phase 3 Plan: DB + Admin + Upload

## Goals

1. Replace file/in-memory source-of-truth with DB-backed persistence.
2. Keep storage adapter-flexible: SQLite for local/dev, Postgres for deployment.
3. Add an admin interface for track metadata management and media upload.
4. Add minimal but real authentication for admin UI/API.

## Architecture Decisions

### DB Adapter Strategy

- Use SQLAlchemy ORM + Core as the persistence boundary.
- Configure engine from `DATABASE_URL`.
  - SQLite local default:
    - `sqlite:///./backend/ferric.db`
  - Postgres example:
    - `postgresql+psycopg://user:pass@host:5432/ferric`
- Keep repository interfaces stable and dialect-agnostic.
- Avoid dialect-specific SQL in app code.

### Migration Strategy

- Use Alembic migrations as the only schema change path.
- Keep one migration tree for both SQLite and Postgres.
- Enforce migration-first development:
  - no implicit `create_all` in runtime startup.
- CI checks:
  - migration upgrade on SQLite
  - migration downgrade smoke on SQLite
  - optional Postgres migration job for compatibility.

### Admin Auth (Lightweight)

- Use HTTP Basic auth for `/admin` and admin API routes.
- Credentials sourced from env:
  - `FERRIC_ADMIN_USER`
  - `FERRIC_ADMIN_PASSWORD`
- Keep this intentionally simple for POC; no full account system.
- Hardening follow-up: migrate to hashed password verification before non-POC deployment.

## Data Model (Initial)

1. `tracks`
   - `id` (string, pk)
   - `title`
   - `artist`
   - `duration_sec`
   - `status` (`draft`, `published`, `archived`)
   - `uploaded_at` (nullable timestamp; set once on first successful publish transition)
   - `created_at`, `updated_at`

2. `track_artwork`
   - `track_id` (fk -> tracks.id, unique)
   - `square_512_path`
   - `created_at`, `updated_at`

3. `track_streams`
   - `track_id` (fk -> tracks.id, unique)
   - `protocol` (`hls`)
   - `playlist_path`
   - `fallback_path`
   - `created_at`, `updated_at`

4. `playback_sessions`
   - `session_id` (string, pk)
   - `queue_track_ids_json`
   - `current_track_id`
   - `position_sec`
   - `shuffle`
   - `repeat_mode`
   - `created_at`, `updated_at`

5. `ingest_jobs` (optional in phase 3b)
   - `job_id` (pk)
   - `track_id`
   - `state` (`queued`, `processing`, `completed`, `failed`)
   - `error_message`
   - `created_at`, `updated_at`

## API Evolution

### Public API (existing routes)

- Keep `/api/v1/catalog`, `/tracks/{id}`, `/playback/resolve` contract stable.
- Back these routes by DB repositories instead of `public/catalog.json`.
- Keep fallback behavior (`fallback_url`) for non-native-HLS browsers.

### Admin API (new, protected by basic auth)

- `POST /api/v1/admin/tracks`
  - Create metadata (`draft` status default).
- `PATCH /api/v1/admin/tracks/{id}`
  - Update metadata/status.
- `POST /api/v1/admin/tracks/{id}/upload/audio`
  - Upload source audio file.
- `POST /api/v1/admin/tracks/{id}/upload/artwork`
  - Upload artwork.
- `POST /api/v1/admin/tracks/{id}/publish`
  - Trigger/mark publish when stream assets are ready.

## Admin UI Scope (Phase 3)

1. Login prompt via HTTP Basic (browser-native dialog).
2. Track list page:
   - status filter
   - sortable/paginated listings
   - single `Edit` action into per-track editorial page
3. Track edit page:
   - editable title, artist, duration, status
   - artwork preview + upload
   - source audio upload
   - publish-ready status management
   - upload processing feedback and inline save status
4. Basic ingest status indicator:
   - queued/processing/completed/failed

## Upload and Media Pipeline

### Phase 3a (Synchronous local)

- Save uploaded files under local managed paths:
  - audio source: `assets/raw-audio/managed/{track_id}/source.<ext>`
  - artwork: `public/images/managed/{track_id}_512.jpg`
- Trigger local HLS generation command for uploaded audio.
- Persist resulting playlist/fallback paths to DB.
- Temporary UX hack (current): while an upload is in flight, admin UI shows a browser confirmation dialog on navigation/close actions:
  - `"Are you sure? You will cancel your upload and processing."`
  - This is a best-effort guard only and will be replaced by explicit async job tracking/state in phase 3b.

### Phase 3b (Async-ready)

- Move ingestion to background worker/job queue.
- Track progress via `ingest_jobs`.

## Implementation Plan

### Milestone 1: Persistence Foundation

1. Add SQLAlchemy models + repository interfaces.
2. Add Alembic setup and initial schema migration.
3. Add DB session wiring via dependency injection.
4. Migrate session endpoints from in-memory to DB-backed.
5. Add migration and repository tests (SQLite).

### Milestone 2: Catalog Migration

1. Add seed command to import existing `public/catalog.json` into DB.
2. Switch public catalog/track/resolve handlers to DB repositories.
3. Keep output schemas identical to Phase 2.
4. Add parity regression tests (old vs new response shape).

### Milestone 3: Admin API + Basic Auth

1. Add basic auth middleware/dependency for admin routes.
2. Add admin CRUD endpoints for tracks and stream/artwork metadata.
3. Add upload endpoints (audio/artwork) with size/type validation.
4. Add audit-style request logs for admin changes.

### Milestone 4: Admin UI

1. Add minimal `/admin` pages (list, edit, upload).
2. Connect forms to admin API.
3. Add UI feedback for upload/ingest states.
4. Add smoke test for create -> upload -> publish -> visible in catalog.

## Testing Plan

1. Unit tests:
   - repository CRUD + filters
   - auth guard behavior
   - upload validators
2. Migration tests:
   - `alembic upgrade head` on SQLite
   - rollback smoke to previous revision
3. Integration tests:
   - catalog/track/resolve with DB seed
   - session persistence across service restart
4. Regression:
   - existing browser smoke flow remains green
   - new admin flow smoke test.

## Risks and Mitigations

1. SQLite vs Postgres behavior drift
   - Mitigation: keep SQLAlchemy abstractions clean; run optional Postgres CI migration/test job.
2. Upload pipeline complexity
   - Mitigation: phase 3a synchronous implementation first, async later.
3. Weak auth posture with HTTP Basic
   - Mitigation: scope to admin only, require strong bcrypt hash, keep behind trusted network for POC.

## Definition of Done (Phase 3)

1. Public API reads from DB, not `catalog.json`.
2. Session state persists across backend restart.
3. Admin can create/edit/publish tracks and upload media.
4. Alembic migrations are the canonical schema lifecycle.
5. Existing listener UX regressions remain green.
