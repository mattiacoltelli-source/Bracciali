// "Prova sulla foto": un quadro nuovo sovrapposto a una foto vera della parete, con prospettiva e misure giuste.
// Si toccano i 4 angoli di un quadro già appeso di cui si conoscono le misure: da lì si ricava il piano della parete.
import * as THREE from 'three';
import { artTexture } from './scene.js';

const $ = (id) => document.getElementById(id);
const KL = 'salotto.foto.v1'; // quadri aggiunti da qui
const KC = 'salotto.foto.cal.v1'; // calibrazioni, una per foto
const KM = 'salotto.v1'; // quadri del salotto 3D (solo lettura)
const MAXPX = 2048;

// ---------- matematica ----------
function solve(A, b) { // eliminazione di Gauss con pivot
  const n = b.length, M = A.map((r, i) => [...r, b[i]]);
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    if (Math.abs(M[p][c]) < 1e-12) return null;
    [M[c], M[p]] = [M[p], M[c]];
    for (let r = c + 1; r < n; r++) { const f = M[r][c] / M[c][c]; for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k]; }
  }
  const x = Array(n).fill(0);
  for (let r = n - 1; r >= 0; r--) { let s = M[r][n]; for (let k = r + 1; k < n; k++) s -= M[r][k] * x[k]; x[r] = s / M[r][r]; }
  return x;
}
// omografia (riga per riga) che porta 4 punti `src` (cm sulla parete) in 4 punti `dst` (pixel della foto)
function homography(src, dst) {
  const A = [], b = [];
  for (let i = 0; i < 4; i++) {
    const [u, v] = src[i], [x, y] = dst[i];
    A.push([u, v, 1, 0, 0, 0, -u * x, -v * x]); b.push(x);
    A.push([0, 0, 0, u, v, 1, -u * y, -v * y]); b.push(y);
  }
  const h = solve(A, b);
  return h && [...h, 1];
}
function inv3(m) {
  const [a, b, c, d, e, f, g, h, i] = m;
  const A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g;
  const det = a * A + b * B + c * C;
  if (Math.abs(det) < 1e-18) return null;
  return [A, -(b * i - c * h), b * f - c * e, B, a * i - c * g, -(a * f - c * d), C, -(a * h - b * g), a * e - b * d].map((v) => v / det);
}
function apply(m, x, y) { const w = m[6] * x + m[7] * y + m[8]; return [(m[0] * x + m[1] * y + m[2]) / w, (m[3] * x + m[4] * y + m[5]) / w, w]; }
// angoli in ordine: alto-sinistra, alto-destra, basso-destra, basso-sinistra, comunque siano stati toccati
function orderCorners(pts) {
  const cx = pts.reduce((s, p) => s + p[0], 0) / 4, cy = pts.reduce((s, p) => s + p[1], 0) / 4;
  const o = [...pts].sort((p, q) => Math.atan2(p[1] - cy, p[0] - cx) - Math.atan2(q[1] - cy, q[0] - cx));
  let k = 0;
  o.forEach((p, i) => { if (p[0] + p[1] < o[k][0] + o[k][1]) k = i; });
  return [0, 1, 2, 3].map((i) => o[(k + i) % 4]);
}
function convex(p) {
  let sign = 0;
  for (let i = 0; i < 4; i++) {
    const a = p[i], b = p[(i + 1) % 4], c = p[(i + 2) % 4];
    const z = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]);
    if (Math.abs(z) < 1e-6) return false;
    if (sign && Math.sign(z) !== sign) return false;
    sign = Math.sign(z);
  }
  return true;
}

// ---------- stato ----------
const S = {
  state: 'start', pw: 0, ph: 0, key: '', loupeUrl: '',
  corners: [], ref: { w: 75, h: 50 }, H: null, Hinv: null,
  art: null, w: 75, h: 50, cu: 0, cv: 0, bright: 0.9, shadow: 0.6, floorRef: null, hide: false, step: 5, show: 1,
};
const view = { z: 1, x: 0, y: 0 }; // zoom e spostamento della foto sullo schermo
let cssScale = 1, drag = null;
const readJson = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
const writeJson = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { showErr('Spazio del telefono pieno: non riesco a ricordare questa scelta.'); } };
function showErr(msg) { const e = $('err'); e.textContent = msg; e.hidden = false; setTimeout(() => { e.hidden = true; }, 4000); }

