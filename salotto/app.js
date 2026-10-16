import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { ROOM, WALLS, PAINTINGS, OLD_POS } from './room.js';
import { buildRoom, addLights, artTexture } from './scene.js';
import { createObjects } from './objects.js';

const $ = (id) => document.getElementById(id);
const KEY = 'salotto.v1';
const DEPTH = 0.03; // spessore del quadro (tela)

// ---------- dati dei quadri ----------
const defaults = () => PAINTINGS.map((p) => ({ id: p.id, name: p.name, w: p.w, h: p.h, wall: p.wall, u: WALLS[p.wall].toU(p.s), y: p.y, art: p.art }));
const FRAME_KEY = 'salotto.frame';
const markFrame = () => { try { localStorage.setItem(FRAME_KEY, '2'); } catch { /* ok */ } };
function load() {
  let ver = 0;
  try { ver = Number(localStorage.getItem(FRAME_KEY)) || 0; } catch { /* ok */ }
  try {
    const v = JSON.parse(localStorage.getItem(KEY));
    if (!Array.isArray(v)) { markFrame(); return null; }
    const fresh = new Set();
    for (const p of v) { // quadri mai spostati: dalle vecchie stime alle misure nuove
      const o = OLD_POS[p.id], d = defaults().find((x) => x.id === p.id);
      if (o && d && p.wall === d.wall && Math.abs(p.u - o[0]) < 1e-6 && Math.abs(p.y - o[1]) < 1e-6) { p.u = d.u; p.y = d.y; fresh.add(p.id); }
    }
    // l'origine delle misure sulla parete TV si è spostata sulla parete split vera (-30 cm): le posizioni salvate prima vanno corrette una volta sola
    let saved = true;
    if (ver < 2) {
      for (const p of v) if (p.wall === 'T' && !fresh.has(p.id)) p.u = Math.max(p.w / 2 + 0.02, p.u - 0.30);
      try { localStorage.setItem(KEY, JSON.stringify(v)); } catch { saved = false; } // si riscrive subito: al prossimo avvio le posizioni sono già quelle nuove
    }
    if (saved) markFrame();
    return v;
  } catch { markFrame(); return null; }
}
function save() {
  try { localStorage.setItem(KEY, JSON.stringify(paintings)); return true; }
  catch { showErr('Spazio del telefono pieno: il progetto non viene salvato. Elimina qualche quadro.'); return false; }
}
let paintings = load() || defaults();

function showErr(msg) { const e = $('err'); e.textContent = msg; e.hidden = false; setTimeout(() => { e.hidden = true; }, 4000); }

