# Ferric Phase 1 Demo Runbook

## Start Demo

1. From repo root:
   - `npm run dev`
2. Open:
   - `http://localhost:8080/public/index.html`

## Demo Flow

1. In List view, click Play on first track.
2. Switch to Now Playing.
3. Pause, seek with +/-10s, and press Next.
4. Toggle Shuffle and Repeat modes.
5. Switch back to List view and confirm playback state remains consistent.

## Quick Regression Commands

- `npm run test:golden-flow`
- `npm run test:view-continuity`
- `npm run test:playback-play-pause`
- `npm run test:browsers`
