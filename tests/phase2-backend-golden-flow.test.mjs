import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

import { PlaybackController } from "../src/playback/playback-controller.mjs";
import { ApiCatalogSource } from "../src/data/catalog-source.mjs";
import { ApiStreamResolver } from "../src/playback/stream-resolver.mjs";

const BACKEND_PORT = 8010;
const BASE_URL = `http://127.0.0.1:${BACKEND_PORT}/api/v1`;

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

async function waitForReady(url, timeoutMs = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        return;
      }
    } catch {
      // keep polling until timeout
    }
    await delay(200);
  }
  throw new Error(`backend not ready at ${url}`);
}

const backendProc = spawn(
  "python3",
  ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)],
  { stdio: "ignore" }
);

try {
  await waitForReady(`${BASE_URL}/health`);

  const catalogSource = new ApiCatalogSource({ baseUrl: BASE_URL });
  const streamResolver = new ApiStreamResolver({ baseUrl: BASE_URL });
  const engine = createFakeMediaEngine();
  const controller = new PlaybackController(engine, { streamResolver });

  const catalog = await catalogSource.fetchCatalog();
  assert.ok(Array.isArray(catalog.tracks) && catalog.tracks.length >= 2, "catalog must include at least 2 tracks");
  controller.setQueue(catalog.tracks);

  // Golden flow against backend APIs:
  // load app -> start track -> pause -> seek -> next track
  await controller.playAt(0);
  await controller.pause();
  await controller.seek(30);
  const state = await controller.next();

  assert.equal(state.currentTrackId, catalog.tracks[1].id);
  assert.equal(state.currentIndex, 1);
  assert.equal(state.isPlaying, true);

  assert.deepEqual(engine.calls, [
    ["load", `/generated/hls/${catalog.tracks[0].id}/playlist.m3u8`],
    ["play"],
    ["pause"],
    ["seek", 30],
    ["load", `/generated/hls/${catalog.tracks[1].id}/playlist.m3u8`],
    ["play"]
  ]);

  console.log("PASS: phase 2 backend golden flow regression passes");
} finally {
  backendProc.kill("SIGTERM");
}
