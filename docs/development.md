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

## Run Locally

Preferred:

```bash
make run
```

Manual split (if needed):

```bash
make backend
make frontend
```

For startup troubleshooting and request-id debugging commands, see:

- `docs/local-debug-runbook.md`

## Test Commands

Full automated validation:

```bash
make test
```

Core playback and UI regressions:

```bash
npm run test:playback-play-pause
npm run test:view-continuity
npm run test:golden-flow
npm run test:phase2-integration
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
npm run test:phase2-integration
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