// ---------- disegno (un solo passaggio sulla GPU) ----------
let renderer;
try { renderer = new THREE.WebGLRenderer({ canvas: $('fc'), preserveDrawingBuffer: true, antialias: false }); }
catch { showErr('Il tuo browser non riesce a mostrare la foto (WebGL non disponibile).'); throw new Error('WebGL'); }
const scene = new THREE.Scene();
const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const mat = new THREE.ShaderMaterial({
  uniforms: {
    uPhoto: { value: null }, uArt: { value: null }, uPhotoSize: { value: new THREE.Vector2(1, 1) },
    uHinv: { value: new THREE.Matrix3() }, uH: { value: new THREE.Matrix3() }, uRect: { value: new THREE.Vector4(0, 0, 75, 50) },
    uRef: { value: new THREE.Vector2(75, 50) }, uHide: { value: 0 },
    uBright: { value: 0.9 }, uShadow: { value: 0.6 }, uShow: { value: 1 }, uSign: { value: 1 },
  },
  vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
  fragmentShader: `
    uniform sampler2D uPhoto; uniform sampler2D uArt;
    uniform vec2 uPhotoSize; uniform mat3 uHinv; uniform mat3 uH; uniform vec4 uRect; uniform vec2 uRef; uniform float uHide;
    uniform float uBright; uniform float uShadow; uniform float uShow; uniform float uSign;
    varying vec2 vUv;
    float sdBox(vec2 p, vec2 b) { vec2 d = abs(p) - b; return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0); }
    // colore della foto in un punto della parete (cm, origine nell'angolo alto-sinistra del quadro di riferimento)
    vec3 wallPx(vec2 w) { vec3 p = uH * vec3(w, 1.0); vec2 t = p.xy / p.z / uPhotoSize; return textureLod(uPhoto, vec2(t.x, 1.0 - t.y), 0.0).rgb; }
    void main() {
      vec3 col = texture2D(uPhoto, vUv).rgb;
      vec2 px = vec2(vUv.x, 1.0 - vUv.y) * uPhotoSize;
      vec3 q = uHinv * vec3(px, 1.0);
      bool front = q.z * uSign > 1e-6;
      float ok = (uShow > 0.5 && front) ? 1.0 : 0.0;
      vec2 wp = q.xy / (front ? q.z : 1.0); // cm sulla parete
      if (uHide > 0.5 && ok > 0.5) { // copro il quadro di riferimento col colore del muro intorno
        vec2 lo = vec2(-3.5), hi = uRef + 3.5;
        float edge = min(min(wp.x - lo.x, hi.x - wp.x), min(wp.y - lo.y, hi.y - wp.y));
        if (edge > 0.0) {
          vec2 a = (wp - lo) / (hi - lo);
          float e = 1.5;
          vec3 L = wallPx(vec2(lo.x - e, wp.y)), R = wallPx(vec2(hi.x + e, wp.y));
          vec3 T = wallPx(vec2(wp.x, lo.y - e)), B = wallPx(vec2(wp.x, hi.y + e));
          vec3 c00 = wallPx(lo - e), c10 = wallPx(vec2(hi.x + e, lo.y - e)), c01 = wallPx(vec2(lo.x - e, hi.y + e)), c11 = wallPx(hi + e);
          vec3 fill = mix(L, R, a.x) + mix(T, B, a.y) - mix(mix(c00, c10, a.x), mix(c01, c11, a.x), a.y);
          col = mix(col, fill, smoothstep(0.0, 1.5, edge));
        }
      }
      vec2 rel = wp - uRect.xy; // cm sulla parete, dal centro del quadro
      vec2 hs = uRect.zw * 0.5;
      float sd = sdBox(rel, hs);
      float pxCm = max(length(vec2(dFdx(sd), dFdy(sd))), 1e-4);
      float cover = clamp(0.5 - sd / pxCm, 0.0, 1.0) * ok;
      float sds = sdBox(rel - vec2(0.6, 1.6), hs); // ombra morbida: un po' sotto e a destra
      float sh = (1.0 - smoothstep(-0.5, 3.0, sds)) * uShadow * 0.45 * ok;
      col *= 1.0 - sh * (1.0 - cover);
      vec2 uv = rel / uRect.zw + 0.5;
      vec3 art = texture2D(uArt, vec2(uv.x, 1.0 - uv.y)).rgb * uBright;
      art *= mix(0.8, 1.0, smoothstep(0.0, 0.9, -sd)); // bordo della tela
      col = mix(col, art, cover);
      gl_FragColor = vec4(col, 1.0);
      #include <colorspace_fragment>
    }`,
});
scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat));
const drawNow = () => renderer.render(scene, cam);
let raf = 0;
const redraw = () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; drawNow(); }); };
function pushUniforms() {
  const u = mat.uniforms;
  if (S.Hinv) {
    const m = S.Hinv, f = S.H;
    u.uHinv.value.set(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8]);
    u.uH.value.set(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8]);
    const cx = S.corners.reduce((s, p) => s + p[0], 0) / 4, cy = S.corners.reduce((s, p) => s + p[1], 0) / 4;
    u.uSign.value = Math.sign(m[6] * cx + m[7] * cy + m[8]) || 1;
  }
  u.uRect.value.set(S.cu, S.cv, S.w, S.h);
  u.uRef.value.set(S.ref.w, S.ref.h); u.uHide.value = S.hide ? 1 : 0;
  u.uBright.value = S.bright; u.uShadow.value = S.shadow; u.uShow.value = S.state === 'try' ? S.show : 0;
  redraw();
}

