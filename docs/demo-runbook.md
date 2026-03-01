# Ferric Demo Runbook

## Start Demo

1. From repo root:
   - `make run`
2. Open:
   - `http://localhost:8080/public/index.html`

## Demo Flow

1. In List view, click the first track row (not the play icon) to open its individual track view.
2. Press Play from the individual view and confirm playback starts.
3. Use the scrubber timeline (click or drag) to seek within the track.
4. Press Next and verify the individual view updates to the next playing track.
5. Return to List view and use Shuffle/Repeat controls in the Tracks header.
6. While a different track is selected in individual view, verify the mini now-playing chip appears and can jump to the active playing track.

## Quick Regression Commands

- `npm run test:golden-flow`
- `npm run test:view-continuity`
- `npm run test:playback-play-pause`
- `npm run test:phase2-integration`
- `npm run test:browsers`
