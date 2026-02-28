export function assertMediaEngine(mediaEngine) {
  if (!mediaEngine) {
    throw new Error("PlaybackController requires a mediaEngine");
  }

  const requiredMethods = ["load", "play", "pause", "seek"];
  for (const method of requiredMethods) {
    if (typeof mediaEngine[method] !== "function") {
      throw new Error(`mediaEngine is missing required method: ${method}`);
    }
  }
}

export class BrowserMediaEngine {
  constructor() {
    this.audio = new Audio();
    this.supportsNativeHls = Boolean(this.audio.canPlayType("application/vnd.apple.mpegurl"));
  }

  async load(url) {
    if (url.endsWith(".m3u8") && !this.supportsNativeHls) {
      throw new Error("native hls unsupported");
    }
    this.audio.src = url;
    this.audio.load();
  }

  async play() {
    await this.audio.play();
  }

  async pause() {
    this.audio.pause();
  }

  async seek(positionSec) {
    this.audio.currentTime = positionSec;
  }

  getCurrentTimeSec() {
    return this.audio.currentTime || 0;
  }

  onTimeUpdate(handler) {
    this.audio.addEventListener("timeupdate", handler);
  }

  onEnded(handler) {
    this.audio.addEventListener("ended", handler);
  }
}
