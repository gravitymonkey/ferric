import assert from "node:assert/strict";
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

const track1 = { id: "track_001", stream: { url: "/generated/hls/track_001/playlist.m3u8" } };
const track2 = { id: "track_002", stream: { url: "/generated/hls/track_002/playlist.m3u8" } };
const track3 = { id: "track_003", stream: { url: "/generated/hls/track_003/playlist.m3u8" } };
const idOnlyTrack = { id: "track_004" };

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  const state = await controller.play(track1);
  assert.deepEqual(engine.calls, [["load", track1.stream.url], ["play"]]);
  assert.equal(state.currentTrackId, "track_001");
  assert.equal(state.isPlaying, true);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine, {
    streamResolver: {
      async resolve(track) {
        return {
          track_id: track.id,
          stream: {
            protocol: "hls",
            url: `/resolved/${track.id}/playlist.m3u8`
          }
        };
      }
    }
  });

  await controller.play(track1);
  assert.deepEqual(engine.calls, [["load", "/resolved/track_001/playlist.m3u8"], ["play"]]);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine, {
    streamResolver: {
      async resolve(track) {
        return {
          track_id: track.id,
          stream: {
            protocol: "hls",
            url: `/resolved/${track.id}/playlist.m3u8`
          }
        };
      }
    }
  });

  await controller.play(idOnlyTrack);
  assert.deepEqual(engine.calls, [["load", "/resolved/track_004/playlist.m3u8"], ["play"]]);
  assert.equal(controller.getState().currentTrackId, "track_004");
}

