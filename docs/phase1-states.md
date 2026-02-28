# Phase 1 Loading, Empty, and Error States (Frozen)

**Version:** 1.0  
**Date Frozen:** 2026-02-28  
**Status:** Frozen for Phase 1 POC

## Scope

State definitions for:
- catalog loading and render
- playback startup and runtime control

## Catalog States

1. Loading
   - Trigger: initial `catalog.json` fetch in progress.
   - UI: skeleton rows (or loading placeholder list) in List View.
   - Controls: track interaction disabled until catalog is ready.
2. Empty
   - Trigger: catalog fetch succeeds but returns zero tracks.
   - UI: explicit empty message and retry action.
   - Controls: playback controls disabled due to no playable items.
3. Error
   - Trigger: catalog fetch fails or parse/validation fails.
   - UI: non-blocking error panel with retry action.
   - Controls: playback entry disabled until successful reload.

## Playback States

1. Loading
   - Trigger: user starts track and media is buffering/initializing.
   - UI: loading indicator on active track and in Now Playing.
   - Controls: pause enabled if stream has started; seek/skip disabled until ready.
2. Empty (No Active Track)
   - Trigger: app has catalog but no selected track yet.
   - UI: Now Playing placeholder with guidance to select a track.
   - Controls: transport disabled except actions that select/start a track.
3. Error
   - Trigger: stream resolve/load/playback failure.
   - UI: playback error notice with retry current track and return-to-list option.
   - Controls: replay/retry enabled; seek disabled while errored.

## Retry Rules

1. Catalog retry must re-run fetch + validation.
2. Playback retry must preserve queue context and retry current track first.
3. Errors must not clear shuffle/repeat preference state.

## Freeze Rules

1. New state classes are out-of-scope unless logged in `TODO.md`.
2. Any state behavior change requires matching updates to implementation tests once code is added.
