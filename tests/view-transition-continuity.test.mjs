import assert from "node:assert/strict";
import { PlaybackController } from "../src/playback/playback-controller.mjs";
import { ViewShell } from "../src/app/view-shell.mjs";

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

const track1 = { id: "track_001", stream: { url: "/generated/hls/track_001/playlist.m3u8" } };
const track2 = { id: "track_002", stream: { url: "/generated/hls/track_002/playlist.m3u8" } };

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  controller.setQueue([track1, track2]);
  const shell = new ViewShell(controller);

  await controller.playAt(0);
  await controller.seek(37);
  const before = controller.getState();

  let shellState = shell.switchView("now-playing");
  assert.equal(shellState.view, "now-playing");
  assert.deepEqual(shellState.playback, before);

  shellState = shell.switchView("list");
  assert.equal(shellState.view, "list");
  assert.deepEqual(shellState.playback, before);

  assert.deepEqual(engine.calls, [
    ["load", track1.stream.url],
    ["play"],
    ["seek", 37]
  ]);
}

console.log("PASS: playback state remains continuous across view transitions");