// ---------- foto ----------
async function loadPhoto(file) {
  const url = URL.createObjectURL(file);
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    const k = Math.min(1, MAXPX / Math.max(img.naturalWidth, img.naturalHeight));
    const w = Math.round(img.naturalWidth * k), h = Math.round(img.naturalHeight * k);
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.getContext('2d').drawImage(img, 0, 0, w, h);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace; tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false;
    mat.uniforms.uPhoto.value?.dispose();
    mat.uniforms.uPhoto.value = tex;
    mat.uniforms.uPhotoSize.value.set(w, h);
    renderer.setSize(w, h, false);
    S.pw = w; S.ph = h;
    if (S.loupeUrl) URL.revokeObjectURL(S.loupeUrl);
    S.loupeUrl = await new Promise((res) => c.toBlob((b) => res(URL.createObjectURL(b)), 'image/jpeg', 0.9));
    S.key = `${file.name}|${file.size}|${file.lastModified}`;
    view.z = 1; view.x = 0; view.y = 0;
    return true;
  } catch (e) {
    console.error(e);
    showErr('Non riesco a leggere questa foto.');
    return false;
  } finally { URL.revokeObjectURL(url); }
}

// ---------- quadri ----------
const sample = () => ({ id: 'prova', name: 'Esempio', w: 75, h: 50, art: ['#8ec1e6', '#e6edf1', '#2b7fa5'] });
let LIST = [];
function loadList() {
  const mine = readJson(KL, []);
  const fromRoom = readJson(KM, []).filter((p) => p.img).map((p) => ({ id: 'r' + p.id, name: p.name, w: Math.round(p.w * 100), h: Math.round(p.h * 100), img: p.img }));
  LIST = [...mine, ...fromRoom, sample()];
}
const artCache = new Map();
function artTex(p) {
  if (artCache.has(p.id)) return Promise.resolve(artCache.get(p.id));
  if (!p.img) { const t = artTexture(p.art); artCache.set(p.id, t); return Promise.resolve(t); }
  return new Promise((res) => new THREE.TextureLoader().load(p.img, (t) => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; artCache.set(p.id, t); res(t); }, undefined, () => res(artTexture(['#999', '#ccc', '#666']))));
}
async function chooseArt(p) {
  S.art = p;
  mat.uniforms.uArt.value = await artTex(p);
  S.w = p.w; S.h = p.h;
  markList(); refreshTry(); pushUniforms(); saveCal();
}
function markList() {
  document.querySelectorAll('#t-list button').forEach((b, i) => b.setAttribute('aria-pressed', String(LIST[i]?.id === S.art?.id)));
  $('t-del').hidden = !S.art || !readJson(KL, []).some((p) => p.id === S.art.id);
}
function refreshList() {
  loadList();
  const box = $('t-list');
  box.replaceChildren();
  for (const p of LIST) {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = p.name;
    b.onclick = () => chooseArt(p);
    box.append(b);
  }
  const add = document.createElement('button');
  add.type = 'button'; add.textContent = '+ Aggiungi';
  add.onclick = () => { const d = $('t-add'); d.open = true; d.scrollIntoView({ block: 'nearest' }); };
  box.append(add);
  markList();
}

