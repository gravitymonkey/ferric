import assert from "node:assert/strict";
import fs from "node:fs";
import { PlaybackController } from "../src/playback/playback-controller.mjs";

function createFakeMediaEngine() {
  const calls = [];
  return {
    calls,
    async load(url) {
      calls.push(["load", url]);
    },
    async play() {
      calls.push(["play"]);
    },
    async seek(positionSec) {
      calls.push(["seek", positionSec]);
    },
    async pause() {
      calls.push(["pause"]);
    }
  };
}

const catalog = JSON.parse(fs.readFileSync(new URL("../public/catalog.json", import.meta.url), "utf8"));
const tracks = catalog.tracks;
assert.ok(tracks.length >= 2, "golden flow requires at least 2 tracks");

const engine = createFakeMediaEngine();
const controller = new PlaybackController(engine);
controller.setQueue(tracks);

// Golden flow: load app -> start track -> pause -> seek -> next track
await controller.playAt(0);
await controller.pause();
await controller.seek(30);
const state = await controller.next();

assert.equal(state.currentTrackId, tracks[1].id);
assert.equal(state.currentIndex, 1);
assert.equal(state.isPlaying, true);

assert.deepEqual(engine.calls, [
  ["load", tracks[0].stream.url],
  ["play"],
  ["pause"],
  ["seek", 30],
  ["load", tracks[1].stream.url],
  ["play"]
]);

console.log("PASS: golden flow regression passes");
