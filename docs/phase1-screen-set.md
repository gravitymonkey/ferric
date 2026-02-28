# Phase 1 Minimal Screen Set (Frozen)

**Version:** 1.0  
**Date Frozen:** 2026-02-28  
**Status:** Frozen for Phase 1 POC

## Screen Inventory

Phase 1 includes exactly two primary screens:

1. List View
2. Now Playing View

No additional primary screens are included in Phase 1 scope.

## 1) List View

Purpose: browsing and selecting tracks from static catalog data.

Required UI regions:
- App header/title
- Track list (scrollable)
- Track row metadata: artwork thumbnail, title, artist, duration
- Active track indicator when playback is in progress
- Persistent mini-player entry point to Now Playing

Required actions:
- Select track to start playback
- Play/pause current track
- Navigate to Now Playing

## 2) Now Playing View

Purpose: focused playback control for the active track and queue progression.

Required UI regions:
- Track hero area: artwork, title, artist
- Timeline/progress + seek interaction
- Transport controls: previous, play/pause, next
- Secondary controls: -10s, +10s, shuffle toggle, repeat cycle (off/one/all)
- Queue context indicator (current position)
- Back navigation to List View

Required actions:
- Full playback control set from PRD
- Navigate back to List View without interrupting playback

## Navigation + State Rules

1. List View and Now Playing share one playback state and one queue state.
2. Navigation between views must not reset track, position, or transport state.
3. If there is no active track, Now Playing shows an empty-state shell with disabled transport actions (except selecting/browsing from List View).

## Freeze Rules

1. Any extra primary screen proposal is out-of-scope for Phase 1 unless logged in `TODO.md` decision log.
2. If a control is moved between views, parity with required actions must remain intact.