// ---------- calibrazione ----------
const HELP = ['Tocca l\'angolo in alto a sinistra del riferimento', 'Ora quello in alto a destra', 'Ora quello in basso a destra', 'Ora quello in basso a sinistra'];
function computeH() {
  if (S.corners.length !== 4) return false;
  const pts = orderCorners(S.corners);
  const area = Math.abs(pts.reduce((s, p, i) => { const q = pts[(i + 1) % 4]; return s + (p[0] * q[1] - q[0] * p[1]); }, 0)) / 2;
  if (!convex(pts) || area < 400) { showErr('I 4 punti non formano un quadro: rifai i punti.'); return false; }
  S.corners = pts;
  const H = homography([[0, 0], [S.ref.w, 0], [S.ref.w, S.ref.h], [0, S.ref.h]], pts);
  const Hi = H && inv3(H);
  if (!Hi) { showErr('Non riesco a calcolare la parete: rifai i punti.'); return false; }
  S.H = H; S.Hinv = Hi;
  return true;
}
function setState(st) {
  S.state = st;
  $('p-start').hidden = st !== 'start'; $('p-calib').hidden = st !== 'calib'; $('p-try').hidden = st !== 'try';
  $('fhint').textContent = st === 'calib' ? (S.corners.length < 4 ? HELP[S.corners.length] : 'Trascina i punti per sistemarli, poi premi "Prova il quadro"') : '';
  $('c-go').disabled = S.corners.length !== 4;
  layout(); drawOverlay(); pushUniforms(); sheetHeight();
}
function wallOf(x, y) { const [u, v] = apply(S.Hinv, x, y); return [u, v]; }
function saveCal() {
  if (!S.key || S.corners.length !== 4) return;
  const all = readJson(KC, {});
  all[S.key] = { c: S.corners.map((p) => [p[0] / S.pw, p[1] / S.ph]), ref: S.ref, art: S.art?.id, w: S.w, h: S.h, cu: S.cu, cv: S.cv, bright: S.bright, shadow: S.shadow, floorRef: S.floorRef, hide: S.hide };
  const keys = Object.keys(all);
  if (keys.length > 30) delete all[keys[0]];
  writeJson(KC, all);
}

