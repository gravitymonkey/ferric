import { PlaybackController } from "../src/playback/playback-controller.mjs";
import { BrowserMediaEngine } from "../src/playback/media-engine.mjs";
import { ApiStreamResolver } from "../src/playback/stream-resolver.mjs";
import { ApiCatalogSource } from "../src/data/catalog-source.mjs";
import { ViewShell } from "../src/app/view-shell.mjs";

const ICONS = {
  play: `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
      <path fill-rule="evenodd" d="M4.5 5.653c0-1.427 1.529-2.33 2.779-1.64l11.54 6.347c1.295.712 1.295 2.57 0 3.282l-11.54 6.347c-1.25.69-2.779-.213-2.779-1.64V5.653Z" clip-rule="evenodd" />
    </svg>
  `,
  stop: `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
      <rect x="6" y="6" width="12" height="12" rx="2.25" />
    </svg>
  `,
  pause: `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
      <path fill-rule="evenodd" d="M6.75 5.25A.75.75 0 0 1 7.5 4.5h2.25a.75.75 0 0 1 .75.75v13.5a.75.75 0 0 1-.75.75H7.5a.75.75 0 0 1-.75-.75V5.25Zm6.75 0a.75.75 0 0 1 .75-.75h2.25a.75.75 0 0 1 .75.75v13.5a.75.75 0 0 1-.75.75h-2.25a.75.75 0 0 1-.75-.75V5.25Z" clip-rule="evenodd" />
    </svg>
  `
};

