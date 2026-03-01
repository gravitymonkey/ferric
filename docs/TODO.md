# Ferric POC TODO

**Date:** 2026-03-01  
**Source:** [PRD.md](./PRD.md)

---

## Phase 1: Static Web-First HLS (No Backend)

### Product/UX

- [x] Define and freeze Phase 1 user journey (browse -> play -> control -> continue listening)
- [x] Finalize minimal screen set: list view + now playing view
- [x] Define empty/error/loading states for catalog and playback

### Data + Media

- [x] Create `public/catalog.json` with at least 10 representative tracks
- [x] Add HLS sample assets and consistent file naming
- [x] Validate all catalog track IDs resolve to valid media URLs

### Playback + Queue

- [x] Implement play/pause
- [x] Implement seek/scrub
- [x] Implement +/- 10s skip
- [x] Implement next/previous
- [x] Implement shuffle
- [x] Implement repeat (off/one/all)
- [x] Keep playback continuous across list/now-playing view transitions

### Architecture

- [x] Introduce `MediaEngine` abstraction (UI does not call HLS library directly)
- [x] Separate playback controller/queue logic from UI components
- [x] Add interface seams for future API-based catalog and stream resolution

### Phase 1 Exit Criteria

- [x] Demo-ready end-to-end flow in web client
- [x] No critical playback regressions across major target browsers
- [x] Document known constraints and migration notes for Phase 2

---

## Phase 1.5: Improvement Re-Plan (Before Phase 2)

### Priority Improvement Tracks

- [x] Replace app title text with Ferric logo header (`docs/ferric_invert.png`, 250px width)
- [x] Introduce Tailwind-based UI styling and stateful navigation buttons (List/Now Playing)
- [x] Re-plan executed via iterative UI delivery during Phase 1.5/2/3 development

---

## Phase 2: Python Backend Evolution

### Backend Foundation

- [x] Scaffold Python service project
- [x] Add `/api/v1/health`
- [x] Add `/api/v1/catalog`
- [x] Add `/api/v1/tracks/{track_id}`
- [x] Add `/api/v1/playback/resolve`
- [x] Add session endpoints: create/update/read

### Contract + Integration

- [x] Implement response and error schemas from PRD API sketch
- [x] Replace frontend static catalog load with API client
- [x] Replace direct media URL assumptions with `playback/resolve` call
- [x] Preserve Phase 1 UX and control behavior after backend integration

### Observability + Reliability (POC level)

- [x] Add request logging with request IDs
- [x] Add basic API validation and clear 4xx errors
- [x] Add minimal runbook notes for local startup/debug

### Phase 2 Exit Criteria

- [x] Frontend fully functional against Python backend
- [x] Phase 1 behavior parity verified
- [x] Integration demo proves direction for post-POC build

---

## Test Plan (Simple Unit + Regression)

Keep tests intentionally lightweight and fast.

### Unit Tests

- [x] Queue logic: next/previous behavior with and without shuffle
- [x] Repeat modes: off/one/all end-of-track handling
- [x] Playback state reducer/controller transitions (play, pause, seek, skip)
- [x] Catalog parser/validator for required fields
- [x] Phase 2 API handlers:
  - [x] `GET /health` returns 200 + expected schema
  - [x] `GET /catalog` returns valid shape
  - [x] `GET /tracks/{track_id}` returns 200 + expected schema
  - [x] `POST /playback/resolve` returns stream info for valid track
  - [x] Session create/update/read endpoints return expected schema
  - [x] Missing track returns expected 404 error schema
  - [x] Missing session returns expected 404 error schema

### Simple Regression Tests

- [x] Golden flow: load app -> start track -> pause -> seek -> next track
- [x] Queue regression: shuffle on/off does not lose current track
- [x] Repeat regression: repeat one does not advance queue at end
- [x] Phase 2 integration regression: same golden flow passes against backend APIs

### Manual Smoke Checklist (per release candidate, recurring)

- Catalog renders without console/runtime errors
- First track plays within expected startup time on local/dev
- Controls update UI state correctly
- Reload/resume behavior matches current phase expectations
- No blocker bug in end-to-end listening flow

---

## Deferred Backlog (Post-POC / Future Phase)

- Improve playback error handling and retry UX in live UI
- Improve explicit loading/error/empty state rendering implementation parity with specs
- Add deterministic timing/mocking strategy for browser smoke and UI flow tests
- Add optional local persistence for shuffle/repeat/current-track resume
- Media Session API support
- Persist session preferences locally (shuffle/repeat)
- Harden auth plumbing for protected streams beyond HTTP Basic

