#!/usr/bin/env bash
set -euo pipefail

CATALOG_PATH="${1:-public/catalog.json}"
MP3_DIR="${2:-assets/raw-audio}"
HLS_ROOT="${3:-public/generated/hls}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg is required but not found in PATH" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required but not found in PATH" >&2
  exit 1
fi

test -f "$CATALOG_PATH"
test -d "$MP3_DIR"
mkdir -p "$HLS_ROOT"

TRACK_IDS=()
while IFS= read -r line; do
  TRACK_IDS+=("$line")
done < <(jq -r '.tracks[].id' "$CATALOG_PATH")

MP3_FILES=()
while IFS= read -r line; do
  MP3_FILES+=("$line")
done < <(find "$MP3_DIR" -maxdepth 1 -type f -name '*.mp3' | sort)

if [ "${#MP3_FILES[@]}" -lt "${#TRACK_IDS[@]}" ]; then
  echo "ERROR: Need at least ${#TRACK_IDS[@]} mp3 files, found ${#MP3_FILES[@]}" >&2
  exit 1
fi

for i in "${!TRACK_IDS[@]}"; do
  track_id="${TRACK_IDS[$i]}"
  input_mp3="${MP3_FILES[$i]}"
  out_dir="$HLS_ROOT/$track_id"

  rm -rf "$out_dir"
  mkdir -p "$out_dir"

  ffmpeg -y -hide_banner -loglevel error \
    -i "$input_mp3" \
    -c:a aac \
    -b:a 128k \
    -f hls \
    -hls_time 10 \
    -hls_playlist_type vod \
    -hls_segment_type mpegts \
    -hls_segment_filename "$out_dir/seg_%03d.ts" \
    "$out_dir/playlist.m3u8"

  echo "Built HLS for $track_id from $(basename "$input_mp3")"
done

echo "PASS: generated ${#TRACK_IDS[@]} HLS track directories under $HLS_ROOT"
