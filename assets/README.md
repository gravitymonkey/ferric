# Assets

This directory is for local source media inputs used to generate playable assets for the Ferric POC.

## Folder Layout

- `assets/raw-audio/` local source audio files (`.mp3`)

`assets/raw-audio/` is ignored by git and should not be committed.

## Generate Playback Assets

From repo root:

```bash
npm run build:hls
```

This command:

1. Reads `public/catalog.json` track IDs.
2. Maps sorted files from `assets/raw-audio/*.mp3` to those track IDs.
3. Generates HLS output to `public/generated/hls/{track_id}/playlist.m3u8` + `seg_XXX.ts`.

## Requirements

- `ffmpeg` installed and available in `PATH`
- `jq` installed and available in `PATH`

## Notes

- If there are fewer MP3 files than catalog tracks, the build fails.
- After changing source audio files, rerun `npm run build:hls` before playback tests or demo runs.
