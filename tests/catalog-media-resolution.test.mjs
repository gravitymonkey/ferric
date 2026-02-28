import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";

const catalogPath = new URL("../public/catalog.json", import.meta.url);
const publicRoot = path.join(new URL("../public/", import.meta.url).pathname);
const catalog = JSON.parse(fs.readFileSync(catalogPath, "utf8"));

for (const track of catalog.tracks) {
  const streamUrl = track.stream?.url;
  assert.ok(typeof streamUrl === "string" && streamUrl.startsWith("/"), `invalid stream url for ${track.id}`);

  const localPath = path.join(publicRoot, streamUrl.replace(/^\//, ""));
  assert.ok(fs.existsSync(localPath), `missing stream target for ${track.id}: ${streamUrl}`);

  const playlistText = fs.readFileSync(localPath, "utf8");
  assert.ok(playlistText.includes("#EXTM3U"), `playlist header missing for ${track.id}`);

  const segmentRefs = playlistText
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"));

  assert.ok(segmentRefs.length > 0, `playlist has no segment entries for ${track.id}`);

  for (const segmentRef of segmentRefs) {
    const segmentPath = path.join(path.dirname(localPath), segmentRef);
    assert.ok(fs.existsSync(segmentPath), `missing segment ${segmentRef} for ${track.id}`);
  }
}

console.log(`PASS: resolved ${catalog.tracks.length} catalog stream URLs to valid HLS playlists`);
