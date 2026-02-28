# Development Guide

## Build Media Assets

Generate HLS assets from local source audio:

```bash
npm run build:hls
```

Defaults:

- Source audio: `assets/raw-audio/`
- Generated output: `public/generated/hls/`
- Catalog source of track IDs: `public/catalog.json`

## Test Commands

Core playback and UI regressions:

```bash
npm run test:playback-play-pause
npm run test:view-continuity
npm run test:golden-flow
npm run test:browsers
```

Full local suite:

```bash
npm run test:catalog
npm run test:api-seams
npm run test:queue
npm run test:media-engine
npm run test:playback-play-pause
npm run test:view-continuity
npm run test:golden-flow
npm run test:hls-assets
npm run test:catalog-media
npm run test:browsers
```

## Repo Layout

- `docs/` requirements, plans, and runbooks
- `src/` core app/playback/data logic
- `public/` static app files and generated media outputs
- `tests/` unit and regression tests
- `scripts/` local utility scripts
- `assets/raw-audio/` local source media inputs (ignored in git)