// ---------- scena ----------
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas: $('c'), antialias: (window.devicePixelRatio || 1) < 2 }); // sui telefoni ad alta densità si evita: pesa e non serve
} catch {
  showErr('Il tuo browser non riesce a mostrare il 3D (WebGL non disponibile).');
  throw new Error('WebGL');
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
const scene = new THREE.Scene();
scene.background = new THREE.Color('#0b0b0c');
const camera = new THREE.PerspectiveCamera(60, 1, 0.02, 200);
const controls = new OrbitControls(camera, renderer.domElement);
controls.minDistance = 0.05;
controls.maxDistance = 25;

const roomRoot = new THREE.Group(); // tutto il modello a blocchi: si nasconde mentre si apre la stanza a foto
scene.add(roomRoot);
const { pieces, groups } = buildRoom(roomRoot);
addLights(scene);

let needs = true;
const render = () => { needs = true; };
controls.addEventListener('change', render);
function resize() {
  const w = window.innerWidth, h = window.innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  walkApi?.refov();
  fitView();
}
window.addEventListener('resize', resize);

// Con una scheda aperta il centro della vista e' il centro di quello che resta visibile sopra la scheda: quello che guardi (e l'oggetto che metti a terra) non finisce dietro la scheda.
function fitView() {
  const sh = $('sheet'), W = window.innerWidth, H = window.innerHeight, cover = sh.hidden ? 0 : Math.min(sh.offsetHeight, H * 0.7);
  if (cover > 0) camera.setViewOffset(W, H, 0, Math.round(cover / 2), W, H); else camera.clearViewOffset();
  camera.updateProjectionMatrix(); render();
}
new ResizeObserver(fitView).observe($('sheet')); // la scheda cambia altezza con il contenuto (elenco, comandi, schede dell'oggetto)

// ---------- stanza a foto + camminata (pacchetto cifrato, caricato solo quando serve) ----------
let realApi = null, walkApi = null, realMod = null, realLoading = null, look = 'blocks';
const getReal = () => (realLoading ??= Promise.all([import('./real.js'), import('./walk.js')]).then(([r, w]) => {
  realMod = r;
  realApi = r.createReal({ renderer, roomRoot, groups, pieces, render });
  walkApi = w.createWalk({ camera, controls, canvas: renderer.domElement, render, real: realApi });
  return realApi;
}));

// ---------- viste ----------
const VIEWS = {
  pano: { pos: [3.55, 9.2, 8.2], at: [3.55, 0.6, 2.0] },
  top: { pos: [3.55, 11, 3.2], at: [3.55, 0, 2.25] },
  door: { pos: [1.4, 1.6, 4.0], at: [3.9, 1.4, 0], inside: true },
  sofa: { pos: [5.3, 1.15, 3.75], at: [5.3, 1.3, 0], inside: true },
  tv: { pos: [4.9, 1.55, 0.7], at: [3.3, 1.4, 4.5], inside: true },
  window: { pos: [6.4, 1.6, 1.5], at: [0, 1.5, 2.6], inside: true },
  split: { pos: [0.4, 1.6, 2.4], at: [7.1, 1.4, 2.0], inside: true },
};
let tween = null;
function goTo(name, instant) {
  const v = VIEWS[name];
  if (walkApi?.active()) {
    if (v.inside) { walkApi.place(v.pos, v.at, v.pos[1] < 1.3 ? 1.12 : 1.6); return; } // dal divano: seduti
    walkApi.exit();
  }
  let pos = new THREE.Vector3(...v.pos);
  let at = new THREE.Vector3(...v.at);
  if (!v.inside && camera.aspect < 1) pos = at.clone().add(pos.sub(at).multiplyScalar(Math.min(1.8, 1 / (camera.aspect * 1.25)))); // telefono in verticale: più lontano
  if (v.inside) at = pos.clone().add(at.sub(pos).normalize().multiplyScalar(0.8)); // si guarda "da dentro"
  if (instant) { camera.position.copy(pos); controls.target.copy(at); controls.update(); render(); return; }
  tween = { t0: performance.now(), p0: camera.position.clone(), a0: controls.target.clone(), p1: pos, a1: at };
}
function stepTween(now) {
  if (!tween) return;
  const k = Math.min(1, (now - tween.t0) / 600), e = k * k * (3 - 2 * k);
  camera.position.lerpVectors(tween.p0, tween.p1, e);
  controls.target.lerpVectors(tween.a0, tween.a1, e);
  controls.update();
  render();
  if (k >= 1) tween = null;
}

// ---------- quadri ----------
const objs = new Map(); // id -> { group, box, outline, mat }
const loader = new THREE.TextureLoader();
const sideMat = new THREE.MeshStandardMaterial({ color: '#e7e4dd', roughness: 0.9 });

const BRIGHT = 0.92; // il quadro stampato sulla parete fotografata è un po' meno brillante dello schermo
function frontMaterial(p) {
  const real = look === 'real';
  const m = real ? new THREE.MeshBasicMaterial({ toneMapped: false }) : new THREE.MeshStandardMaterial({ roughness: 0.7 });
  if (real) m.color.setScalar(BRIGHT);
  const base = real ? m.color.clone() : null;
  if (p.img) {
    m.map = null; m.color.set('#888');
    loader.load(p.img, (t) => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; m.map = t; if (real) m.color.copy(base); else m.color.set('#ffffff'); m.needsUpdate = true; render(); });
  } else {
    m.map = (real && realApi?.art(p.id)) || artTexture(p.art || ['#999', '#ccc', '#666']);
  }
  return m;
}
function clampP(p) {
  const w = WALLS[p.wall];
  p.u = Math.min(Math.max(p.u, p.w / 2), w.len - p.w / 2);
  p.y = Math.min(Math.max(p.y, p.h / 2), ROOM.H - 0.1 - p.h / 2);
}
function place(p) {
  const o = objs.get(p.id);
  clampP(p);
  if (o.group.parent !== groups[p.wall]) groups[p.wall].add(o.group);
  o.group.position.set(p.u, p.y, DEPTH / 2 + 0.002);
  render();
}
let shadowTex = null;
function shadowTexture() { // ombra morbida sotto e a destra del quadro (luce dal soffitto)
  if (shadowTex) return shadowTex;
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  for (let i = 0; i < 14; i++) {
    const m = 6 + i * 1.8;
    g.fillStyle = 'rgba(0,0,0,0.045)';
    g.beginPath();
    if (g.roundRect) g.roundRect(m, m, 64 - 2 * m, 64 - 2 * m, 4); else g.rect(m, m, 64 - 2 * m, 64 - 2 * m); // roundRect manca nei Safari più vecchi
    g.fill();
  }
  shadowTex = new THREE.CanvasTexture(c);
  shadowTex.colorSpace = THREE.SRGBColorSpace;
  return shadowTex;
}
function makeObj(p) {
  const group = new THREE.Group();
  group.userData.keep = true; // i quadri restano visibili cambiando aspetto
  const front = frontMaterial(p);
  const bx = new THREE.Mesh(new THREE.BoxGeometry(p.w, p.h, DEPTH), [sideMat, sideMat, sideMat, sideMat, front, sideMat]);
  bx.userData.pid = p.id;
  const outline = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(p.w + 0.02, p.h + 0.02, DEPTH + 0.01)), new THREE.LineBasicMaterial({ color: '#ff8a3d' }));
  outline.visible = false;
  group.add(bx, outline);
  let shadow = null;
  if (look === 'real') {
    const grow = 0.16;
    shadow = new THREE.Mesh(new THREE.PlaneGeometry(p.w + grow, p.h + grow), new THREE.MeshBasicMaterial({ map: shadowTexture(), transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
    shadow.position.set(0.012, -0.02, -DEPTH / 2 - 0.0015);
    shadow.renderOrder = 1;
    group.add(shadow);
  }
  objs.set(p.id, { group, box: bx, outline, front, shadow });
  place(p);
}
function removeObj(id) {
  const o = objs.get(id);
  if (!o) return;
  o.group.parent?.remove(o.group);
  o.box.geometry.dispose(); o.outline.geometry.dispose();
  if (o.shadow) { o.shadow.geometry.dispose(); o.shadow.material.dispose(); }
  if (!(realApi && o.front.map === realApi.art(id))) o.front.map?.dispose(); // la foto del pacchetto è condivisa: non si butta
  o.front.dispose();
  objs.delete(id);
}
function rebuild(p) { removeObj(p.id); makeObj(p); if (selected === p.id) setOutline(true); }
paintings.forEach(makeObj);

// ---------- oggetti di prova (tavolo, sedia, tappeto...) ----------
function viewRay() { // dove guarda la camera (con la scheda aperta e' il centro di quello che si vede, vedi fitView)
  camera.getWorldDirection(ray.ray.direction); ray.ray.origin.copy(camera.position);
  return ray;
}
const objApi = createObjects({ scene, camera, render, showErr, select: (id) => select(id), frame: (id) => { const o = objApi.get(id); if (o) { fitView(); frameAt(pv.set(o.x, o.h / 2, o.z)); } }, selected: () => selected, refresh: () => refreshPanels(), openTab: (n) => openTab(n), toDataUrl: (f, max) => toDataUrl(f, max), viewRay });

// ---------- selezione e pannelli ----------
let selected = null, step = 0.05;
const byId = (id) => paintings.find((p) => p.id === id);
function setOutline(on) { const o = objs.get(selected); if (o) { o.outline.visible = on; render(); } else if (selected) objApi.setOutline(selected, on); }
function select(id) {
  setOutline(false);
  if (id !== selected) $('sheet').scrollTop = 0;
  selected = id;
  setOutline(true);
  refreshPanels();
  if (id) openTab('paintings');
  const ob = id && objApi.get(id), pq = id && objs.get(id);
  const pt = ob ? pv.set(ob.x, ob.h / 2, ob.z) : pq ? pq.group.getWorldPosition(pv) : null;
  if (pt) { fitView(); if (!inViewAt(pt)) frameAt(pt); } // quello che scegli resta visibile sopra la scheda
}
const pv = new THREE.Vector3(), pw = new THREE.Vector3();
function inViewAt(p) { // il punto e' davanti alla camera e nella parte di schermo che non e' coperta dalla scheda?
  pw.copy(p).applyMatrix4(camera.matrixWorldInverse);
  if (pw.z > -0.1) return false;
  pw.copy(p).project(camera);
  const H = window.innerHeight, sh = $('sheet'), lo = -1 + (2 * (sh.hidden ? 0 : sh.offsetHeight)) / H, m = 0.12 * (1 - lo);
  return Math.abs(pw.x) < 0.88 && pw.y > lo + m && pw.y < 1 - m;
}
function frameAt(p) { // punta la vista su un punto: in camminata gira lo sguardo, altrimenti sposta il punto guardato
  if (walkApi?.active()) walkApi.lookAt(p.x, p.y, p.z);
  else { controls.target.copy(p); controls.update(); }
  render();
}
const cm = (v) => Math.round(v * 100);
function info(p) {
  const w = WALLS[p.wall];
  return `${w.name} · centro a ${cm(w.fromU(p.u))} cm dall'${w.corner} · bordo basso a ${cm(p.y - p.h / 2)} cm da terra · ${cm(p.w)}×${cm(p.h)} cm`;
}
function refreshPanels() {
  const list = $('plist');
  list.replaceChildren();
  for (const p of paintings) {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = p.name;
    const sm = document.createElement('small');
    sm.textContent = `${WALLS[p.wall].name} · ${cm(p.w)}×${cm(p.h)} cm`;
    b.append(sm);
    if (p.id === selected) b.setAttribute('aria-current', 'true');
    b.onclick = () => select(p.id);
    li.append(b);
    list.append(li);
  }
  objApi.renderList($('olist'), selected, select);
  const p = byId(selected), ob = objApi.get(selected);
  $('editor').hidden = !p;
  $('oeditor').hidden = !ob;
  $('lists').hidden = !!(p || ob); // con un elemento scelto l'elenco lascia spazio ai comandi
  $('back').hidden = !(p || ob);
  $('sheet').classList.toggle('compact', !!ob); // i comandi dell'oggetto stanno in una scheda piu' bassa: la stanza resta visibile
  $('sheet').classList.toggle('tall', !$('obj-form').hidden && !$('obj-form').closest('[data-panel]').hidden); // il modulo del nuovo oggetto ha bisogno di piu' spazio
  if (p) { $('e-name').textContent = p.name; $('e-info').textContent = info(p); }
  if (ob) objApi.syncEditor(ob);
}
let lastTab = null;
function openTab(name) {
  $('sheet').hidden = false;
  document.querySelectorAll('[data-panel]').forEach((el) => { el.hidden = el.dataset.panel !== name; });
  if (name !== lastTab) { $('sheet').scrollTop = 0; lastTab = name; } // cambiando scheda si riparte dall'alto
  refreshPanels();
}
document.querySelectorAll('.bar [data-tab]').forEach((b) => { b.onclick = () => openTab(b.dataset.tab); });
$('sheet-close').onclick = () => { $('sheet').hidden = true; };
document.querySelectorAll('[data-view]').forEach((b) => { b.onclick = () => { goTo(b.dataset.view); $('sheet').hidden = true; }; });
document.querySelectorAll('[data-step]').forEach((b) => {
  b.onclick = () => {
    step = Number(b.dataset.step) / 100;
    document.querySelectorAll('[data-step]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
  };
});
document.querySelectorAll('[data-nudge]').forEach((b) => {
  b.onclick = () => {
    const p = byId(selected);
    if (!p) return;
    const d = b.dataset.nudge;
    if (d === 'left') p.u -= step; if (d === 'right') p.u += step;
    if (d === 'up') p.y += step; if (d === 'down') p.y -= step;
    place(p); save(); refreshPanels();
  };
});
$('back').onclick = () => select(null);
$('e-rot').onclick = () => { const p = byId(selected); if (!p) return; [p.w, p.h] = [p.h, p.w]; rebuild(p); place(p); save(); refreshPanels(); };
$('e-del').onclick = () => {
  const p = byId(selected);
  if (!p || !confirm(`Eliminare "${p.name}" dal salotto?`)) return;
  removeObj(p.id);
  paintings = paintings.filter((x) => x !== p);
  selected = null;
  save(); refreshPanels(); render();
};
$('reset').onclick = () => {
  if (!confirm('Ripristinare i quadri iniziali? I quadri aggiunti da te verranno rimossi.')) return;
  [...objs.keys()].forEach(removeObj);
  paintings = defaults();
  paintings.forEach(makeObj);
  selected = null;
  try { localStorage.removeItem(KEY); } catch { /* ok */ }
  refreshPanels(); render();
};

// ---------- trascinare un quadro già selezionato ----------
const ray = new THREE.Raycaster();
const ndc = new THREE.Vector2();
function setRay(e) {
  const r = renderer.domElement.getBoundingClientRect();
  ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
}
const pickItem = () => ray.intersectObjects([...[...objs.values()].map((o) => o.box), ...objApi.pickables()], false)[0]; // quadri e oggetti: il piu' vicino
const pickWall = () => ray.intersectObjects(pieces, false)[0];
let drag = null, down = null, odrag = false;
const cv = renderer.domElement;
cv.addEventListener('pointerdown', (e) => {
  $('hint').classList.add('off');
  setRay(e);
  const hit = pickItem(), hid = hit ? hit.object.userData.pid || hit.object.userData.oid : null;
  down = { x: e.clientX, y: e.clientY, id: hid, moved: false };
  if (hit && hid === selected && hit.object.userData.oid && !walkApi?.active()) { // oggetto scelto: si trascina sul pavimento
    if (objApi.beginDrag(hid, ray)) { odrag = true; controls.enabled = false; cv.setPointerCapture(e.pointerId); }
  } else if (hit && hid === selected && !walkApi?.active()) {
    const p = byId(selected), wh = pickWall();
    drag = { off: wh && wh.object.userData.wall === p.wall ? local(wh).map((v, i) => [p.u, p.y][i] - v) : [0, 0] };
    controls.enabled = false;
    cv.setPointerCapture(e.pointerId);
  }
});
function local(wh) { const q = groups[wh.object.userData.wall].worldToLocal(wh.point.clone()); return [q.x, q.y]; }
cv.addEventListener('pointermove', (e) => {
  if (down && Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6) down.moved = true;
  if (odrag) { setRay(e); objApi.dragTo(ray); return; }
  if (!drag) return;
  setRay(e);
  const wh = pickWall();
  if (!wh) return;
  const p = byId(selected), nw = wh.object.userData.wall, [u, y] = local(wh);
  if (nw !== p.wall) { p.wall = nw; drag.off = [0, 0]; }
  p.u = u + drag.off[0]; p.y = y + drag.off[1];
  place(p);
  refreshPanels();
});
function end() {
  if (odrag) { odrag = false; controls.enabled = true; objApi.endDrag(); }
  else if (drag) { drag = null; controls.enabled = true; save(); }
  else if (down && !down.moved) select(down.id);
  down = null;
}
cv.addEventListener('pointerup', end);
cv.addEventListener('pointercancel', () => { if (odrag) { odrag = false; objApi.endDrag(); controls.enabled = true; } if (drag) { drag = null; controls.enabled = true; } down = null; });

// ---------- nuovo quadro ----------
async function toDataUrl(file, max = 1024) {
  const bmp = await createImageBitmap(file);
  const k = Math.min(1, max / Math.max(bmp.width, bmp.height));
  const c = document.createElement('canvas');
  c.width = Math.round(bmp.width * k); c.height = Math.round(bmp.height * k);
  c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
  return c.toDataURL('image/jpeg', 0.85);
}
$('add-form').onsubmit = async (e) => {
  e.preventDefault();
  const f = $('a-file').files[0];
  if (!f) return;
  const btn = e.submitter; btn.disabled = true;
  try {
    const img = await toDataUrl(f);
    setRay({ clientX: window.innerWidth / 2, clientY: window.innerHeight / 2 });
    const wh = pickWall();
    const p = { id: 'p' + Date.now().toString(36), name: $('a-name').value.trim() || 'Nuovo quadro', w: Number($('a-w').value) / 100, h: Number($('a-h').value) / 100, wall: wh ? wh.object.userData.wall : 'T', u: wh ? local(wh)[0] : 3.5, y: 1.65, img };
    paintings.push(p);
    makeObj(p);
    save();
    $('add-form').reset();
    $('a-w').value = 75; $('a-h').value = 50;
    select(p.id);
  } catch { showErr('Non riesco a leggere quella foto.'); }
  btn.disabled = false;
};

// ---------- salvare l'immagine della vista ----------
$('snap').onclick = async () => {
  const outl = [...objs.values()].map((o) => o.outline);
  const was = outl.map((o) => o.visible);
  outl.forEach((o) => { o.visible = false; });
  renderer.render(scene, camera); // subito prima della copia: il canvas non conserva l'immagine
  const blob = await new Promise((res) => cv.toBlob(res, 'image/png'));
  outl.forEach((o, i) => { o.visible = was[i]; });
  render();
  if (!blob) { showErr('Non riesco a salvare l\'immagine.'); return; }
  const file = new File([blob], 'salotto.png', { type: 'image/png' });
  try {
    if (navigator.canShare?.({ files: [file] })) { await navigator.share({ files: [file], title: 'Salotto' }); return; }
  } catch (e) { if (e && e.name === 'AbortError') return; }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = 'salotto.png'; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
};

// ---------- aspetto: blocchi / foto, camminata ----------
const MSG = {
  nokey: 'Serve la chiave della stanza: apri il link che ti ho dato, oppure incollala qui sotto.',
  badkey: 'La chiave non è quella giusta: incolla quella corretta.',
  assente: 'Il pacchetto della stanza non è ancora online: dopo il merge ci vuole qualche minuto.',
  rete: 'Non riesco a scaricare la stanza: controlla la connessione e riprova.',
  pacchetto: 'Il pacchetto della stanza è danneggiato.',
  errore: 'Non riesco ad aprire la stanza.',
};
const setStatus = (t) => { $('real-status').textContent = t || ''; };
function syncLookUi() {
  document.querySelectorAll('[data-look]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.look === look)));
  $('walk-go').hidden = look !== 'real';
  $('copy-link').hidden = !realApi?.ready; // c'e' solo con la chiave giusta (la stanza e' stata aperta)
  $('share').hidden = !realApi?.ready; // idem: il pulsante "Condividi" in alto a destra
}
async function setLook(next) {
  if (next === look) { syncLookUi(); return true; }
  if (next === 'real') {
    setStatus('Preparo…');
    const real = await getReal();
    const r = await real.load(setStatus);
    $('real-key').hidden = !(r === 'nokey' || r === 'badkey');
    if (r !== 'ok') { setStatus(MSG[r] || MSG.errore); syncLookUi(); return false; }
    setStatus('');
  }
  look = next;
  realApi?.setLook(next === 'real');
  paintings.forEach(rebuild); // i quadri cambiano materiale: illuminati nel modello a blocchi, "stampati" nella stanza a foto
  if (next !== 'real') walkApi?.exit();
  syncLookUi(); render();
  return true;
}
document.querySelectorAll('[data-look]').forEach((b) => { b.onclick = () => setLook(b.dataset.look); });
$('real-key-go').onclick = async () => {
  await getReal();
  if (!realMod.saveKey($('real-key-in').value)) { setStatus('Quella non sembra una chiave: sono 43 caratteri, senza spazi.'); return; }
  $('real-key-in').value = '';
  setLook('real');
};
// Il link con la chiave: chi lo apre vede subito la stanza a foto. L'app toglie la chiave dall'indirizzo dopo la prima apertura, quindi l'indirizzo della barra non basta: il link si ricompone qui.
const roomLink = () => { const k = realMod?.readKey?.(); return k ? `${location.origin}${location.pathname}#k=${k}` : null; };
let toastT = 0;
const toast = (t, ms = 4500) => { const h = $('hint'); h.textContent = t; h.classList.remove('off'); clearTimeout(toastT); toastT = setTimeout(() => h.classList.add('off'), ms); };
async function copyRoomLink() {
  const link = roomLink();
  if (!link) return;
  let done = false;
  try { await navigator.clipboard.writeText(link); done = true; } catch { /* provo il metodo vecchio */ }
  if (!done) {
    const t = document.createElement('textarea'); t.value = link; t.setAttribute('readonly', ''); t.style.cssText = 'position:fixed;top:0;opacity:0';
    document.body.append(t); t.select();
    try { done = document.execCommand('copy'); } catch { /* ok */ }
    t.remove();
  }
  if (!done) { prompt('Copia il link della stanza:', link); return; } // ultima strada: si copia a mano
  setStatus('Link copiato: chi lo apre vede la stanza a foto.');
  toast('Link copiato · incollalo in un messaggio ai tuoi amici');
  const b = $('copy-link'); b.textContent = 'Link copiato';
  setTimeout(() => { b.textContent = 'Copia il link della stanza'; }, 2500);
}
$('copy-link').onclick = copyRoomLink;
// "Condividi": sul telefono apre i fogli di condivisione (WhatsApp, Messaggi…); dove non c'e' (computer) copia il link.
// Nessun await prima di share(): deve partire direttamente dal tocco, altrimenti Safari lo rifiuta.
$('share').onclick = () => {
  const url = roomLink();
  if (!url) return;
  if (!navigator.share) { copyRoomLink(); return; }
  navigator.share({ title: 'Salotto 3D', text: 'Guarda il mio salotto in 3D', url })
    .catch((e) => { if (e?.name !== 'AbortError') copyRoomLink(); }); // annullato = niente; altro errore = si copia
};
$('walk-go').onclick = () => {
  if (!realApi?.ready || look !== 'real') return;
  $('sheet').hidden = true;
  walkApi.enter();
  const h = $('hint'); h.textContent = 'Joystick per muoverti · trascina per guardare · tocca un quadro o un oggetto per selezionarlo'; h.classList.remove('off');
  setTimeout(() => h.classList.add('off'), 6000);
};

// ---------- avvio ----------
resize();
goTo('pano', true);
const wallN = Object.fromEntries(Object.entries(WALLS).map(([id, w]) => [id, new THREE.Vector3(...w.N)]));
const tmp = new THREE.Vector3();
renderer.setAnimationLoop((now) => {
  stepTween(now);
  if (walkApi?.step(now)) needs = true;
  if (realApi?.update(camera)) needs = true;
  if (needs) {
    needs = false;
    for (const id in groups) { // da fuori la parete (con quello che ha attaccato) sparisce: si vede dentro la stanza
      tmp.copy(camera.position).sub(new THREE.Vector3(...WALLS[id].O));
      groups[id].visible = tmp.dot(wallN[id]) > 0;
    }
    renderer.render(scene, camera);
  }
});
if ('serviceWorker' in navigator) {
  const had = !!navigator.serviceWorker.controller; // già c'era una versione installata: questa è un aggiornamento
  navigator.serviceWorker.register('sw.js').catch(() => {});
  // al primo avvio dopo un aggiornamento si vedrebbe ancora la versione vecchia (dalla cache): si ricarica una volta sola, subito
  navigator.serviceWorker.addEventListener('controllerchange', () => { if (had && performance.now() < 20000) location.reload(); });
}
// La stanza dalle foto e' la versione di partenza: con la chiave (nel link, #k=, oppure gia' salvata nel telefono) si apre subito, senza passare dal modello a blocchi.
// Senza la chiave resta il modello a blocchi (la stanza a foto si legge solo con la chiave); il toggle Blocchi/Foto resta nel pannello Viste.
{
  const hint = $('hint');
  const say = (t, ms = 0) => { hint.textContent = t; hint.classList.remove('off'); if (ms) setTimeout(() => hint.classList.add('off'), ms); };
  const fromLink = /[#&]k=/.test(location.hash);
  let stored = false;
  try { stored = !!localStorage.getItem('salotto.key'); } catch { /* ok */ }
  if (fromLink || stored) {
    roomRoot.visible = false; // niente lampo del modello a blocchi mentre la stanza a foto si prepara
    say('Apro la tua stanza dalle foto…');
    setLook('real').then((ok) => {
      if (ok) { if (fromLink) openTab('views'); say('La tua stanza, dalle foto · prova "Cammina nella stanza"', 6000); }
      else { openTab('views'); say('La stanza dalle foto non si e\' aperta: intanto vedi il modello a blocchi', 6000); } // il motivo e' nel pannello Viste
    }).catch(() => { openTab('views'); }).finally(() => { roomRoot.visible = true; render(); });
  }
}
window.__salotto = { goTo, select, camera, controls, scene, setLook, objects: objApi, get look() { return look; }, get real() { return realApi; }, get walk() { return walkApi; } };
