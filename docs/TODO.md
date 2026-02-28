# Ferric POC TODO

**Date:** 2026-02-28  
**Source:** [PRD.md](PRD.md)

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

- [ ] Improve playback error handling and retry UX in live UI
- [ ] Improve explicit loading/error/empty state rendering implementation parity with specs
- [ ] Add deterministic timing/mocking strategy for browser smoke and UI flow tests
- [ ] Add optional local persistence for shuffle/repeat/current-track resume

### Re-Plan Gate

- [ ] Review and approve Phase 1.5 plan before starting Phase 2 backend tasks

---

## Phase 2: Python Backend Evolution

### Backend Foundation

- [ ] Scaffold Python service project
- [ ] Add `/api/v1/health`
- [ ] Add `/api/v1/catalog`
- [ ] Add `/api/v1/tracks/{track_id}`
- [ ] Add `/api/v1/playback/resolve`
- [ ] Add session endpoints: create/update/read

### Contract + Integration

- [ ] Implement response and error schemas from PRD API sketch
- [ ] Replace frontend static catalog load with API client
- [ ] Replace direct media URL assumptions with `playback/resolve` call
- [ ] Preserve Phase 1 UX and control behavior after backend integration

### Observability + Reliability (POC level)

- [ ] Add request logging with request IDs
- [ ] Add basic API validation and clear 4xx errors
- [ ] Add minimal runbook notes for local startup/debug

### Phase 2 Exit Criteria

- [ ] Frontend fully functional against Python backend
- [ ] Phase 1 behavior parity verified
- [ ] Integration demo proves direction for post-POC build

---

## Test Plan (Simple Unit + Regression)

Keep tests intentionally lightweight and fast.

### Unit Tests

- [x] Queue logic: next/previous behavior with and without shuffle
- [x] Repeat modes: off/one/all end-of-track handling
- [x] Playback state reducer/controller transitions (play, pause, seek, skip)
- [x] Catalog parser/validator for required fields
- [ ] Phase 2 API handlers:
  - [ ] `GET /health` returns 200 + expected schema
  - [ ] `GET /catalog` returns valid shape
  - [ ] `POST /playback/resolve` returns stream info for valid track
  - [ ] Missing track/session returns expected 404 error schema

### Simple Regression Tests

- [x] Golden flow: load app -> start track -> pause -> seek -> next track
- [x] Queue regression: shuffle on/off does not lose current track
- [x] Repeat regression: repeat one does not advance queue at end
- [ ] Phase 2 integration regression: same golden flow passes against backend APIs

### Manual Smoke Checklist (per release candidate)

- [ ] Catalog renders without console/runtime errors
- [ ] First track plays within expected startup time on local/dev
- [ ] Controls update UI state correctly
- [ ] Reload/resume behavior matches current phase expectations
- [ ] No blocker bug in end-to-end listening flow

---

## Nice-to-Have (After Core Stability)

- [ ] Media Session API support
- [ ] Persist session preferences locally (shuffle/repeat)
- [ ] Basic analytics event stubs for play/pause/skip
- [ ] Initial auth hook plumbing for future protected streams

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
