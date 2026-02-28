# Ferric POC

Ferric is a music playback POC focused on validating core listener UX first, then evolving to a Python backend.

## Goals

1. Prove a compelling web-first listening flow in Phase 1.
2. Preserve that behavior while migrating data/control seams to a backend in Phase 2.

## Current Status

- Phase 1 playback controls and queue behavior are implemented.
- Browser smoke regression currently passes on Chromium, Firefox, and WebKit.
- Phase 2 is intentionally gated behind a Phase 1.5 improvement re-plan.

## Key Docs

- PRD: [`docs/PRD.md`](docs/PRD.md)
- TODO + decision log: [`docs/TODO.md`](docs/TODO.md)
- Demo runbook: [`docs/demo-runbook.md`](docs/demo-runbook.md)
- Constraints + migration notes: [`docs/phase1-constraints-and-phase2-migration.md`](docs/phase1-constraints-and-phase2-migration.md)

## Run Locally

```bash
npm run dev
```

Open: `http://localhost:8080/public/index.html`

## Test Commands

```bash
npm run test:playback-play-pause
npm run test:view-continuity
npm run test:golden-flow
npm run test:browsers
```

## Repo Layout

- `docs/` product and planning docs
- `public/` static app assets + catalog + generated media output (`public/generated/hls/`)
- `assets/raw-audio/` local source audio inputs for media generation (ignored in git)
- `src/` playback, queue, and data abstractions
- `tests/` unit and regression tests
- `scripts/` local build/dev scripts