function asBrowserTrack(track) {
  const rawStreamUrl = track.stream?.url ?? `/generated/hls/${track.id}/playlist.m3u8`;
  const rawFallbackUrl = track.stream?.fallback_url ?? null;
  const normalizedUrl = rawStreamUrl.startsWith("/generated/hls/") ? `/public${rawStreamUrl}` : rawStreamUrl;
  const normalizedFallback = rawFallbackUrl?.startsWith("/assets/raw-audio/") ? rawFallbackUrl : rawFallbackUrl ?? null;
  const normalizedArtwork = track.artwork?.square_512?.startsWith("/")
    ? track.artwork.square_512
    : track.artwork?.square_512 ?? null;

  return {
    ...track,
    artwork: {
      ...track.artwork,
      square_512: normalizedArtwork
    },
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
  const npDetailBlock = document.getElementById("np-detail-block");
  const npArtwork = document.getElementById("np-artwork");
  const npTitle = document.getElementById("np-title");
  const npArtist = document.getElementById("np-artist");
  const npScrubber = document.getElementById("np-scrubber");
  const npTimeCurrent = document.getElementById("np-time-current");
  const npTimeTotal = document.getElementById("np-time-total");
  const miniNowPlaying = document.getElementById("mini-now-playing");
  const miniNowPlayingMain = document.getElementById("mini-now-playing-main");
  const miniNowPlayingTime = document.getElementById("mini-now-playing-time");
  const playPauseBtn = document.getElementById("play-pause");
  const prevBtn = document.getElementById("previous");
  const nextBtn = document.getElementById("next");
  const shuffleBtn = document.getElementById("shuffle");
  const repeatBtn = document.getElementById("repeat");
  const transportButtons = [playPauseBtn, prevBtn, nextBtn, shuffleBtn, repeatBtn];
  let statusHideTimer = null;

  const mediaEngine = new BrowserMediaEngine();
  const apiStreamResolver = new ApiStreamResolver();
  const streamResolver = {
    async resolve(track, client) {
      const resolved = await apiStreamResolver.resolve(track, client);
      const streamUrl = resolved?.stream?.url ?? "";
      const fallbackUrl = resolved?.stream?.fallback_url ?? null;
      return {
        ...resolved,
        stream: {
          ...resolved.stream,
          url: streamUrl.startsWith("/generated/hls/") ? `/public${streamUrl}` : streamUrl,
          fallback_url: fallbackUrl?.startsWith("/assets/raw-audio/") ? fallbackUrl : fallbackUrl
        }
      };
    }
  };
  const catalogSource = new ApiCatalogSource();
  const controller = new PlaybackController(mediaEngine, { streamResolver });
  const shell = new ViewShell(controller);
  let tracks = [];
  let selectedTrackId = null;
  let isScrubbing = false;

  const navBaseClass =
    "rounded-lg px-4 py-2 text-sm font-semibold transition";
  const navActiveClass = "bg-cyan-400 text-slate-950 shadow-sm shadow-cyan-500/40";
  const navInactiveClass = "text-slate-300 hover:text-white";
  const actionBtnClass =
    "shrink-0 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm font-medium text-slate-100 transition hover:border-cyan-400 hover:text-cyan-200";
  const playBtnClass =
    "shrink-0 rounded-lg border border-cyan-500 bg-cyan-500/20 px-3 py-2 text-sm font-semibold text-cyan-200 transition hover:bg-cyan-500/30";

  nowBtn.className = navBaseClass;
  listBtn.className = navBaseClass;
  transportButtons.forEach((button) => {
    button.className = actionBtnClass;
  });
  prevBtn.className = actionBtnClass.replace("px-3", "px-4");
  nextBtn.className = actionBtnClass.replace("px-3", "px-4");
  playPauseBtn.className = playBtnClass;

  function showStatus(message, { variant = "neutral", persistent = false, durationMs = 2200 } = {}) {
    if (statusHideTimer) {
      clearTimeout(statusHideTimer);
      statusHideTimer = null;
    }

    statusEl.textContent = message;
    statusEl.classList.remove("hidden");

    if (variant === "error") {
      statusEl.className =
        "mb-4 rounded-lg border border-rose-700 bg-rose-900/30 px-3 py-2 text-sm text-rose-200";
    } else if (variant === "success") {
      statusEl.className =
        "mb-4 rounded-lg border border-emerald-700 bg-emerald-900/30 px-3 py-2 text-sm text-emerald-200";
    } else {
      statusEl.className =
        "mb-4 rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2 text-sm text-slate-300";
    }

    if (!persistent) {
      statusHideTimer = setTimeout(() => {
        statusEl.classList.add("hidden");
      }, durationMs);
    }
  }

  function animateTrackDetailShift() {
    if (!npDetailBlock) {
      return;
    }
    npDetailBlock.classList.remove("track-detail-shift");
    void npDetailBlock.offsetWidth;
    npDetailBlock.classList.add("track-detail-shift");
  }

  function render() {
    const state = controller.getState();
    const playingTrack = tracks.find((t) => t.id === state.currentTrackId) ?? null;
    const selectedTrack = tracks.find((t) => t.id === selectedTrackId) ?? null;
    const displayTrack = selectedTrack ?? playingTrack;
    const isSelectedTrackPlaying = Boolean(displayTrack && state.currentTrackId === displayTrack.id && state.isPlaying);
    const isSelectedTrackLoaded = Boolean(displayTrack && state.currentTrackId === displayTrack.id);

    listBtn.className = `${navBaseClass} ${shell.currentView === "list" ? navActiveClass : navInactiveClass}`;
    nowBtn.className = `${navBaseClass} ${shell.currentView === "now-playing" ? navActiveClass : navInactiveClass}`;
    listView.classList.toggle("hidden", shell.currentView !== "list");
    nowView.classList.toggle("hidden", shell.currentView !== "now-playing");

    if (!displayTrack) {
      npEmpty.classList.remove("hidden");
      npContent.classList.add("hidden");
      npScrubber.value = "0";
      npScrubber.max = "100";
      npScrubber.disabled = true;
      npTimeCurrent.textContent = "0:00";
      npTimeTotal.textContent = "0:00";
    } else {
      npEmpty.classList.add("hidden");
      npContent.classList.remove("hidden");
      npArtwork.src = displayTrack.artwork?.square_512 || "";
      npArtwork.alt = `${displayTrack.title} cover art`;
      npTitle.textContent = displayTrack.title;
      npArtist.textContent = displayTrack.artist;

      const totalSec = Math.max(0, Math.floor(displayTrack.duration_sec || 0));
      const currentSec = isSelectedTrackLoaded ? Math.min(state.positionSec, totalSec) : 0;
      npScrubber.max = String(Math.max(1, totalSec));
      npScrubber.disabled = !isSelectedTrackLoaded;
      if (!isScrubbing) {
        npScrubber.value = String(currentSec);
      }
      npTimeCurrent.textContent = formatTime(Math.floor(Number(npScrubber.value || 0)));
      npTimeTotal.textContent = formatTime(totalSec);
    }

    const showMiniNowPlaying = Boolean(shell.currentView !== "list" && state.isPlaying && playingTrack);
    miniNowPlaying.classList.toggle("hidden", !showMiniNowPlaying);
    if (showMiniNowPlaying) {
      miniNowPlaying.classList.add("flex");
      miniNowPlayingMain.textContent = `${playingTrack.title}: ${playingTrack.artist}`;
      miniNowPlayingTime.textContent = formatTime(state.positionSec);
    } else {
      miniNowPlaying.classList.remove("flex");
      miniNowPlayingMain.textContent = "";
      miniNowPlayingTime.textContent = "";
    }

    playPauseBtn.innerHTML = isSelectedTrackPlaying ? ICONS.pause : ICONS.play;
    playPauseBtn.setAttribute("data-state", isSelectedTrackPlaying ? "playing" : "paused");
    playPauseBtn.setAttribute("aria-label", isSelectedTrackPlaying ? "Pause" : "Play");
    shuffleBtn.textContent = `Shuffle: ${state.shuffleEnabled ? "On" : "Off"}`;
    repeatBtn.textContent = `Repeat: ${state.repeatMode}`;

    const rowButtons = trackList.querySelectorAll("button[data-track-id]");
    rowButtons.forEach((button) => {
      const trackId = button.getAttribute("data-track-id");
      const isActivePlaying = trackId === state.currentTrackId && state.isPlaying;
      button.innerHTML = isActivePlaying ? ICONS.stop : ICONS.play;
      button.setAttribute("aria-label", isActivePlaying ? "Stop track" : "Play track");
      button.className = isActivePlaying
        ? "inline-flex items-center justify-center rounded-lg border border-cyan-500 bg-cyan-500/20 px-3 py-2 text-sm font-medium text-cyan-200 transition hover:bg-cyan-500/30"
        : "inline-flex items-center justify-center rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm font-medium text-slate-100 transition hover:border-cyan-400 hover:text-cyan-200";
    });
  }

  npArtwork.addEventListener("error", () => {
    npArtwork.src =
      "data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 96 96'%3E%3Crect width='96' height='96' fill='%230f172a'/%3E%3Ccircle cx='48' cy='48' r='24' fill='%231e293b'/%3E%3C/svg%3E";
  });

  npScrubber.addEventListener("input", () => {
    isScrubbing = true;
    npTimeCurrent.textContent = formatTime(Math.floor(Number(npScrubber.value || 0)));
  });

  npScrubber.addEventListener("change", async () => {
    const targetTrackId = selectedTrackId;
    const state = controller.getState();
    const seekTo = Math.floor(Number(npScrubber.value || 0));

    if (!targetTrackId || state.currentTrackId !== targetTrackId) {
      isScrubbing = false;
      render();
      return;
    }

    await controller.seek(seekTo);
    isScrubbing = false;
    render();
  });

  function bindTrackList() {
    trackList.innerHTML = "";
    tracks.forEach((track, index) => {
      const li = document.createElement("li");
      li.setAttribute("data-track-id", track.id);
      li.className =
        "flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-3 transition hover:border-cyan-500/60";
      const left = document.createElement("div");
      left.className = "flex min-w-0 items-center gap-3";

      const art = document.createElement("img");
      art.className = "h-11 w-11 shrink-0 rounded-md border border-slate-700 object-cover";
      art.src = track.artwork?.square_512 || "";
      art.alt = `${track.title} cover art`;
      art.onerror = () => {
        art.style.display = "none";
      };

      const meta = document.createElement("span");
      meta.className = "truncate text-sm text-slate-200";
      meta.textContent = `${track.title} - ${track.artist} (${formatTime(track.duration_sec)})`;
      left.append(art, meta);
      li.addEventListener("click", async () => {
        selectedTrackId = track.id;
        shell.switchView("now-playing");
        render();
      });
      const btn = document.createElement("button");
      btn.setAttribute("data-track-id", track.id);
      btn.className =
        "inline-flex items-center justify-center rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm font-medium text-slate-100 transition hover:border-cyan-400 hover:text-cyan-200";
      btn.setAttribute("aria-label", "Play track");
      btn.innerHTML = ICONS.play;
      btn.addEventListener("click", async (event) => {
        event.stopPropagation();
        const state = controller.getState();
        const isCurrentTrack = state.currentTrackId === track.id;
        if (isCurrentTrack && state.isPlaying) {
          await controller.pause();
        } else {
          selectedTrackId = track.id;
          await controller.playAt(index);
          shell.switchView("now-playing");
        }
        render();
      });
      li.append(left, btn);
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
    const targetTrackId = selectedTrackId ?? state.currentTrackId;
    if (!targetTrackId) {
      return;
    }

    if (state.currentTrackId === targetTrackId && state.isPlaying) {
      await controller.pause();
    } else {
      const targetIndex = tracks.findIndex((track) => track.id === targetTrackId);
      if (targetIndex >= 0) {
        await controller.playAt(targetIndex);
        selectedTrackId = targetTrackId;
      }
    }
    render();
  });

  prevBtn.addEventListener("click", async () => {
    await controller.previous();
    selectedTrackId = controller.getState().currentTrackId ?? selectedTrackId;
    render();
  });

  nextBtn.addEventListener("click", async () => {
    await controller.next();
    selectedTrackId = controller.getState().currentTrackId ?? selectedTrackId;
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

  miniNowPlaying.addEventListener("click", () => {
    const state = controller.getState();
    if (!state.currentTrackId) {
      return;
    }
    selectedTrackId = state.currentTrackId;
    shell.switchView("now-playing");
    render();
  });

  mediaEngine.onTimeUpdate(() => {
    const sec = mediaEngine.getCurrentTimeSec();
    controller.updatePlaybackPosition(sec);
    render();
  });

  mediaEngine.onEnded(async () => {
    const before = controller.getState();
    const wasViewingPlayingTrack = selectedTrackId && selectedTrackId === before.currentTrackId;
    await controller.handleTrackEnded();
    const after = controller.getState();
    const advancedToDifferentTrack =
      Boolean(after.currentTrackId) && after.currentTrackId !== before.currentTrackId;

    if (wasViewingPlayingTrack && advancedToDifferentTrack) {
      selectedTrackId = after.currentTrackId;
      if (shell.currentView === "now-playing") {
        animateTrackDetailShift();
      }
    }
    render();
  });

  try {
    showStatus("Loading catalog...", { variant: "neutral", persistent: true });
    const catalog = await catalogSource.fetchCatalog();
    tracks = catalog.tracks.map(asBrowserTrack);
    controller.setQueue(tracks);
    selectedTrackId = tracks[0]?.id ?? null;
    bindTrackList();
    showStatus(`Loaded ${tracks.length} tracks.`, { variant: "success", persistent: false, durationMs: 1800 });
  } catch (error) {
    showStatus(`Error: ${error.message}`, { variant: "error", persistent: true });
  }

  render();
}

main();
