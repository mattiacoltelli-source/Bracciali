"use strict";
// Repo derivato dall'URL di GitHub Pages (https://<owner>.github.io/<repo>/), così sopravvive ai rename.
const FALLBACK_REPO = "mattiacoltelli-source/video-lab";
const REPO = location.hostname.endsWith(".github.io") && location.pathname.split("/")[1]
  ? `${location.hostname.split(".")[0]}/${location.pathname.split("/")[1]}`
  : FALLBACK_REPO;
const API = `https://api.github.com/repos/${REPO}/releases?per_page=100`;
const CACHE_KEY = "videolab.releases.v1";

const $ = (id) => document.getElementById(id);
const grid = $("grid"), empty = $("empty"), errBox = $("error"), statusEl = $("status");
const dlg = $("player"), video = $("video");
let current = null;

const store = {
  get() { try { return JSON.parse(localStorage.getItem(CACHE_KEY)); } catch { return null; } },
  set(v) { try { localStorage.setItem(CACHE_KEY, JSON.stringify(v)); } catch { /* storage non disponibile */ } },
};

const fmtDate = (iso) => new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "short", year: "numeric" });
const fmtSize = (b) => (b >= 1e6 ? (b / 1e6).toFixed(1) + " MB" : Math.round(b / 1e3) + " KB");

function toVideos(releases) {
  return releases
    .filter((r) => !r.draft && /^video-/.test(r.tag_name))
    .map((r) => {
      const mp4 = r.assets.find((a) => /\.mp4$/i.test(a.name));
      const jpg = r.assets.find((a) => /\.jpe?g$/i.test(a.name));
      return mp4 && { id: r.id, title: r.name || r.tag_name, date: r.published_at || r.created_at, url: mp4.browser_download_url, size: mp4.size, poster: jpg && jpg.browser_download_url };
    })
    .filter(Boolean);
}

function render(videos) {
  grid.replaceChildren();
  empty.hidden = videos.length > 0;
  for (const v of videos) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "card";
    const thumb = document.createElement("div");
    thumb.className = "thumb";
    if (v.poster) {
      const img = document.createElement("img");
      img.src = v.poster; img.alt = ""; img.loading = "lazy";
      thumb.append(img);
    }
    const play = document.createElement("span");
    play.className = "play";
    thumb.append(play);
    const info = document.createElement("div");
    info.className = "info";
    const t = document.createElement("div");
    t.className = "t"; t.textContent = v.title;
    const m = document.createElement("div");
    m.className = "m"; m.textContent = `${fmtDate(v.date)} · ${fmtSize(v.size)}`;
    info.append(t, m);
    card.append(thumb, info);
    card.addEventListener("click", () => openPlayer(v));
    grid.append(card);
  }
}

function skeleton() {
  grid.replaceChildren(...Array.from({ length: 4 }, () => Object.assign(document.createElement("div"), { className: "skel" })));
}

async function load() {
  errBox.hidden = true; empty.hidden = true; statusEl.hidden = true;
  $("refresh").classList.add("spin");
  const cached = store.get();
  if (cached) render(cached); else skeleton();
  try {
    const res = await fetch(API, { headers: { Accept: "application/vnd.github+json" } });
    if (!res.ok) throw new Error(res.status === 403 ? "limite richieste GitHub, riprova tra poco" : `HTTP ${res.status}`);
    const videos = toVideos(await res.json());
    store.set(videos);
    render(videos);
  } catch (e) {
    if (cached) {
      statusEl.textContent = "Offline o GitHub non raggiungibile: mostro l'ultima lista salvata.";
      statusEl.hidden = false;
    } else {
      grid.replaceChildren();
      errBox.hidden = false;
    }
  } finally {
    $("refresh").classList.remove("spin");
  }
}

function openPlayer(v) {
  current = v;
  $("p-title").textContent = v.title;
  $("p-meta").textContent = `${fmtDate(v.date)} · ${fmtSize(v.size)}`;
  $("p-msg").textContent = "";
  $("p-download").href = v.url;
  $("p-share").hidden = !navigator.share;
  video.src = v.url;
  if (v.poster) video.poster = v.poster; else video.removeAttribute("poster");
  dlg.showModal();
}

function closePlayer() {
  if (dlg.open) dlg.close();
}
dlg.addEventListener("close", () => { video.pause(); video.removeAttribute("src"); video.load(); current = null; });
dlg.addEventListener("click", (e) => { if (e.target === dlg) closePlayer(); });
$("close").addEventListener("click", closePlayer);

$("p-share").addEventListener("click", async () => {
  const v = current, msg = $("p-msg");
  if (!v) return;
  msg.textContent = "Preparo il file…";
  try {
    const blob = await (await fetch(v.url)).blob();
    const file = new File([blob], `${v.title.replace(/[^\w-]+/g, "_") || "video"}.mp4`, { type: "video/mp4" });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file], title: v.title });
    } else {
      await navigator.share({ title: v.title, url: v.url });
    }
    msg.textContent = "";
  } catch (e) {
    if (e && e.name === "AbortError") { msg.textContent = ""; return; }
    // fetch bloccato (CORS) o share non riuscita: ripiego sul link
    try { await navigator.share({ title: v.title, url: v.url }); msg.textContent = ""; }
    catch (e2) { msg.textContent = e2 && e2.name === "AbortError" ? "" : "Condivisione non riuscita, usa Scarica."; }
  }
});

$("refresh").addEventListener("click", load);
$("retry").addEventListener("click", load);

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
load();