// ---------- disposizione, zoom e disegno dei punti ----------
const stage = $('stage'), cvs = $('fc'), svg = $('overlay'), loupe = $('loupe'), zoomEl = $('zoom');
function layout() {
  if (!S.pw) { cvs.style.width = '0'; return; }
  const r = stage.getBoundingClientRect();
  cssScale = Math.min(r.width / S.pw, r.height / S.ph);
  const w = S.pw * cssScale, h = S.ph * cssScale;
  cvs.style.width = w + 'px'; cvs.style.height = h + 'px';
  svg.setAttribute('width', w); svg.setAttribute('height', h); svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.style.left = (r.width - w) / 2 + 'px'; svg.style.top = (r.height - h) / 2 + 'px';
  setView(view.z, view.x, view.y);
}
function setView(z, x, y) {
  const r = stage.getBoundingClientRect();
  view.z = Math.min(Math.max(z, 1), 8);
  view.x = Math.min(Math.max(x, r.width * (1 - view.z)), 0);
  view.y = Math.min(Math.max(y, r.height * (1 - view.z)), 0);
  zoomEl.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.z})`;
  $('zreset').hidden = view.z < 1.05;
  drawOverlay();
}
function zoomAbout(v0, m0, m1, z) { // tiene il punto sotto m0 (schermo) sotto m1 dopo lo zoom
  const r = stage.getBoundingClientRect(), z1 = Math.min(Math.max(z, 1), 8);
  const cx = (m0.x - r.left - v0.x) / v0.z, cy = (m0.y - r.top - v0.y) / v0.z;
  setView(z1, m1.x - r.left - z1 * cx, m1.y - r.top - z1 * cy);
}
function drawOverlay() {
  svg.replaceChildren();
  if (S.state !== 'calib') return;
  const ns = 'http://www.w3.org/2000/svg', k = cssScale, z = view.z;
  const mk = (tag, attrs) => { const e = document.createElementNS(ns, tag); for (const a in attrs) e.setAttribute(a, attrs[a]); svg.append(e); return e; };
  if (S.corners.length > 1) mk('polygon', { points: S.corners.map((p) => `${p[0] * k},${p[1] * k}`).join(' '), fill: 'rgba(255,138,61,.12)', stroke: '#ff8a3d', 'stroke-width': 1.5 / z });
  S.corners.forEach((p, i) => {
    mk('circle', { cx: p[0] * k, cy: p[1] * k, r: 4 / z, fill: '#ff8a3d' });
    const h = mk('circle', { cx: p[0] * k, cy: p[1] * k, r: 24 / z, fill: 'transparent', class: 'h' });
    h.dataset.i = i;
  });
}
function sheetHeight() { document.documentElement.style.setProperty('--sheet-h', $('fsheet').offsetHeight + 'px'); layout(); }
new ResizeObserver(sheetHeight).observe($('fsheet'));
window.addEventListener('resize', sheetHeight);
$('zreset').onclick = () => setView(1, 0, 0);

// ---------- lente d'ingrandimento ----------
function showLoupe(x, y, cx, cy) { // (x,y) punto della foto; (cx,cy) posizione del dito sullo schermo
  const size = 112, r = stage.getBoundingClientRect(), k = Math.max(cssScale * view.z * 2, 1); // almeno 1 pixel della foto per pixel dello schermo
  loupe.hidden = false;
  loupe.style.backgroundImage = `url(${S.loupeUrl})`;
  loupe.style.backgroundSize = `${S.pw * k}px ${S.ph * k}px`;
  loupe.style.backgroundPosition = `${size / 2 - x * k}px ${size / 2 - y * k}px`;
  const lx = Math.min(Math.max(cx - r.left - size / 2, 4), r.width - size - 4);
  let ly = cy - r.top - size - 36;
  if (ly < 4) ly = cy - r.top + 36;
  loupe.style.left = lx + 'px'; loupe.style.top = ly + 'px';
}

// ---------- tocchi sulla foto ----------
const ptrs = new Map(); // dita sullo schermo: id -> {x, y}
let pinch = null, gesture = false;
function photoXY(e) {
  const rc = cvs.getBoundingClientRect();
  return [Math.min(Math.max((e.clientX - rc.left) / rc.width * S.pw, 0), S.pw), Math.min(Math.max((e.clientY - rc.top) / rc.height * S.ph, 0), S.ph)];
}
function twoFingers() { const [a, b] = [...ptrs.values()]; return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, d: Math.hypot(a.x - b.x, a.y - b.y) || 1 }; }
stage.addEventListener('pointerdown', (e) => {
  if (!S.pw || e.target.closest('button')) return;
  ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
  stage.setPointerCapture(e.pointerId);
  if (ptrs.size >= 2) { // due dita: zoom e spostamento
    if (drag && drag.mode !== 'new') endDrag(); else { drag = null; loupe.hidden = true; }
    gesture = true;
    if (ptrs.size === 2) pinch = { ...twoFingers(), v: { ...view } };
    return;
  }
  gesture = false;
  const [x, y] = photoXY(e);
  const pan = () => { drag = view.z > 1 ? { mode: 'pan', x0: e.clientX, y0: e.clientY, v: { ...view } } : null; };
  if (S.state === 'calib') {
    const i = e.target.dataset?.i;
    if (i !== undefined) drag = { mode: 'h', i: Number(i) };
    else if (S.corners.length < 4) drag = { mode: 'new' };
    else { pan(); return; }
    drag.x = x; drag.y = y;
    showLoupe(x, y, e.clientX, e.clientY);
  } else if (S.state === 'try' && S.Hinv) {
    const [u, v] = wallOf(x, y);
    const m = 3;
    if (Math.abs(u - S.cu) <= S.w / 2 + m && Math.abs(v - S.cv) <= S.h / 2 + m) drag = { mode: 'art', du: S.cu - u, dv: S.cv - v };
    else pan();
  }
});
stage.addEventListener('pointermove', (e) => {
  if (ptrs.has(e.pointerId)) ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (pinch && ptrs.size === 2) { const m = twoFingers(); zoomAbout(pinch.v, pinch, m, pinch.v.z * m.d / pinch.d); return; }
  if (gesture || !drag) return;
  if (drag.mode === 'pan') { setView(drag.v.z, drag.v.x + e.clientX - drag.x0, drag.v.y + e.clientY - drag.y0); return; }
  const [x, y] = photoXY(e);
  if (drag.mode === 'art') {
    const [u, v] = wallOf(x, y);
    S.cu = u + drag.du; S.cv = v + drag.dv;
    refreshTry(); pushUniforms();
    return;
  }
  drag.x = x; drag.y = y;
  if (drag.mode === 'h') { S.corners[drag.i] = [x, y]; drawOverlay(); }
  showLoupe(x, y, e.clientX, e.clientY);
});
function endDrag() {
  if (!drag) return;
  const d = drag; drag = null;
  loupe.hidden = true;
  if (d.mode === 'new') { S.corners.push([d.x, d.y]); }
  if (d.mode === 'art') saveCal();
  if (d.mode === 'new' || d.mode === 'h') { if (S.corners.length === 4 && !computeH()) S.corners = []; setState('calib'); }
}
function release(e) { ptrs.delete(e.pointerId); if (ptrs.size < 2) pinch = null; if (!ptrs.size) gesture = false; }
stage.addEventListener('pointerup', (e) => { const g = gesture; release(e); if (!g) endDrag(); });
stage.addEventListener('pointercancel', (e) => { release(e); drag = null; loupe.hidden = true; });
stage.addEventListener('wheel', (e) => { // computer: rotella per lo zoom
  if (!S.pw) return;
  e.preventDefault();
  const p = { x: e.clientX, y: e.clientY };
  zoomAbout({ ...view }, p, p, view.z * Math.exp(-e.deltaY * 0.0015));
}, { passive: false });

// ---------- pannello "prova" ----------
const cmv = (v) => Math.round(v);
function refreshTry() {
  if (S.state !== 'try') return;
  $('t-w').value = cmv(S.w); $('t-h').value = cmv(S.h);
  const du = S.cu - S.ref.w / 2, dv = S.cv - S.ref.h / 2; // rispetto al centro del quadro di riferimento
  let t = `Centro a ${cmv(Math.abs(du))} cm ${du >= 0 ? 'a destra' : 'a sinistra'} e ${cmv(Math.abs(dv))} cm ${dv >= 0 ? 'più in basso' : 'più in alto'} del riferimento.`;
  if (S.floorRef != null && Number.isFinite(S.floorRef)) {
    const bottom = S.floorRef + S.ref.h - (S.cv + S.h / 2);
    t += ` Bordo basso a ${cmv(bottom)} cm da terra, centro a ${cmv(bottom + S.h / 2)} cm.`;
  }
  $('t-info').textContent = t;
}
async function startTry() {
  if (!S.Hinv) return;
  refreshList();
  if (!S.art) {
    const [wu, wv] = wallOf(S.pw / 2, S.ph / 2); // di partenza al centro della foto
    S.cu = wu; S.cv = wv;
    await chooseArt(LIST[0]);
  }
  setState('try'); markList(); refreshTry();
  saveCal();
}
document.querySelectorAll('[data-fstep]').forEach((b) => { b.onclick = () => { S.step = Number(b.dataset.fstep); document.querySelectorAll('[data-fstep]').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); }; });
document.querySelectorAll('[data-fnudge]').forEach((b) => {
  b.onclick = () => {
    const d = b.dataset.fnudge;
    if (d === 'left') S.cu -= S.step; if (d === 'right') S.cu += S.step;
    if (d === 'up') S.cv -= S.step; if (d === 'down') S.cv += S.step;
    refreshTry(); pushUniforms(); saveCal();
  };
});
const sizeChange = () => {
  const w = Number($('t-w').value), h = Number($('t-h').value);
  if (w >= 5) S.w = w; if (h >= 5) S.h = h;
  pushUniforms(); refreshTry(); saveCal();
};
$('t-w').onchange = sizeChange; $('t-h').onchange = sizeChange;
$('t-bright').oninput = (e) => { S.bright = Number(e.target.value) / 100; pushUniforms(); };
$('t-shadow').oninput = (e) => { S.shadow = Number(e.target.value) / 100; pushUniforms(); };
$('t-bright').onchange = saveCal; $('t-shadow').onchange = saveCal;
$('t-floor').oninput = (e) => { const v = e.target.value; S.floorRef = v === '' ? null : Number(v); refreshTry(); };
$('t-floor').onchange = saveCal;
$('t-hide').onchange = (e) => { S.hide = e.target.checked; pushUniforms(); saveCal(); };
const hold = (on) => { S.show = on ? 0 : 1; pushUniforms(); };
$('t-hold').addEventListener('pointerdown', () => hold(true));
['pointerup', 'pointerleave', 'pointercancel'].forEach((n) => $('t-hold').addEventListener(n, () => hold(false)));
$('t-hold').addEventListener('contextmenu', (e) => e.preventDefault());
$('t-save').onclick = async () => {
  S.show = 1; pushUniforms(); drawNow();
  const blob = await new Promise((res) => cvs.toBlob(res, 'image/jpeg', 0.92));
  if (!blob) { showErr('Non riesco a salvare l\'immagine.'); return; }
  const file = new File([blob], 'quadro-in-salotto.jpg', { type: 'image/jpeg' });
  try { if (navigator.canShare?.({ files: [file] })) { await navigator.share({ files: [file], title: 'Prova quadro' }); return; } }
  catch (e) { if (e && e.name === 'AbortError') return; }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = 'quadro-in-salotto.jpg'; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
};
$('t-recal').onclick = () => { S.corners = []; S.Hinv = S.H = null; setState('calib'); };
$('t-newphoto').onclick = () => { S.corners = []; S.H = S.Hinv = null; S.art = null; $('f-photo').value = ''; setState('start'); };

// ---------- pannello calibrazione ----------
function refSize() {
  const w = Number($('c-w').value), h = Number($('c-h').value);
  if (w >= 5 && h >= 5) { S.ref = { w, h }; if (S.corners.length === 4) { const ok = computeH(); if (!ok) { S.corners = []; setState('calib'); } } }
  markRef();
}
function markRef() {
  const w = Number($('c-w').value), h = Number($('c-h').value);
  document.querySelectorAll('[data-ref]').forEach((b) => { const [pw, ph] = b.dataset.ref.split(',').map(Number); b.setAttribute('aria-pressed', String(pw === w && ph === h)); });
}
document.querySelectorAll('[data-ref]').forEach((b) => { b.onclick = () => { const [w, h] = b.dataset.ref.split(',').map(Number); $('c-w').value = w; $('c-h').value = h; refSize(); }; });
$('c-w').onchange = refSize; $('c-h').onchange = refSize;
$('c-swap').onclick = () => { const w = $('c-w').value; $('c-w').value = $('c-h').value; $('c-h').value = w; refSize(); };
$('c-reset').onclick = () => { S.corners = []; S.H = S.Hinv = null; setState('calib'); };
$('c-go').onclick = startTry;
$('f-toggle').onclick = () => { const s = $('fsheet'); s.classList.toggle('collapsed'); $('f-toggle').textContent = s.classList.contains('collapsed') ? 'Mostra pannello' : 'Nascondi pannello'; sheetHeight(); };

// ---------- scelta della foto ----------
$('f-photo').onchange = async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  if (!(await loadPhoto(f))) return;
  const cal = readJson(KC, {})[S.key];
  S.corners = []; S.H = S.Hinv = null; S.art = null;
  if (cal) { // stessa foto di prima: ritrovo calibrazione e posizione
    S.ref = cal.ref; S.corners = cal.c.map((p) => [p[0] * S.pw, p[1] * S.ph]);
    S.w = cal.w; S.h = cal.h; S.cu = cal.cu; S.cv = cal.cv; S.bright = cal.bright; S.shadow = cal.shadow; S.floorRef = cal.floorRef ?? null; S.hide = !!cal.hide;
    $('c-w').value = S.ref.w; $('c-h').value = S.ref.h; markRef(); $('t-bright').value = Math.round(S.bright * 100); $('t-shadow').value = Math.round(S.shadow * 100);
    $('t-floor').value = S.floorRef ?? ''; $('t-hide').checked = S.hide;
    if (computeH()) {
      refreshList();
      const p = LIST.find((x) => x.id === cal.art) || LIST[0];
      S.art = p; mat.uniforms.uArt.value = await artTex(p);
      setState('try'); markList(); refreshTry();
      return;
    }
  }
  $('c-help').textContent = 'Scegli le misure del riferimento (quadro appeso o foglio attaccato al muro), poi toccane i 4 angoli. Tieni premuto: compare una lente per essere precisi. Pizzica con due dita per ingrandire la foto.';
  setState('calib');
};

// ---------- nuovo quadro ----------
let addRatio = 1.5;
$('a-file').onchange = async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  try { const b = await createImageBitmap(f); addRatio = b.width / b.height; b.close?.(); if ($('a-ratio').checked) $('a-h').value = Math.round(Number($('a-w').value) / addRatio); } catch { /* ok */ }
};
$('a-w').oninput = () => { if ($('a-ratio').checked) $('a-h').value = Math.round(Number($('a-w').value) / addRatio); };
async function toDataUrl(file) {
  const bmp = await createImageBitmap(file);
  const k = Math.min(1, 1024 / Math.max(bmp.width, bmp.height));
  const c = document.createElement('canvas');
  c.width = Math.round(bmp.width * k); c.height = Math.round(bmp.height * k);
  c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
  return c.toDataURL('image/jpeg', 0.88);
}
$('add-form').onsubmit = async (e) => {
  e.preventDefault();
  const f = $('a-file').files[0];
  if (!f) return;
  const btn = e.submitter; btn.disabled = true;
  try {
    const p = { id: 'f' + Date.now().toString(36), name: $('a-name').value.trim() || 'Nuovo quadro', w: Number($('a-w').value), h: Number($('a-h').value), img: await toDataUrl(f) };
    writeJson(KL, [...readJson(KL, []), p]);
    $('add-form').reset(); $('a-w').value = 75; $('a-h').value = 50;
    $('t-add').open = false;
    refreshList(); await chooseArt(LIST.find((x) => x.id === p.id) || p);
  } catch { showErr('Non riesco a leggere la foto del quadro.'); }
  btn.disabled = false;
};

$('t-del').onclick = () => {
  const id = S.art?.id;
  if (!id || !readJson(KL, []).some((p) => p.id === id)) return;
  if (!confirm('Eliminare questo quadro dall\'elenco? La foto del quadro viene cancellata dal telefono.')) return;
  writeJson(KL, readJson(KL, []).filter((p) => p.id !== id));
  artCache.delete(id);
  refreshList(); chooseArt(LIST[0]);
};
markRef();
cvs.addEventListener('webglcontextrestored', redraw);
document.addEventListener('visibilitychange', () => { if (!document.hidden) redraw(); });

setState('start');
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
window.__foto = { S, view };