{
  const calls = [];
  const engine = {
    calls,
    async load(url) {
      calls.push(["load", url]);
      if (url.endsWith(".m3u8")) {
        throw new Error("native hls unsupported");
      }
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

  const controller = new PlaybackController(engine, {
    streamResolver: {
      async resolve(track) {
        return {
          track_id: track.id,
          stream: {
            protocol: "hls",
            url: `/resolved/${track.id}/playlist.m3u8`,
            fallback_url: `/assets/raw-audio/${track.id}.mp3`
          }
        };
      }
    }
  });

  const state = await controller.play(track1);
  assert.equal(state.currentStreamUrl, "/assets/raw-audio/track_001.mp3");
  assert.deepEqual(calls, [
    ["load", "/resolved/track_001/playlist.m3u8"],
    ["load", "/assets/raw-audio/track_001.mp3"],
    ["play"]
  ]);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  await controller.play(track1);
  await controller.pause();
  await controller.play(track1);

  assert.deepEqual(engine.calls, [["load", track1.stream.url], ["play"], ["pause"], ["play"]]);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  await controller.play(track1);
  await controller.play(track2);

  assert.deepEqual(engine.calls, [
    ["load", track1.stream.url],
    ["play"],
    ["load", track2.stream.url],
    ["play"]
  ]);
  assert.equal(controller.getState().currentTrackId, "track_002");
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  await controller.play(track1);
  const state = await controller.pause();

  assert.deepEqual(engine.calls, [["load", track1.stream.url], ["play"], ["pause"]]);
  assert.equal(state.isPlaying, false);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  await controller.pause();
  assert.deepEqual(engine.calls, []);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  await controller.play(track1);
  const state = await controller.seek(42.9);

  assert.deepEqual(engine.calls, [["load", track1.stream.url], ["play"], ["seek", 42]]);
  assert.equal(state.positionSec, 42);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  await assert.rejects(() => controller.seek(5), /cannot seek without an active track/);
  assert.deepEqual(engine.calls, []);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  await controller.play(track1);

  await assert.rejects(() => controller.seek(-1), /non-negative number/);
  await assert.rejects(() => controller.seek(Number.NaN), /non-negative number/);

  assert.deepEqual(engine.calls, [["load", track1.stream.url], ["play"]]);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  await controller.play(track1);
  await controller.seek(15);

  const state = await controller.skipForward10();
  assert.equal(state.positionSec, 25);
  assert.deepEqual(engine.calls, [
    ["load", track1.stream.url],
    ["play"],
    ["seek", 15],
    ["seek", 25]
  ]);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  await controller.play(track1);
  await controller.seek(15);

  const state = await controller.skipBack10();
  assert.equal(state.positionSec, 5);
  assert.deepEqual(engine.calls, [
    ["load", track1.stream.url],
    ["play"],
    ["seek", 15],
    ["seek", 5]
  ]);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  await controller.play(track1);
  await controller.seek(6);

  const state = await controller.skipBack10();
  assert.equal(state.positionSec, 0);
  assert.deepEqual(engine.calls, [
    ["load", track1.stream.url],
    ["play"],
    ["seek", 6],
    ["seek", 0]
  ]);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  await assert.rejects(() => controller.skipForward10(), /cannot seek without an active track/);
  await assert.rejects(() => controller.skipBack10(), /cannot seek without an active track/);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  controller.setQueue([track1, track2]);

  let state = await controller.playAt(0);
  assert.equal(state.currentTrackId, "track_001");
  assert.equal(state.currentIndex, 0);

  state = await controller.next();
  assert.equal(state.currentTrackId, "track_002");
  assert.equal(state.currentIndex, 1);

  state = await controller.previous();
  assert.equal(state.currentTrackId, "track_001");
  assert.equal(state.currentIndex, 0);

  assert.deepEqual(engine.calls, [
    ["load", track1.stream.url],
    ["play"],
    ["load", track2.stream.url],
    ["play"],
    ["load", track1.stream.url],
    ["play"]
  ]);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  controller.setQueue([track1, track2]);

  await controller.playAt(1);
  const state = await controller.next();
  assert.equal(state.currentTrackId, "track_002");
  assert.equal(state.currentIndex, 1);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  controller.setQueue([track1, track2]);

  await controller.playAt(0);
  const state = await controller.previous();
  assert.equal(state.currentTrackId, "track_001");
  assert.equal(state.currentIndex, 0);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  await assert.rejects(() => controller.next(), /without a queue/);
  await assert.rejects(() => controller.previous(), /without a queue/);
  await assert.rejects(() => controller.playAt(0), /out of range/);
}

{
  const engine = createFakeMediaEngine();
  const randomValues = [0.7, 0.2, 0.9];
  const controller = new PlaybackController(engine, {
    randomFn: () => randomValues.shift() ?? 0
  });

  controller.setQueue([track1, track2, track3]);
  await controller.playAt(1);

  let state = controller.toggleShuffle(true);
  assert.equal(state.shuffleEnabled, true);
  assert.equal(state.currentTrackId, "track_002");
  assert.equal(state.currentIndex, 0);

  state = await controller.next();
  assert.equal(state.currentTrackId, "track_001");
  assert.equal(state.currentIndex, 1);

  state = controller.toggleShuffle(false);
  assert.equal(state.shuffleEnabled, false);
  assert.equal(state.currentTrackId, "track_001");
  assert.equal(state.currentIndex, 0);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);

  let state = controller.toggleShuffle(true);
  assert.equal(state.shuffleEnabled, true);
  state = controller.toggleShuffle(false);
  assert.equal(state.shuffleEnabled, false);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  controller.setQueue([track1, track2]);
  await controller.playAt(0);

  let state = controller.setRepeatMode("one");
  assert.equal(state.repeatMode, "one");
  state = await controller.handleTrackEnded();

  assert.equal(state.currentTrackId, "track_001");
  assert.equal(state.currentIndex, 0);
  assert.equal(state.isPlaying, true);
  assert.deepEqual(engine.calls, [
    ["load", track1.stream.url],
    ["play"],
    ["seek", 0],
    ["play"]
  ]);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  controller.setQueue([track1, track2]);
  await controller.playAt(0);

  const state = await controller.handleTrackEnded();
  assert.equal(state.currentTrackId, "track_002");
  assert.equal(state.currentIndex, 1);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  controller.setQueue([track1, track2]);
  await controller.playAt(1);

  let state = await controller.handleTrackEnded();
  assert.equal(state.currentTrackId, "track_002");
  assert.equal(state.currentIndex, 1);
  assert.equal(state.isPlaying, false);
  assert.equal(state.positionSec, 0);

  controller.setRepeatMode("all");
  state = await controller.handleTrackEnded();
  assert.equal(state.currentTrackId, "track_001");
  assert.equal(state.currentIndex, 0);
  assert.equal(state.isPlaying, true);
}

{
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine);
  assert.throws(() => controller.setRepeatMode("invalid"), /one of: off, one, all/);
}

console.log("PASS: play/pause/seek/skip/next/previous/shuffle/repeat controller behavior is correct");
