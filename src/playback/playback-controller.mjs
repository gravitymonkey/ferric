import { assertMediaEngine } from "./media-engine.mjs";
import { QueueManager } from "./queue-manager.mjs";
import { StaticStreamResolver, assertStreamResolver } from "./stream-resolver.mjs";

export class PlaybackController {
  constructor(mediaEngine, options = {}) {
    assertMediaEngine(mediaEngine);

    const { randomFn = Math.random, streamResolver = new StaticStreamResolver() } = options;
    this.randomFn = randomFn;
    this.mediaEngine = mediaEngine;
    assertStreamResolver(streamResolver);
    this.streamResolver = streamResolver;
    this.queueManager = new QueueManager({ randomFn: this.randomFn });
    this.state = {
      currentTrackId: null,
      currentStreamUrl: null,
      isPlaying: false,
      positionSec: 0,
      currentIndex: -1,
      shuffleEnabled: false,
      repeatMode: "off"
    };
  }

  getState() {
    return { ...this.state };
  }

  setQueue(tracks) {
    this.queueManager.setQueue(tracks, this.state.currentTrackId, this.state.shuffleEnabled);
    this.state.currentIndex = this.queueManager.getCurrentIndex(this.state.currentTrackId);
    return this.getState();
  }

  toggleShuffle(enabled = !this.state.shuffleEnabled) {
    const nextEnabled = Boolean(enabled);
    if (nextEnabled === this.state.shuffleEnabled) {
      return this.getState();
    }

    this.state.shuffleEnabled = nextEnabled;
    this.queueManager.toggleShuffle(nextEnabled, this.state.currentTrackId);
    this.state.currentIndex = this.queueManager.getCurrentIndex(this.state.currentTrackId);
    return this.getState();
  }

  setRepeatMode(mode) {
    if (!["off", "one", "all"].includes(mode)) {
      throw new Error("repeat mode must be one of: off, one, all");
    }
    this.state.repeatMode = mode;
    return this.getState();
  }

  async playAt(index) {
    return this.play(this.queueManager.getTrackAt(index));
  }

  async play(track) {
    if (!track?.id) {
      throw new Error("play requires track.id");
    }

    const isNewTrack = track.id !== this.state.currentTrackId;
    if (isNewTrack) {
      const resolved = await this.streamResolver.resolve(track);
      const streamUrl = resolved?.stream?.url;
      const fallbackUrl = resolved?.stream?.fallback_url;
      if (!streamUrl) {
        throw new Error("stream resolver returned no stream.url");
      }

      let loadedUrl = streamUrl;
      try {
        await this.mediaEngine.load(streamUrl);
      } catch (error) {
        if (!fallbackUrl) {
          throw error;
        }
        await this.mediaEngine.load(fallbackUrl);
        loadedUrl = fallbackUrl;
      }

      this.state.currentTrackId = track.id;
      this.state.currentStreamUrl = loadedUrl;
      this.state.positionSec = 0;

      const queueIndex = this.queueManager.getCurrentIndex(track.id);
      this.state.currentIndex = queueIndex;
    }

    await this.mediaEngine.play();
    this.state.isPlaying = true;
    return this.getState();
  }

  async next() {
    if (this.queueManager.getLength() === 0) {
      throw new Error("cannot go next without a queue");
    }

    const nextIndex = this.state.currentIndex + 1;
    if (nextIndex >= this.queueManager.getLength()) {
      return this.getState();
    }

    return this.playAt(nextIndex);
  }

  async previous() {
    if (this.queueManager.getLength() === 0) {
      throw new Error("cannot go previous without a queue");
    }

    const prevIndex = this.state.currentIndex - 1;
    if (prevIndex < 0) {
      return this.getState();
    }

    return this.playAt(prevIndex);
  }

  async handleTrackEnded() {
    if (!this.state.currentTrackId) {
      return this.getState();
    }

    if (this.state.repeatMode === "one") {
      await this.mediaEngine.seek(0);
      await this.mediaEngine.play();
      this.state.positionSec = 0;
      this.state.isPlaying = true;
      return this.getState();
    }

    if (this.queueManager.getLength() === 0) {
      this.state.isPlaying = false;
      this.state.positionSec = 0;
      return this.getState();
    }

    const atEnd = this.state.currentIndex >= this.queueManager.getLength() - 1;
    if (atEnd && this.state.repeatMode === "all") {
      return this.playAt(0);
    }

    if (atEnd) {
      this.state.isPlaying = false;
      this.state.positionSec = 0;
      return this.getState();
    }

    return this.next();
  }

  async seek(positionSec) {
    if (!this.state.currentTrackId) {
      throw new Error("cannot seek without an active track");
    }

    if (!Number.isFinite(positionSec) || positionSec < 0) {
      throw new Error("seek requires a non-negative number of seconds");
    }

    const normalized = Math.floor(positionSec);
    await this.mediaEngine.seek(normalized);
    this.state.positionSec = normalized;
    return this.getState();
  }

  updatePlaybackPosition(positionSec) {
    if (!Number.isFinite(positionSec) || positionSec < 0) {
      return this.getState();
    }
    this.state.positionSec = Math.floor(positionSec);
    return this.getState();
  }

  async skipForward10() {
    return this.seek(this.state.positionSec + 10);
  }

  async skipBack10() {
    return this.seek(Math.max(0, this.state.positionSec - 10));
  }

  async pause() {
    if (!this.state.isPlaying) {
      return this.getState();
    }

    await this.mediaEngine.pause();
    this.state.isPlaying = false;
    return this.getState();
  }
}
