# Phase 1 User Journey (Frozen)

**Version:** 1.0  
**Date Frozen:** 2026-02-28  
**Status:** Frozen for Phase 1 POC

## Journey Scope

This journey is locked for Phase 1 and maps directly to the PRD sequence:

`browse -> play -> control -> continue listening`

## Canonical Flow

1. Browse catalog
   - User lands on the list view and sees available tracks from static `catalog.json`.
   - Track rows show minimum metadata: title, artist, duration, and artwork thumbnail.
2. Start playback
   - User taps/clicks a track in the list.
   - Playback begins for selected track.
   - Now-playing state becomes visible in list and now-playing view.
3. Control playback
   - User can perform: play/pause, seek/scrub, skip -10s, skip +10s, next, previous, shuffle toggle, repeat mode cycle (off/one/all).
4. Continue listening
   - User can switch between list and now-playing views without playback interruption.
   - Queue position and playback state are preserved during view transitions.
   - End-of-track behavior follows active shuffle/repeat rules.

## Freeze Rules

1. Do not add new user-facing journey states in Phase 1 unless explicitly approved and logged in `TODO.md`.
2. Do not remove any canonical control from the flow.
3. Any behavior change must include:
   - rationale,
   - impacted step(s),
   - regression test update.
