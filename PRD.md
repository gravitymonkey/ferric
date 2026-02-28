# Ferric POC --- Product Requirements Document

**Version:** 0.3  
**Date:** 2026-02-28  
**Status:** Draft (POC Scope)

---

## 1. Executive Summary

Ferric is a Spotify-like consumer music product exploration.

The POC is intentionally split into two complementary phases:

- Phase 1: static, web-first HLS implementation with no backend
- Phase 2: evolve to a Python backend while preserving proven Phase 1 UX and playback patterns

These phases are intended to validate product feasibility quickly first, then validate backend architecture direction second.

---

## 2. Goals

### Primary POC Goal

Validate the feasibility of building compelling consumer-facing listening features and functionality for Ferric.

### Phase 1 Goal (Initial POC)

Prove end-to-end consumer playback UX quickly using static catalog + web-first HLS delivery.

### Phase 2 Goal (Backend Evolution)

Introduce a Python backend that replaces static data paths/API stubs with real service boundaries, without discarding Phase 1 learnings.

---

## 3. Scope by Phase

### Phase 1 In Scope

- Static `catalog.json` content source
- Web-first frontend client
- HLS audio playback (initially locked to simple profile)
- Core consumer controls and queue behavior
- Architecture seams that allow backend insertion later

### Phase 1 Out of Scope

- Backend API/services
- Auth/account system
- Payments/subscriptions
- DRM
- Production-scale analytics/recommendations

### Phase 2 In Scope

- Python backend for catalog and playback metadata delivery
- Migration from static catalog loading to backend endpoints
- Preserve frontend UX flows while changing data/control plane
- Add auth-ready and analytics-ready extension points

---

## 4. Phase 1 Product Requirements (Static, Web-First)

### Core Features

- Load static `catalog.json`
- Display track listing
- Play HLS audio streams
- Support:
  - Play / Pause
  - Scrubbing
  - ±10 second skip
  - Next / Previous
  - Shuffle
  - Repeat (off / one / all)
- Switch between list and now-playing focused views

### Media Profile (Phase 1 Default)

- Protocol: HLS (VOD)
- Segment duration: 10 seconds
- Audio target bitrate: 128 kbps (AAC)
- Container: MPEG-TS segments

These defaults are for speed and consistency in the initial POC and may evolve in Phase 2+.

---

## 5. Technical Direction

### Frontend

- Phase 1 is web-first by design for speed
- Later clients (React Native, Swift, etc.) remain open options after initial validation

### Playback Architecture

- Keep playback engine and UI separated
- Use a media abstraction layer so implementation details can evolve
- Avoid hard coupling that would block Phase 2 backend integration

### Backend Direction

- No backend in Phase 1
- Python backend introduced in Phase 2 as the planned next step, not a reset

---

## 6. Phase 2 Requirements (Python Backend)

### Backend Responsibilities

- Serve catalog and track metadata via APIs
- Provide playback URL/token orchestration as needed
- Create clean extension points for:
  - Auth
  - Analytics
  - Recommendation inputs

### Migration Expectations

- Frontend core UX from Phase 1 remains intact
- Data loading transitions from static file access to API clients
- Playback behavior parity is maintained during migration

### API Contract Sketch (v1)

Base path: `/api/v1`

#### Conventions

- JSON request/response
- `Content-Type: application/json`
- Use stable string IDs (`track_001`, `session_abc123`)
- Timestamp format: ISO-8601 UTC

#### Endpoints

1. `GET /health`
   - Purpose: service health check for dev and CI
   - `200` response:
     ```json
     {
       "status": "ok",
       "service": "ferric-api",
       "time": "2026-02-28T12:00:00Z"
     }
     ```