---

## Phase 3 Direction (Draft)

- [x] Publish detailed Phase 3 plan (`docs/phase3-plan.md`)
- [x] Milestone 1: Persistence foundation (SQLAlchemy repos + Alembic + DB-backed sessions)
- [x] Milestone 2: Catalog migration to DB-backed public API
- [x] Milestone 3: Admin API + lightweight auth (HTTP Basic)
- [x] Milestone 4: Admin UI + upload flow + publish path
- [x] Phase 3 extension: listener analytics capture (user cookie + event ingest + stats endpoints)
- [x] Phase 3 extension: upload-time audio feature extraction to `track_metadata` (librosa-based)

---

## Decision Log (Realtime Spec Changes)

- 2026-02-28: Froze Phase 1 user journey in `docs/phase1-user-journey.md` as v1.0.
- 2026-02-28: Removed doc-only regression guard; testing scope is now code-focused (unit/integration/regression on executable behavior).
- 2026-02-28: Froze minimal Phase 1 screen set in `docs/phase1-screen-set.md` as exactly two primary views (List, Now Playing).
- 2026-02-28: Froze catalog/playback loading-empty-error behavior in `docs/phase1-states.md` for consistent Phase 1 UX handling.
- 2026-02-28: Added `public/catalog.json` with 10 representative tracks and normalized HLS URL pattern `/generated/hls/{track_id}/playlist.m3u8`.
- 2026-02-28: Added HLS build pipeline (`scripts/build_hls_from_mp3s.sh`) using 10s HLS VOD, AAC 128 kbps, MPEG-TS segments, naming `public/generated/hls/{track_id}/playlist.m3u8` + `seg_XXX.ts`.
- 2026-02-28: Added stream resolution regression test (`tests/catalog-media-resolution.test.mjs`) to assert every catalog stream URL resolves to an existing HLS playlist + segment set.
- 2026-02-28: Implemented `PlaybackController` play/pause core logic (`src/playback/playback-controller.mjs`) with unit coverage in `tests/playback-controller-play-pause.test.mjs`.
- 2026-02-28: Extended `PlaybackController` with `seek(positionSec)` scrub behavior (active-track guard + non-negative validation + integer normalization) and unit tests.
- 2026-02-28: Added `skipForward10` / `skipBack10` controls to `PlaybackController` with zero-clamp behavior and unit coverage.
- 2026-02-28: Added queue-backed `next` / `previous` navigation via `setQueue` + `playAt` in `PlaybackController`, including boundary behavior tests.
- 2026-02-28: Added shuffle support to `PlaybackController` with reversible base-order queue, current-track preservation on toggle, and deterministic unit coverage.
- 2026-02-28: Added repeat modes (`off`/`one`/`all`) and `handleTrackEnded()` behavior in `PlaybackController`; validated repeat-one no-advance and end-of-queue semantics with unit tests.
- 2026-02-28: Added runnable web UI (`public/index.html`, `public/app.mjs`) with List + Now Playing bound to one `PlaybackController` instance, plus view continuity test (`tests/view-transition-continuity.test.mjs`).
- 2026-02-28: Extracted explicit `MediaEngine` abstraction (`src/playback/media-engine.mjs`), enforced contract checks in `PlaybackController`, and removed direct `Audio` access from UI code.
- 2026-02-28: Extracted `QueueManager` (`src/playback/queue-manager.mjs`) and moved queue/shuffle ordering logic out of UI and controller internals; UI now updates playback position via controller API (`updatePlaybackPosition`) instead of mutating state directly.
- 2026-02-28: Added API-ready seams for catalog and stream resolution (`src/data/catalog-source.mjs`, `src/playback/stream-resolver.mjs`) and wired app/controller through static implementations with seam tests (`tests/api-seams.test.mjs`).
- 2026-02-28: Added runnable demo server (`npm run dev` via `scripts/dev-server.mjs`), demo runbook (`docs/demo-runbook.md`), and automated golden-flow regression (`tests/golden-flow-regression.test.mjs`).
- 2026-02-28: Added automated cross-browser smoke test (`tests/browser-smoke.py`) covering Chromium/Firefox/WebKit and validated pass locally with HLS-to-MP3 fallback for non-native-HLS browsers.
- 2026-02-28: Documented end-of-Phase-1 constraints and Phase 2 migration notes in `docs/phase1-constraints-and-phase2-migration.md`; added explicit Phase 1.5 re-plan section in TODO to gate Phase 2 start.
- 2026-02-28: Reorganized media paths: raw audio moved to `assets/raw-audio/` and generated HLS output moved to `public/generated/hls/`; updated catalog URLs, build script defaults, tests, and ignore rules accordingly.
- 2026-02-28: Updated web UI presentation for Phase 1.5: replaced text title with Ferric logo (`docs/ferric_invert.png`, width 250), migrated styling to Tailwind CDN utilities, and improved nav/control button state visuals.
- 2026-02-28: Replaced top nav labels with Heroicons (`list-bullet`, `musical-note`) and replaced in-body Play text buttons with Heroicon play glyphs; updated browser smoke assertions to use play/pause state attributes.
- 2026-02-28: Updated list interaction UX: clicking a list play button now opens Now Playing for that track, and the active playing track’s list button switches to a stop icon that pauses playback when clicked.
- 2026-02-28: Scaffolded Phase 2 Python backend service under `backend/` using FastAPI app factory (`backend/app/main.py`) with initial boot test coverage (`backend/tests/test_scaffold.py`).
- 2026-02-28: Added `/api/v1/health` endpoint with PRD-aligned schema (`status`, `service`, `time`) and test coverage in `backend/tests/test_scaffold.py`.
- 2026-02-28: Added `/api/v1/catalog` endpoint with `limit`/`offset`/`q` support and PRD-aligned response shape (`schema_version`, `app`, `tracks`, `page`), backed by `public/catalog.json`.
- 2026-02-28: Added `/api/v1/tracks/{track_id}` endpoint with PRD-aligned track metadata response and 404 error schema (`TRACK_NOT_FOUND`, `request_id`) plus unit tests for found/missing track cases.
- 2026-02-28: Added `/api/v1/playback/resolve` endpoint to resolve `track_id` -> stream metadata (`protocol`, `url`, `expires_at`, `requires_auth`) with 404 `TRACK_NOT_FOUND` behavior and unit tests for success/missing track.
- 2026-02-28: Added in-memory session API endpoints (`POST /sessions`, `PATCH /sessions/{session_id}`, `GET /sessions/{session_id}`) with PRD-aligned payload fields and `SESSION_NOT_FOUND` 404 schema coverage.
- 2026-02-28: Added typed API schema models in `backend/app/schemas.py`, bound FastAPI request/response models for existing Phase 2 routes, and standardized invalid input handling to PRD-style `BAD_REQUEST` 4xx payloads.
- 2026-02-28: Switched frontend catalog loading from static file source to `GET /api/v1/catalog` via `ApiCatalogSource`, and added dev-server `/api/*` proxy support (`BACKEND_ORIGIN`, default `http://127.0.0.1:8000`) to keep local UI flow runnable.
- 2026-02-28: Switched frontend playback stream resolution to `POST /api/v1/playback/resolve` via `ApiStreamResolver`, and removed controller/queue hard-requirements for `track.stream.url` so API catalog track shapes can remain metadata-only.
- 2026-02-28: Database direction decision for Phase 2: keep current file + in-memory approach for immediate POC progress; plan SQLite as the first persistence layer for sessions in a follow-up step.
- 2026-02-28: Restored cross-browser playback parity after API integration by adding `fallback_url` to `/api/v1/playback/resolve` responses and browser-side stream URL normalization for static dev serving paths.
- 2026-02-28: Added backend-integrated regression coverage (`tests/phase2-backend-golden-flow.test.mjs`) and updated browser smoke harness to run against FastAPI + dev proxy on dynamic localhost ports.
- 2026-02-28: Added backend request logging middleware with per-request IDs (`x-request-id` header generation/propagation), structured request logs, and request-id propagation into PRD-style error payloads.
- 2026-02-28: Added `docs/local-debug-runbook.md` with concrete startup, health/proxy checks, request-id debug commands, and common local failure triage; linked from root/dev/backend docs.
- 2026-02-28: Phase 2 closeout verification passed across backend unit tests, frontend unit/regression suites, backend-integrated golden flow, and cross-browser smoke (Chromium/Firefox/WebKit), enabling Phase 2 exit criteria completion.
- 2026-02-28: Added Python-based frontend dev server (`scripts/dev_server.py`) and a root `Makefile` (`make run`, `make backend`, `make frontend`, `make test`, `make smoke`) so local orchestration can run through Python services + scripted targets.
- 2026-02-28: Published detailed Phase 3 implementation plan in `docs/phase3-plan.md`, including SQLite/Postgres adapter strategy, Alembic migration policy, admin/upload scope, and lightweight HTTP Basic auth approach.
- 2026-02-28: Completed Phase 3 Milestone 1 persistence foundation: added SQLAlchemy session model + repository layer, Alembic migration scaffold and initial `playback_sessions` migration, migrated session API endpoints from in-memory to DB-backed storage, and added migration upgrade/downgrade smoke tests.
- 2026-02-28: Completed Phase 3 Milestone 2 catalog migration: added DB catalog tables (`tracks`, `track_artwork`, `track_streams`) + Alembic migration, moved `/catalog`, `/tracks/{id}`, and `/playback/resolve` reads to SQLAlchemy repositories, and added explicit DB seeding command (`make db-seed`) from `public/catalog.json`.
- 2026-02-28: Completed Phase 3 Milestones 3 and 4: added HTTP Basic-protected admin API (`/api/v1/admin/*`) for track CRUD/upload/publish, plus responsive Tailwind admin UI at `/admin` with mobile-friendly forms and list management.
- 2026-02-28: Added listener analytics extension: frontend generates persistent `ferric_user_id` cookie on listening interaction, emits playback action events to `/api/v1/events/listen`, and backend stores/query-aggregates events for per-track and per-user admin stats.
- 2026-02-28: Added upload-time audio metadata extraction foundation: new `track_metadata` table + migration, `librosa`-driven feature extraction service with graceful fallback when library is unavailable, and metadata upsert/read path exposed via admin endpoint (`/api/v1/admin/tracks/{track_id}/metadata`).
- 2026-03-01: Synced PRD (`v0.6`) to current implemented backend/API/product baseline (DB-backed persistence, admin API/UI, listener events/stats, and upload-time metadata extraction) so PRD and TODO are aligned with the codebase state.
- 2026-03-01: Phase 3.1 admin UI design pass: applied the same slate gradient as the player (`from-slate-700 via-slate-900 to-slate-950`), replaced the "Ferric Admin" + subhead header with compact logo + single "Admin" label, and reduced logo display size by ~50% from the player header treatment.
- 2026-03-01: Fixed admin logo asset serving by moving header logo reference to `/images/ferric_invert.png`, copying `docs/ferric_invert.png` into `public/images/`, and mounting `/images` static files in FastAPI so `/admin` resolves logo assets directly.
- 2026-03-01: Restructured admin UI into tabbed multi-view navigation with top tabs for `Stats`, `Listings`, and `Create New`; split prior single-page layout into section-based views while preserving existing admin CRUD/upload/publish actions and stats rendering.
- 2026-03-01: Refined admin section navigation: removed manual refresh button, changed desktop nav to true tab styling (underline/active state), and added mobile hamburger-style section menu that toggles `Stats`, `Listings`, and `Create New` views on narrow widths.
- 2026-03-01: Updated mobile admin header behavior by hiding the Ferric logo + `Admin` title on small screens and renaming the hamburger trigger label from `Sections` to `Ferric Admin`.
- 2026-03-01: Added hot-reload dev make targets (`make backend-hot`, `make run-hot`) so backend-served admin UI changes auto-reload during development while preserving the existing player dev server flow.
- 2026-03-01: Redesigned `Listings` tab from card layout to a paginated sheet/table view with inline editable columns (`id`, `title`, `artist`, `duration`, `status`, `plays`) plus per-row actions (`save`, `publish`, audio/artwork upload); added client-side pagination controls and page reset behavior on filter changes.
- 2026-03-01: Updated listings table behavior for next edit-flow phase: page size increased to 25, listing columns switched to read-only display for title/artist/duration/status, and row actions reduced to a single Heroicon `pencil-square` `Edit` action that navigates into a new per-track edit view scaffold.
- 2026-03-01: Added clickable per-column sorting in listings table (`id`, `title`, `artist`, `duration`, `status`, `plays`) with asc/desc toggle on repeat clicks and client-side ordering applied to the currently filtered result set (search + status).
- 2026-03-01: Styled `Back to Listings` in the edit view with the cyan highlight treatment for consistency with active/action controls.
- 2026-03-01: Switched admin track creation to UUID-first IDs by making `id` optional in create payloads and generating `uuid4` server-side when omitted; kept explicit ID support for compatibility, removed manual ID entry from admin Create form, and added regression coverage for UUID generation.
- 2026-03-01: Added explicit listing state snapshot/restore between `Edit` and `Back to Listings` so search/status filters, sort direction/key, page index, and current row set are preserved when returning from the per-track edit view.
- 2026-03-01: Upgraded the per-track edit page to an editorial workflow: editable `title/artist/duration/status` form backed by `PATCH /api/v1/admin/tracks/{id}`, media upload controls for audio/artwork backed by existing upload endpoints, and a read-only librosa metadata panel sourced from `GET /api/v1/admin/tracks/{id}/metadata`.
- 2026-03-01: Improved edit-page media/metadata UX: show Heroicon `photo` placeholder when artwork is absent (no broken image state), rename metadata section title to `Track Metadata`, and always render a consistent field/value metadata table structure even when no metadata row exists.
- 2026-03-01: Added direct Stats -> Edit navigation: Top 10 rows are now clickable and open the per-track editor, backed by new admin endpoint `GET /api/v1/admin/tracks/{track_id}` for reliable detail loading even when the track is outside the current listing subset.
- 2026-03-01: Added centered admin footer navigation with `Github` and `Tail Logs` links, and introduced a new `/admin/logs` page in matching admin visual style as the initial shell for tail-log viewing.
- 2026-03-01: Updated admin footers (home + logs) to use Silkscreen at fixed `8px` and converted them to floating fixed-bottom components with safe bottom content padding to avoid overlap.
- 2026-03-01: Made admin header branding (Ferric logo + `Admin` text) a low-key clickable home target to `/admin` on admin pages without visual link styling changes.
- 2026-03-01: Implemented safe file-backed log access for admin: added allowlisted `GET /api/v1/admin/logs` (no shell execution), wired `/admin/logs` with source selector + line count + refresh, enabled backend/frontend log file emission (`backend/logs/*.log`) in dev targets, and added `.env.example` + docs for log/env configuration.
- 2026-03-01: Expanded logs test coverage with backend allowlist tail behavior, frontend source tail behavior, and missing-file empty-return behavior; reorganized TODO to mark core POC scope complete and move unfinished non-core items into explicit deferred backlog.
- 2026-03-01: Clarified edit-page upload semantics and feedback: audio/artwork uploads now show immediate per-control status text on selection/upload result, and successful audio metadata extraction now updates track `duration_sec` automatically from extracted duration.
- 2026-03-01: Hardened publish readiness path: admin audio upload now attempts immediate HLS generation (`ffmpeg`) and publish/status->published is rejected unless both playlist and fallback media files exist; added regression coverage for publish-readiness validation.
- 2026-03-01: Updated create-track workflow to avoid manual duration entry: `duration_sec` is now optional with default `0` at create time, create UI removed duration input, and duration is expected to be inferred from uploaded audio metadata.
- 2026-03-01: Added duration fallback when librosa extraction is unavailable: admin audio upload now probes duration with `ffprobe` and updates track `duration_sec` even if full feature extraction is skipped.
- 2026-03-01: Added explicit backend dependency management (`backend/requirements.txt`) and wired startup-oriented make targets to install dependencies via new `make deps` target before backend launch.
- 2026-03-01: Improved upload and media UX: added visible spinners for admin audio/artwork upload processing states, and fixed player artwork URL normalization so admin-uploaded `/images/managed/*` assets render correctly in player list and now-playing views.
- 2026-03-01: Added player artwork lightbox behavior in now-playing view: clicking available album artwork opens a dimmed fullscreen overlay with responsive max-size image, and clicking the enlarged image closes the overlay.
- 2026-03-01: Exposed `updated_at` on admin track payloads and surfaced it in Listings as a sortable `Updated` column so recent edits/uploads/publish operations are visible and sortable by recency.
- 2026-03-01: Added `uploaded_at` tracking on tracks with first-publish semantics (set once on first successful transition to `published`, immutable on later publish cycles), exposed it via admin track payloads, and added sortable `Uploaded` column in admin Listings.
- 2026-03-01: Added a temporary admin upload navigation guard hack: while audio/artwork upload is in-flight, link navigation and browser unload actions prompt `"Are you sure? You will cancel your upload and processing."` to reduce accidental interruption risk pending async ingest job support.
- 2026-03-01: Simplified admin Listings density by removing `ID` and `Duration` columns; table now emphasizes editorial and operational fields (`Title`, `Artist`, `Status`, `Uploaded`, `Updated`, `Plays`).
- 2026-03-01: Updated admin Listings timestamp presentation for readability to `MM/DD/YY HH:MM AM/PM` for both `Uploaded` and `Updated`.
- 2026-03-01: Added inline save-state feedback beside `Save Changes` on track edit (`Saving...`, `Saved`, `Save failed`) so commit completion is visible at the action point.
