import assert from "node:assert/strict";
import { QueueManager } from "../src/playback/queue-manager.mjs";

const track1 = { id: "track_001", stream: { url: "/generated/hls/track_001/playlist.m3u8" } };
const track2 = { id: "track_002", stream: { url: "/generated/hls/track_002/playlist.m3u8" } };
const track3 = { id: "track_003", stream: { url: "/generated/hls/track_003/playlist.m3u8" } };
const idOnlyTrack = { id: "track_004" };

{
  const manager = new QueueManager();
  const queue = manager.setQueue([track1, track2, track3], null, false);
  assert.deepEqual(queue.map((t) => t.id), ["track_001", "track_002", "track_003"]);
  assert.equal(manager.getCurrentIndex("track_002"), 1);
}

{
  const randomValues = [0.7, 0.2, 0.9];
  const manager = new QueueManager({ randomFn: () => randomValues.shift() ?? 0 });
  manager.setQueue([track1, track2, track3], "track_002", true);
  assert.equal(manager.getTrackAt(0).id, "track_002");
  assert.equal(manager.getLength(), 3);
}

{
  const randomValues = [0.7, 0.2, 0.9];
  const manager = new QueueManager({ randomFn: () => randomValues.shift() ?? 0 });
  manager.setQueue([track1, track2, track3], "track_002", false);
  manager.toggleShuffle(true, "track_002");
  assert.equal(manager.getTrackAt(0).id, "track_002");
  manager.toggleShuffle(false, "track_001");
  assert.deepEqual(manager.getQueue().map((t) => t.id), ["track_001", "track_002", "track_003"]);
}

{
  const manager = new QueueManager();
  const queue = manager.setQueue([idOnlyTrack], null, false);
  assert.equal(queue[0].id, "track_004");
}

{
  const manager = new QueueManager();
  assert.throws(() => manager.setQueue("bad"), /array of tracks/);
  assert.throws(() => manager.setQueue([{ stream: { url: "/generated/hls/x/playlist.m3u8" } }]), /requires id/);
  manager.setQueue([track1]);
  assert.throws(() => manager.getTrackAt(2), /out of range/);
}

console.log("PASS: queue manager behavior is correct");