2. `GET /catalog`
   - Purpose: fetch catalog metadata used in Phase 1 static `catalog.json`
   - Query params (optional): `limit`, `offset`, `q`
   - `200` response:
     ```json
     {
       "schema_version": "1.0",
       "app": { "title": "Ferric POC" },
       "tracks": [
         {
           "id": "track_001",
           "title": "Scars",
           "artist": "Example Artist",
           "artwork": { "square_512": "/images/track_001_512.jpg" },
           "duration_sec": 214
         }
       ],
       "page": { "limit": 50, "offset": 0, "total": 1 }
     }
     ```

3. `GET /tracks/{track_id}`
   - Purpose: fetch one track metadata object
   - `200` response:
     ```json
     {
       "id": "track_001",
       "title": "Scars",
       "artist": "Example Artist",
       "duration_sec": 214,
       "artwork": { "square_512": "/images/track_001_512.jpg" }
     }
     ```
   - `404` when track does not exist

4. `POST /playback/resolve`
   - Purpose: map `track_id` to playable stream info (URL/token model can evolve later)
   - Request body:
     ```json
     {
       "track_id": "track_001",
       "client": {
         "platform": "web",
         "app_version": "0.1.0"
       }
     }
     ```
   - `200` response:
     ```json
     {
       "track_id": "track_001",
       "stream": {
         "protocol": "hls",
         "url": "/hls/track_001/playlist.m3u8",
         "expires_at": "2026-02-28T12:30:00Z",
         "requires_auth": false
       }
     }
     ```

5. `POST /sessions`
   - Purpose: create playback session for queue/state continuity
   - Request body:
     ```json
     {
       "queue_track_ids": ["track_001", "track_002"],
       "current_track_id": "track_001",
       "position_sec": 0,
       "shuffle": false,
       "repeat_mode": "off"
     }
     ```
   - `201` response:
     ```json
     {
       "session_id": "session_abc123",
       "created_at": "2026-02-28T12:00:00Z"
     }
     ```

6. `PATCH /sessions/{session_id}`
   - Purpose: update playback session state
   - Request body (partial):
     ```json
     {
       "current_track_id": "track_002",
       "position_sec": 11,
       "shuffle": true,
       "repeat_mode": "all"
     }
     ```
   - `200` response:
     ```json
     {
       "session_id": "session_abc123",
       "updated_at": "2026-02-28T12:05:00Z"
     }
     ```

7. `GET /sessions/{session_id}`
   - Purpose: restore queue/session state on reload
   - `200` response:
     ```json
     {
       "session_id": "session_abc123",
       "queue_track_ids": ["track_001", "track_002"],
       "current_track_id": "track_002",
       "position_sec": 11,
       "shuffle": true,
       "repeat_mode": "all"
     }
     ```

#### Error Schema

All non-2xx responses should use:

```json
{
  "error": {
    "code": "TRACK_NOT_FOUND",
    "message": "Track does not exist",
    "request_id": "req_123"
  }
}
```

Initial error codes:

- `BAD_REQUEST`
- `TRACK_NOT_FOUND`
- `SESSION_NOT_FOUND`
- `INTERNAL_ERROR`

---

## 7. Milestones

### Phase 1: Static POC

- Static catalog renders
- HLS playback works end-to-end in web client
- Core controls and queue logic work reliably
- Consumer-facing flow is demo-ready

### Phase 2: Python-Backed POC

- Python backend scaffold and endpoints operational
- Frontend reads from backend instead of static catalog
- Playback flow remains stable after integration
- Key Phase 1 capabilities retained

---

## 8. Definition of Done

POC is successful when:

1. Phase 1 proves consumer listening UX feasibility with static web-first HLS implementation
2. Phase 2 proves the same experience can be supported by a Python backend directionally aligned with future product growth
3. Team documents feasibility findings, risks, and recommended next implementation path

---

## 9. Risks and Open Decisions

- Over-engineering Phase 1 before validating user-facing value
- Under-defining Phase 2 API boundaries, causing migration churn
- Choosing later client platforms too early without Phase 1 evidence

Open decisions after Phase 1:

- Priority order for additional clients (web refinement vs React Native vs Swift)
- First auth strategy for backend-backed playback

---

END OF DOCUMENT
