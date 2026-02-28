import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";

const catalog = JSON.parse(fs.readFileSync(new URL("../public/catalog.json", import.meta.url), "utf8"));

for (const track of catalog.tracks) {
  const trackDir = path.join(new URL("../public/generated/hls/", import.meta.url).pathname, track.id);
  assert.ok(fs.existsSync(trackDir), `missing HLS directory: ${track.id}`);

  const playlistPath = path.join(trackDir, "playlist.m3u8");
  assert.ok(fs.existsSync(playlistPath), `missing playlist.m3u8 for ${track.id}`);

  const files = fs.readdirSync(trackDir);
  const segmentFiles = files.filter((f) => /^seg_\d{3}\.ts$/.test(f));
  assert.ok(segmentFiles.length > 0, `no seg_XXX.ts files for ${track.id}`);
}

console.log(`PASS: verified HLS naming for ${catalog.tracks.length} tracks`);
