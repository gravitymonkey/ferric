import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";

const raw = fs.readFileSync(new URL("../public/catalog.json", import.meta.url), "utf8");
const catalog = JSON.parse(raw);

assert.equal(catalog.schema_version, "1.0");
assert.equal(catalog.app?.title, "Ferric POC");
assert.ok(Array.isArray(catalog.tracks), "tracks must be an array");
assert.ok(catalog.tracks.length >= 10, "catalog must contain at least 10 tracks");

const ids = new Set();

for (const track of catalog.tracks) {
  assert.ok(typeof track.id === "string" && track.id.length > 0, "track.id is required");
  assert.ok(!ids.has(track.id), `duplicate track id: ${track.id}`);
  ids.add(track.id);

  assert.ok(typeof track.title === "string" && track.title.length > 0, `title missing for ${track.id}`);
  assert.ok(typeof track.artist === "string" && track.artist.length > 0, `artist missing for ${track.id}`);
  assert.ok(Number.isInteger(track.duration_sec) && track.duration_sec > 0, `invalid duration for ${track.id}`);

  assert.ok(typeof track.artwork?.square_512 === "string", `artwork.square_512 missing for ${track.id}`);
  assert.ok(track.artwork.square_512.startsWith("/images/"), `artwork path invalid for ${track.id}`);

  assert.equal(track.stream?.protocol, "hls", `stream.protocol must be hls for ${track.id}`);
  assert.ok(typeof track.stream?.url === "string", `stream.url missing for ${track.id}`);
  assert.equal(
    track.stream.url,
    `/generated/hls/${track.id}/playlist.m3u8`,
    `stream.url must match normalized track path for ${track.id}`
  );

  assert.ok(typeof track.stream?.fallback_url === "string", `stream.fallback_url missing for ${track.id}`);
  assert.ok(track.stream.fallback_url.startsWith("/assets/raw-audio/"), `fallback path invalid for ${track.id}`);
  const localFallback = path.join(new URL("../", import.meta.url).pathname, track.stream.fallback_url.replace(/^\//, ""));
  assert.ok(fs.existsSync(localFallback), `fallback asset missing for ${track.id}`);
}

console.log(`PASS: validated ${catalog.tracks.length} tracks in public/catalog.json`);
