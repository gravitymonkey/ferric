import { PlaybackController } from "../src/playback/playback-controller.mjs";
import { BrowserMediaEngine } from "../src/playback/media-engine.mjs";
import { StaticStreamResolver } from "../src/playback/stream-resolver.mjs";
import { StaticCatalogSource } from "../src/data/catalog-source.mjs";
import { ViewShell } from "../src/app/view-shell.mjs";

function asBrowserTrack(track) {
  const normalizedUrl = track.stream.url.startsWith("/generated/hls/") ? `/public${track.stream.url}` : track.stream.url;
  const normalizedFallback = track.stream.fallback_url?.startsWith("/assets/raw-audio/")
    ? track.stream.fallback_url
    : track.stream.fallback_url ?? null;

  return {
    ...track,
    stream: {
      ...track.stream,
      url: normalizedUrl,
      fallback_url: normalizedFallback
    }
  };
}

function formatTime(sec) {
  const s = Math.max(0, Math.floor(sec));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, "0")}`;
}

async function main() {
  const statusEl = document.getElementById("status");
  const listView = document.getElementById("list-view");
  const nowView = document.getElementById("now-playing-view");
  const listBtn = document.getElementById("show-list");
  const nowBtn = document.getElementById("show-now-playing");
  const trackList = document.getElementById("track-list");
  const npEmpty = document.getElementById("now-playing-empty");
  const npContent = document.getElementById("now-playing-content");
  const npTitle = document.getElementById("np-title");
  const npArtist = document.getElementById("np-artist");
  const npPosition = document.getElementById("np-position");
  const playPauseBtn = document.getElementById("play-pause");
  const prevBtn = document.getElementById("previous");
  const nextBtn = document.getElementById("next");
  const back10Btn = document.getElementById("back-10");
  const fwd10Btn = document.getElementById("fwd-10");
  const shuffleBtn = document.getElementById("shuffle");
  const repeatBtn = document.getElementById("repeat");

  const mediaEngine = new BrowserMediaEngine();
  const streamResolver = new StaticStreamResolver();
  const catalogSource = new StaticCatalogSource();
  const controller = new PlaybackController(mediaEngine, { streamResolver });
  const shell = new ViewShell(controller);
  let tracks = [];

  function render() {
    const state = controller.getState();
    const active = tracks.find((t) => t.id === state.currentTrackId) ?? null;

    listBtn.classList.toggle("active", shell.currentView === "list");
    nowBtn.classList.toggle("active", shell.currentView === "now-playing");
    listView.classList.toggle("hidden", shell.currentView !== "list");
    nowView.classList.toggle("hidden", shell.currentView !== "now-playing");

    if (!active) {
      npEmpty.classList.remove("hidden");
      npContent.classList.add("hidden");
    } else {
      npEmpty.classList.add("hidden");
      npContent.classList.remove("hidden");
      npTitle.textContent = `Title: ${active.title}`;
      npArtist.textContent = `Artist: ${active.artist}`;
      npPosition.textContent = `Position: ${formatTime(state.positionSec)}`;
    }

    playPauseBtn.textContent = state.isPlaying ? "Pause" : "Play";
    shuffleBtn.textContent = `Shuffle: ${state.shuffleEnabled ? "On" : "Off"}`;
    repeatBtn.textContent = `Repeat: ${state.repeatMode}`;
  }

  function bindTrackList() {
    trackList.innerHTML = "";
    tracks.forEach((track, index) => {
      const li = document.createElement("li");
      const meta = document.createElement("span");
      meta.textContent = `${track.title} - ${track.artist} (${formatTime(track.duration_sec)})`;
      const btn = document.createElement("button");
      btn.textContent = "Play";
      btn.addEventListener("click", async () => {
        await controller.playAt(index);
        render();
      });
      li.append(meta, btn);
      trackList.append(li);
    });
  }

  listBtn.addEventListener("click", () => {
    shell.switchView("list");
    render();
  });

  nowBtn.addEventListener("click", () => {
    shell.switchView("now-playing");
    render();
  });

  playPauseBtn.addEventListener("click", async () => {
    const state = controller.getState();
    if (!state.currentTrackId) {
      return;
    }
    if (state.isPlaying) {
      await controller.pause();
    } else {
      await controller.playAt(state.currentIndex);
    }
    render();
  });

  prevBtn.addEventListener("click", async () => {
    await controller.previous();
    render();
  });

  nextBtn.addEventListener("click", async () => {
    await controller.next();
    render();
  });

  back10Btn.addEventListener("click", async () => {
    await controller.skipBack10();
    render();
  });

  fwd10Btn.addEventListener("click", async () => {
    await controller.skipForward10();
    render();
  });

  shuffleBtn.addEventListener("click", () => {
    controller.toggleShuffle();
    render();
  });

  repeatBtn.addEventListener("click", () => {
    const mode = controller.getState().repeatMode;
    const nextMode = mode === "off" ? "one" : mode === "one" ? "all" : "off";
    controller.setRepeatMode(nextMode);
    render();
  });

  mediaEngine.onTimeUpdate(() => {
    const sec = mediaEngine.getCurrentTimeSec();
    controller.updatePlaybackPosition(sec);
    render();
  });

  mediaEngine.onEnded(async () => {
    await controller.handleTrackEnded();
    render();
  });

  try {
    const catalog = await catalogSource.fetchCatalog();
    tracks = catalog.tracks.map(asBrowserTrack);
    controller.setQueue(tracks);
    bindTrackList();
    statusEl.textContent = `Loaded ${tracks.length} tracks.`;
  } catch (error) {
    statusEl.textContent = `Error: ${error.message}`;
  }

  render();
}

main();
