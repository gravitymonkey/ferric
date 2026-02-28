# Ferric POC TODO

**Date:** 2026-02-28  
**Source:** [PRD.md](/Users/jason/dev/ferric/PRD.md)

---

## Phase 1: Static Web-First HLS (No Backend)

### Product/UX

- [ ] Define and freeze Phase 1 user journey (browse -> play -> control -> continue listening)
- [ ] Finalize minimal screen set: list view + now playing view
- [ ] Define empty/error/loading states for catalog and playback

### Data + Media

- [ ] Create `public/catalog.json` with at least 10 representative tracks
- [ ] Add HLS sample assets and consistent file naming
- [ ] Validate all catalog track IDs resolve to valid media URLs

### Playback + Queue

- [ ] Implement play/pause
- [ ] Implement seek/scrub
- [ ] Implement +/- 10s skip
- [ ] Implement next/previous
- [ ] Implement shuffle
- [ ] Implement repeat (off/one/all)
- [ ] Keep playback continuous across list/now-playing view transitions

### Architecture

- [ ] Introduce `MediaEngine` abstraction (UI does not call HLS library directly)
- [ ] Separate playback controller/queue logic from UI components
- [ ] Add interface seams for future API-based catalog and stream resolution

### Phase 1 Exit Criteria

- [ ] Demo-ready end-to-end flow in web client
- [ ] No critical playback regressions across major target browsers
- [ ] Document known constraints and migration notes for Phase 2

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

- [ ] Queue logic: next/previous behavior with and without shuffle
- [ ] Repeat modes: off/one/all end-of-track handling
- [ ] Playback state reducer/controller transitions (play, pause, seek, skip)
- [ ] Catalog parser/validator for required fields
- [ ] Phase 2 API handlers:
  - [ ] `GET /health` returns 200 + expected schema
  - [ ] `GET /catalog` returns valid shape
  - [ ] `POST /playback/resolve` returns stream info for valid track
  - [ ] Missing track/session returns expected 404 error schema

### Simple Regression Tests

- [ ] Golden flow: load app -> start track -> pause -> seek -> next track
- [ ] Queue regression: shuffle on/off does not lose current track
- [ ] Repeat regression: repeat one does not advance queue at end
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
