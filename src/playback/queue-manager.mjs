export class QueueManager {
  constructor(options = {}) {
    const { randomFn = Math.random } = options;
    this.randomFn = randomFn;
    this.baseQueue = [];
    this.queue = [];
    this.shuffleEnabled = false;
  }

  setQueue(tracks, currentTrackId = null, shuffleEnabled = this.shuffleEnabled) {
    this.#assertTracks(tracks);
    this.baseQueue = tracks.slice();
    this.shuffleEnabled = Boolean(shuffleEnabled);
    this.queue = this.shuffleEnabled
      ? this.#buildShuffledQueue(this.baseQueue, currentTrackId)
      : this.baseQueue.slice();
    return this.getQueue();
  }

  toggleShuffle(enabled, currentTrackId = null) {
    this.shuffleEnabled = Boolean(enabled);
    this.queue = this.shuffleEnabled
      ? this.#buildShuffledQueue(this.baseQueue, currentTrackId)
      : this.baseQueue.slice();
    return this.getQueue();
  }

  getQueue() {
    return this.queue.slice();
  }

  getLength() {
    return this.queue.length;
  }

  getTrackAt(index) {
    if (!Number.isInteger(index) || index < 0 || index >= this.queue.length) {
      throw new Error("queue index is out of range");
    }
    return this.queue[index];
  }

  getCurrentIndex(currentTrackId) {
    return this.queue.findIndex((track) => track.id === currentTrackId);
  }

  #assertTracks(tracks) {
    if (!Array.isArray(tracks)) {
      throw new Error("setQueue requires an array of tracks");
    }

    for (const track of tracks) {
      if (!track?.id || !track?.stream?.url) {
        throw new Error("each queued track requires id and stream.url");
      }
    }
  }

  #buildShuffledQueue(inputQueue, currentTrackId) {
    const currentTrack = inputQueue.find((track) => track.id === currentTrackId) ?? null;
    const rest = inputQueue.filter((track) => track.id !== currentTrackId);

    for (let i = rest.length - 1; i > 0; i -= 1) {
      const j = Math.floor(this.randomFn() * (i + 1));
      [rest[i], rest[j]] = [rest[j], rest[i]];
    }

    if (currentTrack) {
      return [currentTrack, ...rest];
    }
    return rest;
  }
}
