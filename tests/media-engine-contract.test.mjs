import assert from "node:assert/strict";
import { assertMediaEngine } from "../src/playback/media-engine.mjs";
import { PlaybackController } from "../src/playback/playback-controller.mjs";

{
  const valid = {
    async load() {},
    async play() {},
    async pause() {},
    async seek() {}
  };
  assert.doesNotThrow(() => assertMediaEngine(valid));
}

{
  assert.throws(
    () => assertMediaEngine({ async load() {}, async play() {}, async pause() {} }),
    /missing required method: seek/
  );
}

{
  assert.throws(() => new PlaybackController(null), /requires a mediaEngine/);
}

{
  assert.throws(
    () => new PlaybackController({ async load() {}, async play() {}, async pause() {} }),
    /missing required method: seek/
  );
}

console.log("PASS: media engine abstraction contract is enforced");
