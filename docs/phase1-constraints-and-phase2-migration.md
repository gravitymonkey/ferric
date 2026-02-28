# Phase 1 Constraints and Phase 2 Migration Notes

**Date:** 2026-02-28  
**Status:** Baseline captured at end of Phase 1

## Known Phase 1 Constraints

1. Playback stack is intentionally lightweight
   - Uses browser `Audio` element behavior with no advanced buffering strategy.
   - No adaptive bitrate orchestration logic in app layer.
2. HLS compatibility needs fallback path
   - Native HLS is not uniformly available across browsers.
   - Current mitigation uses MP3 fallback when native HLS load fails.
3. Static data sources
   - Catalog and stream resolution use static implementations by default.
   - No backend-driven pagination/auth/tokenization yet.
4. Limited operational hardening
   - No centralized request logging, structured telemetry, or runtime health diagnostics for frontend flows.
   - Smoke/regression suite exists but is still POC-depth.
5. Session persistence is minimal
   - Shuffle/repeat/position are runtime-only and not persisted across reloads.
6. Selected-track detail vs active playback are distinct states
   - UI allows viewing a selected track that is different from the currently playing track.
   - This distinction must be preserved through backend integration.

## Phase 2 Migration Notes

1. Keep UX and control semantics stable
   - Preserve behavior for play/pause/seek/skip/next/previous/shuffle/repeat.
   - Preserve list <-> now-playing continuity behavior.
2. Swap only data/control-plane seams first
   - Replace `StaticCatalogSource` with `ApiCatalogSource`.
   - Replace `StaticStreamResolver` with `ApiStreamResolver`.
   - Avoid UI redesign during first backend integration pass.
3. Maintain contract compatibility
   - Keep track IDs and schema shape aligned with PRD `/api/v1` sketch.
   - Keep stream-resolution result mappable to `PlaybackController` expectations.
4. Phase 2 parity gates
   - Existing Phase 1 regressions (golden flow, queue, repeat, view continuity, browser smoke) must still pass.
   - Add backend API handler tests before wiring frontend to backend in default path.
5. Preserve selected-track semantics
   - Individual track view behavior is selection-driven; playback state is related but not identical.
   - Backend session/state APIs must support both active playback state and current detail selection context.

## Phase 1.5 Improvement Focus (Pre-Phase-2)

Use this as the immediate planning slate before backend implementation:

1. Reliability hardening in frontend playback error paths
2. Clearer user-visible loading/error state rendering in live UI
3. Deterministic local test harness improvements (stable timing/mocking)
4. Optional persistence for shuffle/repeat/current track in local storage
