from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from backend.app.admin_auth import require_admin


admin_ui = APIRouter(tags=["admin-ui"])


@admin_ui.get("/admin", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def admin_page() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Ferric Admin</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Silkscreen:wght@400&display=swap" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      .footer-silkscreen {
        font-family: "Silkscreen", monospace;
        font-size: 8px;
      }
    </style>
  </head>
  <body class="min-h-screen bg-gradient-to-b from-slate-700 via-slate-900 to-slate-950 text-slate-100">
    <div class="mx-auto w-full max-w-6xl px-4 py-6 pb-20 sm:px-6 lg:px-8">
      <header class="mb-4 hidden items-center gap-3 md:flex">
        <a href="/admin" class="flex items-center gap-3 text-inherit no-underline">
          <img src="/images/ferric_invert.png" alt="Ferric" width="62" class="h-auto w-10 shrink-0 sm:w-12 md:w-[62px]" />
          <h1 class="text-2xl font-semibold tracking-tight">Admin</h1>
        </a>
      </header>

      <nav class="mb-4" aria-label="Admin sections">
        <div class="relative md:hidden">
          <button
            id="mobile-tab-toggle"
            class="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-900/80 px-3 py-2 text-sm font-medium text-slate-200"
            aria-expanded="false"
            aria-controls="mobile-tab-menu"
          >
            Ferric Admin
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-4 w-4">
              <path fill-rule="evenodd" d="M3 5.25A.75.75 0 0 1 3.75 4.5h16.5a.75.75 0 0 1 0 1.5H3.75A.75.75 0 0 1 3 5.25Zm0 6A.75.75 0 0 1 3.75 10.5h16.5a.75.75 0 0 1 0 1.5H3.75a.75.75 0 0 1-.75-.75Zm0 6a.75.75 0 0 1 .75-.75h16.5a.75.75 0 0 1 0 1.5H3.75a.75.75 0 0 1-.75-.75Z" clip-rule="evenodd" />
            </svg>
          </button>
          <div id="mobile-tab-menu" class="absolute left-0 top-full z-20 mt-2 hidden min-w-[180px] rounded-xl border border-slate-700 bg-slate-900 p-1 shadow-xl">
            <button data-tab-target="stats" data-tab-style="mobile" class="block w-full rounded-lg px-3 py-2 text-left text-sm text-slate-300">Stats</button>
            <button data-tab-target="listings" data-tab-style="mobile" class="mt-1 block w-full rounded-lg px-3 py-2 text-left text-sm text-slate-300">Listings</button>
            <button data-tab-target="create" data-tab-style="mobile" class="mt-1 block w-full rounded-lg px-3 py-2 text-left text-sm text-slate-300">Create New</button>
          </div>
        </div>
        <div class="hidden border-b border-slate-700 md:block">
          <div class="flex items-end gap-6">
            <button
              data-tab-target="stats"
              data-tab-style="desktop"
              class="border-b-2 border-transparent px-1 py-2 text-sm font-semibold text-slate-300 transition"
              aria-selected="true"
            >
              Stats
            </button>
            <button
              data-tab-target="listings"
              data-tab-style="desktop"
              class="border-b-2 border-transparent px-1 py-2 text-sm font-semibold text-slate-300 transition"
              aria-selected="false"
            >
              Listings
            </button>
            <button
              data-tab-target="create"
              data-tab-style="desktop"
              class="border-b-2 border-transparent px-1 py-2 text-sm font-semibold text-slate-300 transition"
              aria-selected="false"
            >
              Create New
            </button>
          </div>
        </div>
      </nav>

      <p id="message" class="mb-3 text-sm text-cyan-200"></p>

      <section id="page-stats" class="space-y-4">
        <section class="rounded-xl border border-slate-700 bg-slate-800/70 p-4 sm:p-5">
          <h2 class="mb-3 text-lg font-medium">Top 10 Most Played</h2>
          <div id="top-plays" class="space-y-2 text-sm text-slate-200"></div>
        </section>
      </section>

      <section id="page-listings" class="hidden space-y-4">
        <section class="flex flex-col gap-3 sm:flex-row sm:items-center">
          <input id="search" placeholder="Search title or artist" class="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm sm:max-w-sm" />
          <select id="status-filter" class="rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm">
            <option value="">all statuses</option>
            <option value="draft">draft</option>
            <option value="published">published</option>
            <option value="archived">archived</option>
          </select>
        </section>
        <section class="overflow-x-auto rounded-xl border border-slate-700 bg-slate-800/70">
          <table class="min-w-full text-left text-sm">
            <thead class="border-b border-slate-700 bg-slate-900/70 text-xs uppercase tracking-wide text-slate-300">
              <tr>
                <th class="px-3 py-2">
                  <button data-sort-key="title" class="sort-btn inline-flex items-center gap-1 hover:text-cyan-300">Title <span data-sort-indicator="title" class="text-[10px] text-slate-400">-</span></button>
                </th>
                <th class="px-3 py-2">
                  <button data-sort-key="artist" class="sort-btn inline-flex items-center gap-1 hover:text-cyan-300">Artist <span data-sort-indicator="artist" class="text-[10px] text-slate-400">-</span></button>
                </th>
                <th class="px-3 py-2">
                  <button data-sort-key="status" class="sort-btn inline-flex items-center gap-1 hover:text-cyan-300">Status <span data-sort-indicator="status" class="text-[10px] text-slate-400">-</span></button>
                </th>
                <th class="px-3 py-2">
                  <button data-sort-key="uploaded_at" class="sort-btn inline-flex items-center gap-1 hover:text-cyan-300">Uploaded <span data-sort-indicator="uploaded_at" class="text-[10px] text-slate-400">-</span></button>
                </th>
                <th class="px-3 py-2">
                  <button data-sort-key="updated_at" class="sort-btn inline-flex items-center gap-1 hover:text-cyan-300">Updated <span data-sort-indicator="updated_at" class="text-[10px] text-slate-400">-</span></button>
                </th>
                <th class="px-3 py-2">
                  <button data-sort-key="plays" class="sort-btn inline-flex items-center gap-1 hover:text-cyan-300">Plays <span data-sort-indicator="plays" class="text-[10px] text-slate-400">-</span></button>
                </th>
                <th class="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody id="track-table-body" class="divide-y divide-slate-700"></tbody>
          </table>
        </section>
        <section class="flex items-center justify-between gap-3">
          <button id="page-prev" class="rounded-md border border-slate-600 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40">
            Previous
          </button>
          <p id="page-indicator" class="text-xs text-slate-300">Page 1 of 1</p>
          <button id="page-next" class="rounded-md border border-slate-600 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40">
            Next
          </button>
        </section>
      </section>

      <section id="page-create" class="hidden space-y-4">
        <section class="rounded-xl border border-slate-700 bg-slate-800/70 p-4 sm:p-5">
          <h2 class="mb-3 text-lg font-medium">Create Track</h2>
          <form id="create-form" class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <input name="title" placeholder="title" class="rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm" required />
            <input name="artist" placeholder="artist" class="rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm" required />
            <select name="status" class="rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm">
              <option value="draft">draft</option>
              <option value="published">published</option>
              <option value="archived">archived</option>
            </select>
            <button class="rounded-md bg-cyan-500 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-cyan-400 sm:col-span-2 lg:col-span-1">Create</button>
          </form>
        </section>
      </section>

      <section id="page-edit" class="hidden space-y-4">
        <button id="edit-back" class="inline-flex rounded-md border border-cyan-500 px-3 py-1.5 text-sm text-cyan-200 hover:bg-cyan-500/20">
          Back to Listings
        </button>
        <section class="rounded-xl border border-slate-700 bg-slate-800/70 p-4 sm:p-5">
          <div class="mb-4">
            <h2 id="edit-track-title" class="text-lg font-medium">Edit Track</h2>
          </div>
          <form id="edit-track-form" class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label class="text-sm text-slate-300">
              Title
              <input
                id="edit-title"
                name="title"
                class="mt-1 w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>
            <label class="text-sm text-slate-300">
              Artist
              <input
                id="edit-artist"
                name="artist"
                class="mt-1 w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>
            <label class="text-sm text-slate-300">
              Duration (sec)
              <input
                id="edit-duration"
                name="duration_sec"
                type="number"
                min="0"
                class="mt-1 w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                required
              />
            </label>
            <label class="text-sm text-slate-300">
              Status
              <select
                id="edit-status"
                name="status"
                class="mt-1 w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              >
                <option value="draft">draft</option>
                <option value="published">published</option>
                <option value="archived">archived</option>
              </select>
            </label>
            <div class="sm:col-span-2">
              <div class="flex items-center gap-3">
                <button
                  id="edit-save"
                  type="submit"
                  class="rounded-md bg-cyan-500 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-cyan-400"
                >
                  Save Changes
                </button>
                <span id="edit-save-status" class="text-xs text-cyan-200"></span>
              </div>
            </div>
          </form>
        </section>

        <section class="rounded-xl border border-slate-700 bg-slate-800/70 p-4 sm:p-5">
          <h3 class="mb-3 text-base font-medium text-slate-100">Media Uploads</h3>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label class="text-sm text-slate-300">
              Audio (MP3/WAV/M4A/AAC)
              <input
                id="edit-audio-upload"
                type="file"
                accept=".mp3,.wav,.m4a,.aac"
                class="mt-1 block w-full text-sm text-slate-200"
              />
              <span class="mt-1 flex items-center gap-2 text-xs text-slate-400">
                <svg id="edit-audio-spinner" xmlns="http://www.w3.org/2000/svg" class="hidden h-3 w-3 animate-spin text-cyan-300" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v3a5 5 0 0 0-5 5H4Z"></path>
                </svg>
                <span id="edit-audio-upload-status">Select a file to upload immediately.</span>
              </span>
            </label>
            <label class="text-sm text-slate-300">
              Artwork (JPG/PNG/WEBP)
              <input
                id="edit-artwork-upload"
                type="file"
                accept=".jpg,.jpeg,.png,.webp"
                class="mt-1 block w-full text-sm text-slate-200"
              />
              <span class="mt-1 flex items-center gap-2 text-xs text-slate-400">
                <svg id="edit-artwork-spinner" xmlns="http://www.w3.org/2000/svg" class="hidden h-3 w-3 animate-spin text-cyan-300" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v3a5 5 0 0 0-5 5H4Z"></path>
                </svg>
                <span id="edit-artwork-upload-status">Select a file to upload immediately.</span>
              </span>
            </label>
          </div>
          <div id="edit-artwork-preview-wrap" class="mt-4">
            <p class="mb-2 text-xs uppercase tracking-wide text-slate-400">Current Artwork</p>
            <img id="edit-artwork-preview" src="" alt="" class="h-24 w-24 rounded-md border border-slate-700 object-cover" />
            <div id="edit-artwork-placeholder" class="hidden h-24 w-24 items-center justify-center rounded-md border border-dashed border-slate-600 bg-slate-900/60">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-8 w-8 text-slate-500">
                <path fill-rule="evenodd" d="M1.5 6A2.25 2.25 0 0 1 3.75 3.75h16.5A2.25 2.25 0 0 1 22.5 6v12a2.25 2.25 0 0 1-2.25 2.25H3.75A2.25 2.25 0 0 1 1.5 18V6Zm1.5 0a.75.75 0 0 1 .75-.75h16.5A.75.75 0 0 1 21 6v8.19l-3.72-3.72a1.5 1.5 0 0 0-2.12 0l-3.94 3.94-1.22-1.22a1.5 1.5 0 0 0-2.12 0L3 18.06V6Zm6 3.75a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
        </section>

        <section class="rounded-xl border border-slate-700 bg-slate-800/70 p-4 sm:p-5">
          <h3 class="mb-3 text-base font-medium text-slate-100">Track Metadata</h3>
          <div id="edit-metadata" class="text-sm text-slate-300"></div>
        </section>
      </section>

      <footer class="footer-silkscreen fixed inset-x-0 bottom-0 z-40 border-t border-slate-700 bg-slate-950/90 py-2 backdrop-blur-sm">
        <div class="flex items-center justify-center gap-6">
          <a href="https://github.com/gravitymonkey/ferric" target="_blank" rel="noreferrer" class="text-cyan-300 hover:text-cyan-200">Github</a>
          <a href="/admin/logs" class="text-cyan-300 hover:text-cyan-200">Tail Logs</a>
        </div>
      </footer>
    </div>

    <script>
      const messageEl = document.getElementById("message");
      const tableBodyEl = document.getElementById("track-table-body");
      const searchEl = document.getElementById("search");
      const statusFilterEl = document.getElementById("status-filter");
      const pagePrevEl = document.getElementById("page-prev");
      const pageNextEl = document.getElementById("page-next");
      const pageIndicatorEl = document.getElementById("page-indicator");
      const createForm = document.getElementById("create-form");
      const topPlaysEl = document.getElementById("top-plays");
      const editTrackTitleEl = document.getElementById("edit-track-title");
      const editTrackFormEl = document.getElementById("edit-track-form");
      const editSaveStatusEl = document.getElementById("edit-save-status");
      const editTitleEl = document.getElementById("edit-title");
      const editArtistEl = document.getElementById("edit-artist");
      const editDurationEl = document.getElementById("edit-duration");
      const editStatusEl = document.getElementById("edit-status");
      const editAudioUploadEl = document.getElementById("edit-audio-upload");
      const editAudioUploadStatusEl = document.getElementById("edit-audio-upload-status");
      const editAudioSpinnerEl = document.getElementById("edit-audio-spinner");
      const editArtworkUploadEl = document.getElementById("edit-artwork-upload");
      const editArtworkUploadStatusEl = document.getElementById("edit-artwork-upload-status");
      const editArtworkSpinnerEl = document.getElementById("edit-artwork-spinner");
      const editArtworkPreviewWrapEl = document.getElementById("edit-artwork-preview-wrap");
      const editArtworkPreviewEl = document.getElementById("edit-artwork-preview");
      const editArtworkPlaceholderEl = document.getElementById("edit-artwork-placeholder");
      const editMetadataEl = document.getElementById("edit-metadata");
      const editBackEl = document.getElementById("edit-back");
      const mobileTabToggle = document.getElementById("mobile-tab-toggle");
      const mobileTabMenu = document.getElementById("mobile-tab-menu");
      const sortButtons = Array.from(document.querySelectorAll(".sort-btn"));
      const sortIndicators = Array.from(document.querySelectorAll("[data-sort-indicator]"));
      const PAGE_SIZE = 25;
      const LEAVE_UPLOAD_WARNING = "Are you sure? You will cancel your upload and processing.";
      let activeUploadCount = 0;
      const listingState = {
        tracks: [],
        playsByTrackId: new Map(),
        page: 1,
        selectedTrackId: null,
        sortKey: "title",
        sortDir: "asc",
        snapshotBeforeEdit: null,
      };
      const editState = { track: null, metadata: null };

      const tabButtons = Array.from(document.querySelectorAll("[data-tab-target]"));
      const pages = {
        stats: document.getElementById("page-stats"),
        listings: document.getElementById("page-listings"),
        create: document.getElementById("page-create"),
        edit: document.getElementById("page-edit"),
      };

      function showMessage(text, isError = false) {
        messageEl.textContent = text;
        messageEl.className = isError ? "mb-3 text-sm text-rose-300" : "mb-3 text-sm text-cyan-200";
      }

      function isUploadInFlight() {
        return activeUploadCount > 0;
      }

      function beginUpload() {
        activeUploadCount += 1;
      }

      function endUpload() {
        activeUploadCount = Math.max(0, activeUploadCount - 1);
      }

      function setActiveTab(tab) {
        Object.entries(pages).forEach(([name, el]) => {
          el.classList.toggle("hidden", name !== tab);
        });
        const highlightedTab = tab === "edit" ? "listings" : tab;
        tabButtons.forEach((btn) => {
          const active = btn.dataset.tabTarget === highlightedTab;
          const style = btn.dataset.tabStyle;
          btn.setAttribute("aria-selected", active ? "true" : "false");
          if (style === "desktop") {
            btn.classList.toggle("border-cyan-400", active);
            btn.classList.toggle("text-cyan-300", active);
            btn.classList.toggle("border-transparent", !active);
            btn.classList.toggle("text-slate-300", !active);
          } else {
            btn.classList.toggle("bg-slate-700", active);
            btn.classList.toggle("text-white", active);
            btn.classList.toggle("text-slate-300", !active);
          }
        });
      }

      async function api(path, init = {}) {
        const response = await fetch(path, init);
        const text = await response.text();
        const data = text ? JSON.parse(text) : {};
        if (!response.ok) {
          const msg = data?.error?.message || `Request failed: ${response.status}`;
          throw new Error(msg);
        }
        return data;
      }

      function formatAdminDateTime(value) {
        if (!value) return "-";
        const parsed = Date.parse(value);
        if (Number.isNaN(parsed)) return String(value);
        const date = new Date(parsed);
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const year = String(date.getFullYear()).slice(-2);
        const hours24 = date.getHours();
        const ampm = hours24 >= 12 ? "PM" : "AM";
        const hours12 = hours24 % 12 || 12;
        const minute = String(date.getMinutes()).padStart(2, "0");
        return `${month}/${day}/${year} ${hours12}:${minute} ${ampm}`;
      }

      function renderTrackRow(track) {
        const plays = listingState.playsByTrackId.get(track.id) || 0;
        const uploaded = formatAdminDateTime(track.uploaded_at);
        const updated = formatAdminDateTime(track.updated_at);
        return `
          <tr data-track-id="${track.id}" class="align-top">
            <td class="px-3 py-2 text-slate-100">${track.title}</td>
            <td class="px-3 py-2 text-slate-200">${track.artist}</td>
            <td class="px-3 py-2"><span class="uppercase text-slate-300">${track.status}</span></td>
            <td class="whitespace-nowrap px-3 py-2 text-slate-300">${uploaded}</td>
            <td class="whitespace-nowrap px-3 py-2 text-slate-300">${updated}</td>
            <td class="whitespace-nowrap px-3 py-2 text-cyan-200">${plays}</td>
            <td class="px-3 py-2">
              <button data-action="edit" class="inline-flex items-center gap-1.5 rounded-md border border-cyan-500 px-2.5 py-1 text-xs text-cyan-200 hover:bg-cyan-500/20">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-4 w-4">
                  <path d="M16.862 4.487a1.875 1.875 0 1 1 2.652 2.652L8.71 17.943a4.5 4.5 0 0 1-1.897 1.13l-2.685.805a.75.75 0 0 1-.932-.932l.805-2.685a4.5 4.5 0 0 1 1.13-1.897L16.862 4.487Z" />
                  <path d="M18 14.25a.75.75 0 0 0-1.5 0v3A2.25 2.25 0 0 1 14.25 19.5h-9A2.25 2.25 0 0 1 3 17.25v-9A2.25 2.25 0 0 1 5.25 6h3a.75.75 0 0 0 0-1.5h-3A3.75 3.75 0 0 0 1.5 8.25v9A3.75 3.75 0 0 0 5.25 21h9A3.75 3.75 0 0 0 18 17.25v-3Z" />
                </svg>
                Edit
              </button>
            </td>
          </tr>
        `;
      }

      function renderEditTrack() {
        const track = editState.track;
        if (!track) {
          editTrackTitleEl.textContent = "Edit Track";
          editMetadataEl.innerHTML = `<p class="text-slate-400">Track data unavailable.</p>`;
          return;
        }
        editTrackTitleEl.textContent = `Edit Track: ${track.title}`;
        editTitleEl.value = track.title || "";
        editArtistEl.value = track.artist || "";
        editDurationEl.value = String(track.duration_sec ?? 0);
        editStatusEl.value = track.status || "draft";

        const artwork = track.artwork?.square_512 || "";
        if (artwork) {
          showArtworkImage(artwork, `${track.title} artwork`);
        } else {
          showArtworkPlaceholder();
        }

        renderMetadataPanel();
      }

      function renderMetadataPanel() {
        const meta = editState.metadata;
        const noRecord = !meta;
        const fields = [
          ["track_id", meta?.track_id],
          ["analysis_version", meta?.analysis_version],
          ["analyzed_at", meta?.analyzed_at],
          ["sample_rate_hz", meta?.sample_rate_hz],
          ["duration_sec", meta?.duration_sec],
          ["tempo_bpm", meta?.tempo_bpm],
          ["beat_count", meta?.beat_count],
          ["onset_strength_mean", meta?.onset_strength_mean],
          ["rms_mean", meta?.rms_mean],
          ["rms_std", meta?.rms_std],
          ["spectral_centroid_mean", meta?.spectral_centroid_mean],
          ["spectral_centroid_std", meta?.spectral_centroid_std],
          ["spectral_bandwidth_mean", meta?.spectral_bandwidth_mean],
          ["spectral_rolloff_mean", meta?.spectral_rolloff_mean],
          ["spectral_flatness_mean", meta?.spectral_flatness_mean],
          ["zero_crossing_rate_mean", meta?.zero_crossing_rate_mean],
          ["mfcc_mean_json", meta?.mfcc_mean_json],
          ["chroma_mean_json", meta?.chroma_mean_json],
          ["tonnetz_mean_json", meta?.tonnetz_mean_json],
          ["metadata_json", meta?.metadata_json],
        ];
        editMetadataEl.innerHTML = `
          ${noRecord ? '<p class="mb-3 text-slate-400">No metadata record found yet.</p>' : ""}
          <div class="overflow-x-auto rounded-md border border-slate-700 bg-slate-900/60">
            <table class="min-w-full text-left text-sm">
              <thead class="border-b border-slate-700 bg-slate-900/80 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th class="px-3 py-2">Field</th>
                  <th class="px-3 py-2">Value</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-700">
            ${fields
              .map(([key, value]) => {
                const rendered = value === null || value === undefined || value === "" ? "-" : String(value);
                return `
                  <tr>
                    <td class="whitespace-nowrap px-3 py-2 text-xs uppercase tracking-wide text-slate-400">${key}</td>
                    <td class="px-3 py-2 break-all text-slate-100">${rendered}</td>
                  </tr>
                `;
              })
              .join("")}
              </tbody>
            </table>
          </div>
        `;
      }

      function showArtworkPlaceholder() {
        editArtworkPreviewWrapEl.classList.remove("hidden");
        editArtworkPreviewEl.classList.add("hidden");
        editArtworkPreviewEl.src = "";
        editArtworkPreviewEl.alt = "";
        editArtworkPlaceholderEl.classList.remove("hidden");
        editArtworkPlaceholderEl.classList.add("flex");
      }

      function showArtworkImage(src, alt) {
        editArtworkPreviewWrapEl.classList.remove("hidden");
        editArtworkPreviewEl.classList.remove("hidden");
        editArtworkPreviewEl.alt = alt;
        editArtworkPreviewEl.src = src;
        editArtworkPlaceholderEl.classList.add("hidden");
        editArtworkPlaceholderEl.classList.remove("flex");
      }

      function applyTrackUpdate(track) {
        if (!track || !track.id) return;
        listingState.tracks = listingState.tracks.map((row) => (row.id === track.id ? track : row));
        if (listingState.snapshotBeforeEdit) {
          listingState.snapshotBeforeEdit.tracks = listingState.snapshotBeforeEdit.tracks.map((row) =>
            row.id === track.id ? track : row
          );
        }
        if (editState.track && editState.track.id === track.id) {
          editState.track = track;
        }
      }

      function renderListingTable() {
        const sortedTracks = [...listingState.tracks].sort((a, b) => {
          const key = listingState.sortKey;
          const dir = listingState.sortDir === "asc" ? 1 : -1;

          if (key === "duration_sec") {
            return (Number(a.duration_sec) - Number(b.duration_sec)) * dir;
          }
          if (key === "plays") {
            const pa = listingState.playsByTrackId.get(a.id) || 0;
            const pb = listingState.playsByTrackId.get(b.id) || 0;
            return (pa - pb) * dir;
          }
          if (key === "updated_at") {
            const ta = Date.parse(a.updated_at || "") || 0;
            const tb = Date.parse(b.updated_at || "") || 0;
            return (ta - tb) * dir;
          }
          if (key === "uploaded_at") {
            const ta = Date.parse(a.uploaded_at || "") || 0;
            const tb = Date.parse(b.uploaded_at || "") || 0;
            return (ta - tb) * dir;
          }

          const av = String(a[key] || "").toLowerCase();
          const bv = String(b[key] || "").toLowerCase();
          const base = av.localeCompare(bv);
          if (base !== 0) return base * dir;
          return String(a.id).localeCompare(String(b.id)) * dir;
        });

        sortIndicators.forEach((el) => {
          if (el.dataset.sortIndicator === listingState.sortKey) {
            el.textContent = listingState.sortDir === "asc" ? "▲" : "▼";
            el.className = "text-[10px] text-cyan-300";
          } else {
            el.textContent = "-";
            el.className = "text-[10px] text-slate-400";
          }
        });

        const totalRows = sortedTracks.length;
        const totalPages = Math.max(1, Math.ceil(totalRows / PAGE_SIZE));
        listingState.page = Math.min(Math.max(listingState.page, 1), totalPages);
        const start = (listingState.page - 1) * PAGE_SIZE;
        const rows = sortedTracks.slice(start, start + PAGE_SIZE);

        if (rows.length === 0) {
          tableBodyEl.innerHTML = `
            <tr>
              <td colspan="7" class="px-3 py-6 text-center text-sm text-slate-400">No matching tracks.</td>
            </tr>
          `;
        } else {
          tableBodyEl.innerHTML = rows.map((track) => renderTrackRow(track)).join("");
        }
        pageIndicatorEl.textContent = `Page ${listingState.page} of ${totalPages}`;
        pagePrevEl.disabled = listingState.page <= 1;
        pageNextEl.disabled = listingState.page >= totalPages;
      }

      async function loadData() {
        const q = searchEl.value.trim();
        const status = statusFilterEl.value;
        const params = new URLSearchParams();
        if (q) params.set("q", q);
        if (status) params.set("status", status);

        const [data, stats] = await Promise.all([
          api(`/api/v1/admin/tracks?${params.toString()}`),
          api("/api/v1/admin/stats/tracks")
        ]);
        listingState.tracks = data.tracks;
        listingState.playsByTrackId = new Map(stats.tracks.map((row) => [row.track_id, row.starts]));
        renderListingTable();

        const names = new Map(data.tracks.map((t) => [t.id, `${t.title} — ${t.artist}`]));
        const top = [...stats.tracks].sort((a, b) => b.starts - a.starts).slice(0, 10);
        if (top.length === 0) {
          topPlaysEl.innerHTML = `<p class="text-slate-400">No plays recorded yet.</p>`;
        } else {
          topPlaysEl.innerHTML = top
            .map(
              (row, idx) => `
                <button data-action="stats-open-track" data-track-id="${row.track_id}" class="flex w-full items-center justify-between rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2 text-left transition hover:border-cyan-500/60 hover:bg-slate-900">
                  <span class="truncate pr-3 text-slate-200">${idx + 1}. ${names.get(row.track_id) || row.track_id}</span>
                  <span class="shrink-0 text-cyan-200">${row.starts} plays</span>
                </button>
              `
            )
            .join("");
        }
      }

      async function loadEditMetadata(trackId) {
        const response = await fetch(`/api/v1/admin/tracks/${trackId}/metadata`);
        if (response.status === 404) {
          editState.metadata = null;
          renderMetadataPanel();
          return;
        }
        const text = await response.text();
        const data = text ? JSON.parse(text) : {};
        if (!response.ok) {
          throw new Error(data?.error?.message || `Request failed: ${response.status}`);
        }
        editState.metadata = data;
        renderMetadataPanel();
      }

      async function openTrackEditor(trackId) {
        let track = listingState.tracks.find((row) => row.id === trackId);
        if (!track) {
          track = await api(`/api/v1/admin/tracks/${trackId}`);
          if (!listingState.tracks.some((row) => row.id === track.id)) {
            listingState.tracks.push(track);
          }
        }
        listingState.selectedTrackId = trackId;
        editState.track = track;
        editState.metadata = null;
        renderEditTrack();
        setActiveTab("edit");
        await loadEditMetadata(trackId);
      }

      tabButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
          setActiveTab(btn.dataset.tabTarget);
          if (mobileTabMenu) {
            mobileTabMenu.classList.add("hidden");
          }
          if (mobileTabToggle) {
            mobileTabToggle.setAttribute("aria-expanded", "false");
          }
        });
      });

      if (mobileTabToggle && mobileTabMenu) {
        mobileTabToggle.addEventListener("click", () => {
          const hidden = mobileTabMenu.classList.toggle("hidden");
          mobileTabToggle.setAttribute("aria-expanded", hidden ? "false" : "true");
        });
      }

      editArtworkPreviewEl.addEventListener("error", () => {
        showArtworkPlaceholder();
      });

      topPlaysEl.addEventListener("click", async (event) => {
        const button = event.target.closest("button[data-action='stats-open-track']");
        if (!button) return;
        const trackId = button.getAttribute("data-track-id");
        if (!trackId) return;
        listingState.snapshotBeforeEdit = {
          tracks: [...listingState.tracks],
          playsByTrackId: new Map(listingState.playsByTrackId),
          page: listingState.page,
          sortKey: listingState.sortKey,
          sortDir: listingState.sortDir,
          search: searchEl.value,
          status: statusFilterEl.value,
        };
        await openTrackEditor(trackId).catch((e) => showMessage(e.message, true));
      });

      tableBodyEl.addEventListener("click", async (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button) return;
        const row = event.target.closest("tr[data-track-id]");
        if (!row) return;
        const trackId = row.getAttribute("data-track-id");
        if (button.dataset.action === "edit") {
          listingState.snapshotBeforeEdit = {
            tracks: [...listingState.tracks],
            playsByTrackId: new Map(listingState.playsByTrackId),
            page: listingState.page,
            sortKey: listingState.sortKey,
            sortDir: listingState.sortDir,
            search: searchEl.value,
            status: statusFilterEl.value,
          };
          await openTrackEditor(trackId).catch((e) => showMessage(e.message, true));
        }
      });

      createForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(createForm);
        const payload = Object.fromEntries(formData.entries());
        const created = await api("/api/v1/admin/tracks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        showMessage(`Created ${created.id}`);
        createForm.reset();
        setActiveTab("listings");
        await loadData();
      });

      editTrackFormEl.addEventListener("submit", async (event) => {
        try {
          event.preventDefault();
          const trackId = listingState.selectedTrackId;
          if (!trackId) return;
          if (editSaveStatusEl) editSaveStatusEl.textContent = "Saving...";
          const payload = {
            title: editTitleEl.value.trim(),
            artist: editArtistEl.value.trim(),
            duration_sec: Number(editDurationEl.value),
            status: editStatusEl.value,
          };
          const updated = await api(`/api/v1/admin/tracks/${trackId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          applyTrackUpdate(updated);
          renderEditTrack();
          renderListingTable();
          if (editSaveStatusEl) editSaveStatusEl.textContent = "Saved";
          showMessage(`Saved ${updated.id}`);
        } catch (e) {
          if (editSaveStatusEl) editSaveStatusEl.textContent = "Save failed";
          showMessage(e.message || "Failed to save track", true);
        }
      });

      editAudioUploadEl.addEventListener("change", async () => {
        try {
          const trackId = listingState.selectedTrackId;
          const file = editAudioUploadEl.files?.[0];
          if (!trackId || !file) return;
          beginUpload();
          editAudioSpinnerEl.classList.remove("hidden");
          editAudioUploadEl.disabled = true;
          editAudioUploadStatusEl.textContent = `Uploading ${file.name}...`;
          const formData = new FormData();
          formData.append("file", file);
          const updated = await api(`/api/v1/admin/tracks/${trackId}/upload/audio`, {
            method: "POST",
            body: formData,
          });
          applyTrackUpdate(updated);
          await loadEditMetadata(trackId);
          renderEditTrack();
          renderListingTable();
          editAudioUploadEl.value = "";
          editAudioUploadStatusEl.textContent = `Uploaded ${file.name}`;
          showMessage(`Uploaded audio for ${trackId}`);
        } catch (e) {
          editAudioUploadStatusEl.textContent = "Audio upload failed";
          showMessage(e.message || "Failed to upload audio", true);
        } finally {
          endUpload();
          editAudioSpinnerEl.classList.add("hidden");
          editAudioUploadEl.disabled = false;
        }
      });

      editArtworkUploadEl.addEventListener("change", async () => {
        try {
          const trackId = listingState.selectedTrackId;
          const file = editArtworkUploadEl.files?.[0];
          if (!trackId || !file) return;
          beginUpload();
          editArtworkSpinnerEl.classList.remove("hidden");
          editArtworkUploadEl.disabled = true;
          editArtworkUploadStatusEl.textContent = `Uploading ${file.name}...`;
          const formData = new FormData();
          formData.append("file", file);
          const updated = await api(`/api/v1/admin/tracks/${trackId}/upload/artwork`, {
            method: "POST",
            body: formData,
          });
          applyTrackUpdate(updated);
          renderEditTrack();
          renderListingTable();
          editArtworkUploadEl.value = "";
          editArtworkUploadStatusEl.textContent = `Uploaded ${file.name}`;
          showMessage(`Uploaded artwork for ${trackId}`);
        } catch (e) {
          editArtworkUploadStatusEl.textContent = "Artwork upload failed";
          showMessage(e.message || "Failed to upload artwork", true);
        } finally {
          endUpload();
          editArtworkSpinnerEl.classList.add("hidden");
          editArtworkUploadEl.disabled = false;
        }
      });

      searchEl.addEventListener("input", () => {
        listingState.page = 1;
        loadData().catch((e) => showMessage(e.message, true));
      });
      statusFilterEl.addEventListener("change", () => {
        listingState.page = 1;
        loadData().catch((e) => showMessage(e.message, true));
      });
      sortButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
          const key = btn.dataset.sortKey;
          if (!key) return;
          if (listingState.sortKey === key) {
            listingState.sortDir = listingState.sortDir === "asc" ? "desc" : "asc";
          } else {
            listingState.sortKey = key;
            listingState.sortDir = "asc";
          }
          listingState.page = 1;
          renderListingTable();
        });
      });
      pagePrevEl.addEventListener("click", () => {
        listingState.page -= 1;
        renderListingTable();
      });
      pageNextEl.addEventListener("click", () => {
        listingState.page += 1;
        renderListingTable();
      });
      editBackEl.addEventListener("click", () => {
        const snap = listingState.snapshotBeforeEdit;
        if (snap) {
          listingState.tracks = [...snap.tracks];
          listingState.playsByTrackId = new Map(snap.playsByTrackId);
          listingState.page = snap.page;
          listingState.sortKey = snap.sortKey;
          listingState.sortDir = snap.sortDir;
          searchEl.value = snap.search;
          statusFilterEl.value = snap.status;
          renderListingTable();
        }
        setActiveTab("listings");
      });

      window.addEventListener("beforeunload", (event) => {
        if (!isUploadInFlight()) return;
        event.preventDefault();
        event.returnValue = LEAVE_UPLOAD_WARNING;
        return LEAVE_UPLOAD_WARNING;
      });

      document.addEventListener(
        "click",
        (event) => {
          if (!isUploadInFlight()) return;
          const link = event.target.closest("a[href]");
          if (!link) return;
          const href = link.getAttribute("href") || "";
          if (href.startsWith("#")) return;
          const shouldLeave = window.confirm(LEAVE_UPLOAD_WARNING);
          if (!shouldLeave) {
            event.preventDefault();
            event.stopPropagation();
          }
        },
        true
      );

      setActiveTab("stats");
      loadData().catch((err) => showMessage(err.message, true));
    </script>
  </body>
</html>"""


@admin_ui.get("/admin/logs", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def admin_logs_page() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Ferric Admin Logs</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Silkscreen:wght@400&display=swap" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      .footer-silkscreen {
        font-family: "Silkscreen", monospace;
        font-size: 8px;
      }
    </style>
  </head>
  <body class="min-h-screen bg-gradient-to-b from-slate-700 via-slate-900 to-slate-950 text-slate-100">
    <div class="mx-auto w-full max-w-6xl px-4 py-6 pb-20 sm:px-6 lg:px-8">
      <header class="mb-4 hidden items-center gap-3 md:flex">
        <a href="/admin" class="flex items-center gap-3 text-inherit no-underline">
          <img src="/images/ferric_invert.png" alt="Ferric" width="62" class="h-auto w-10 shrink-0 sm:w-12 md:w-[62px]" />
          <h1 class="text-2xl font-semibold tracking-tight">Admin</h1>
        </a>
      </header>

      <section class="mb-4 rounded-xl border border-slate-700 bg-slate-800/70 p-4 sm:p-5">
        <h2 class="text-lg font-medium">Tail Logs</h2>
        <p class="mt-2 text-sm text-slate-300">Read-only tailed logs from allowlisted service log files.</p>
        <div class="mt-3 flex flex-wrap items-center gap-3">
          <label class="text-sm text-slate-300">
            Source
            <select id="log-source" class="ml-2 rounded-md border border-slate-600 bg-slate-900 px-2 py-1 text-sm text-slate-100">
              <option value="backend">backend</option>
              <option value="frontend">frontend</option>
            </select>
          </label>
          <label class="text-sm text-slate-300">
            Lines
            <input id="log-lines" type="number" min="1" max="1000" value="200" class="ml-2 w-24 rounded-md border border-slate-600 bg-slate-900 px-2 py-1 text-sm text-slate-100" />
          </label>
          <button id="log-refresh" class="rounded-md border border-cyan-500 px-3 py-1.5 text-sm text-cyan-200 hover:bg-cyan-500/20">
            Refresh
          </button>
          <span id="log-meta" class="text-xs text-slate-400"></span>
        </div>
      </section>

      <section class="rounded-xl border border-slate-700 bg-slate-900/70 p-4 sm:p-5">
        <pre id="log-output" class="max-h-[60vh] overflow-auto whitespace-pre-wrap break-words text-xs text-slate-300">Loading logs...</pre>
      </section>

      <footer class="footer-silkscreen fixed inset-x-0 bottom-0 z-40 border-t border-slate-700 bg-slate-950/90 py-2 backdrop-blur-sm">
        <div class="flex items-center justify-center gap-6">
          <a href="/admin" class="text-cyan-300 hover:text-cyan-200">Admin Home</a>
          <a href="https://github.com/gravitymonkey/ferric" target="_blank" rel="noreferrer" class="text-cyan-300 hover:text-cyan-200">Github</a>
        </div>
      </footer>
    </div>
    <script>
      const sourceEl = document.getElementById("log-source");
      const linesEl = document.getElementById("log-lines");
      const refreshEl = document.getElementById("log-refresh");
      const outputEl = document.getElementById("log-output");
      const metaEl = document.getElementById("log-meta");

      async function loadLogs() {
        const source = sourceEl.value;
        const lines = Math.max(1, Math.min(1000, Number(linesEl.value || 200)));
        linesEl.value = String(lines);
        outputEl.textContent = "Loading logs...";
        metaEl.textContent = "";
        try {
          const response = await fetch(`/api/v1/admin/logs?source=${encodeURIComponent(source)}&lines=${lines}`);
          const text = await response.text();
          const data = text ? JSON.parse(text) : {};
          if (!response.ok) {
            const msg = data?.error?.message || `Request failed: ${response.status}`;
            outputEl.textContent = `Error: ${msg}`;
            return;
          }
          outputEl.textContent = data.lines.length ? data.lines.join("\\n") : "(no log lines yet)";
          metaEl.textContent = `${data.source} · ${data.line_count} lines · ${data.generated_at}`;
        } catch (err) {
          outputEl.textContent = `Error: ${err?.message || "Failed to load logs"}`;
        }
      }

      refreshEl.addEventListener("click", loadLogs);
      sourceEl.addEventListener("change", loadLogs);
      loadLogs();
    </script>
  </body>
</html>"""
