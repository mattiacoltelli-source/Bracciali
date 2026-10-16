// Oggetti di prova nella stanza (tavolo, tavolino, sedia, mobile, tappeto, scatola): forme semplici a misura, che si spostano sul pavimento
// e si salvano nel telefono. Lo stato sta qui; app.js gestisce selezione, schede e tocchi sulla scena.
import * as THREE from 'three';
import { ROOM, WALLS } from './room.js';

const $ = (id) => document.getElementById(id);
const KEY = 'salotto.obj.v1', IMG = 'salotto.oimg.'; // elenco degli oggetti / foto (una chiave per foto: l'elenco resta leggero)
const cm = (v) => Math.round(v * 100);
const rad = (d) => (d * Math.PI) / 180;
const clamp = (v, a, b) => Math.min(Math.max(v, a), b);
const ACCENT = '#ff8a3d';
const LIM = { w: [0.05, 5], d: [0.05, 5], h: [0.01, 3] }; // misure ammesse, in metri

// misure di partenza (m); faces = su quali facce si puo' mettere la foto del prodotto
export const KINDS = {
  table: { label: 'Tavolo', w: 1.6, d: 0.9, h: 0.75, mat: 'rovere', round: true, faces: ['top'] },
  coffee: { label: 'Tavolino', w: 1.0, d: 0.55, h: 0.42, mat: 'noce', round: true, faces: ['top'] },
  chair: { label: 'Sedia', w: 0.45, d: 0.47, h: 0.85, mat: 'rovere', round: false, faces: [] },
  cabinet: { label: 'Mobile', w: 1.2, d: 0.4, h: 0.85, mat: 'bianco', round: false, faces: ['front', 'top'] },
  rug: { label: 'Tappeto', w: 2.0, d: 1.4, h: 0.015, mat: 'beige', round: true, faces: ['top'] },
  box: { label: 'Scatola', w: 1.0, d: 0.6, h: 1.0, mat: 'grigio', round: false, faces: ['front', 'top'] },
};
export const MATS = { rovere: ['Rovere', '#c2a47c'], noce: ['Noce', '#5e3d2a'], bianco: ['Bianco', '#e8e6df'], beige: ['Beige', '#d2c7b2'], grigio: ['Grigio', '#868a90'], nero: ['Nero', '#26262a'], rosso: ['Rosso', '#9e302b'] };
const LIGHT = 0.8; // le luci della scena sommano piu' di 1: senza questo i colori chiari escono bruciati (il rovere diventava giallo acceso)
const PHOTO_HINT = { table: 'La foto va sul piano: per esempio un marmo o un legno.', coffee: 'La foto va sul piano: per esempio un marmo o un legno.', rug: 'La foto va sopra il tappeto.', cabinet: 'Scegli se metterla davanti o sopra.', box: 'Scegli se metterla davanti o sopra.' };

// ---- misure e posizione ----
const eff = (o) => ({ w: o.w, d: o.round ? o.w : o.d, h: o.h }); // il tavolo rotondo ha un diametro solo
const sizeText = (o) => (o.round ? `Ø ${cm(o.w)} × ${cm(o.h)} cm` : `${cm(o.w)}×${cm(o.d)}×${cm(o.h)} cm`);
function half(o) { // mezza ingombro sugli assi della stanza (con la rotazione)
  const { w, d } = eff(o), a = rad(o.rot), c = Math.abs(Math.cos(a)), s = Math.abs(Math.sin(a));
  return o.round ? [w / 2, w / 2] : [(c * w + s * d) / 2, (s * w + c * d) / 2];
}
function fit(o) { const [hx, hz] = half(o); o.x = clamp(o.x, hx, ROOM.L - hx); o.z = clamp(o.z, hz, ROOM.W - hz); } // resta dentro la stanza
const wallName = (id) => { const n = WALLS[id].name; return n[0].toLowerCase() + n.slice(1); };
function gapText(o) { // le due pareti piu' vicine
  const [hx, hz] = half(o);
  const g = [['A', o.x - hx], ['W', ROOM.L - o.x - hx], ['T', o.z - hz], ['F', ROOM.W - o.z - hz]].sort((p, q) => p[1] - q[1]).slice(0, 2);
  return g.map(([id, v]) => (v < 0.005 ? `contro la ${wallName(id)}` : `a ${cm(v)} cm dalla ${wallName(id)}`)).join(' · ');
}

// ---- ombra morbida a terra (una per forma, condivisa) ----
const shadows = {};
function shadowTex(round) {
  const k = round ? 'round' : 'rect';
  if (shadows[k]) return shadows[k];
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'); g.fillStyle = 'rgba(0,0,0,0.05)';
  for (let i = 0; i < 14; i++) {
    const m = 4 + i * 2; g.beginPath();
    if (round) g.arc(32, 32, 32 - m, 0, Math.PI * 2);
    else if (g.roundRect) g.roundRect(m, m, 64 - 2 * m, 64 - 2 * m, 6); else g.rect(m, m, 64 - 2 * m, 64 - 2 * m); // roundRect manca nei Safari piu' vecchi
    g.fill();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return (shadows[k] = t);
}

// ---- foto del prodotto: ritaglio al centro per non deformarla ----
function fitTex(tex, ar) {
  const ia = tex.image.width / tex.image.height;
  if (ia > ar) { tex.repeat.set(ar / ia, 1); tex.offset.set((1 - ar / ia) / 2, 0); } else { tex.repeat.set(1, ia / ar); tex.offset.set(0, (1 - ia / ar) / 2); }
}

// ---- forme: tutto in coordinate locali, origine a terra al centro, davanti = +z ----
function build(o, tex) {
  const { w, d, h } = eff(o), g = new THREE.Group();
  const base = new THREE.Color(MATS[o.mat][1]).multiplyScalar(LIGHT);
  const main = new THREE.MeshLambertMaterial({ color: base }), dark = new THREE.MeshLambertMaterial({ color: base.clone().multiplyScalar(0.62) });
  const photo = tex ? new THREE.MeshLambertMaterial({ map: tex, color: new THREE.Color(LIGHT, LIGHT, LIGHT) }) : null;
  const top = photo && o.face === 'top' ? photo : main, front = photo && o.face === 'front' ? photo : main;
  const put = (geo, m, x, y, z) => { const e = new THREE.Mesh(geo, m); e.position.set(x, y, z); e.userData.oid = o.id; g.add(e); return e; };
  const box = (bw, bh, bd, x, y, z, m) => put(new THREE.BoxGeometry(bw, bh, bd), m, x, y, z);
  const drum = (r, ch, x, y, z, side, cap) => { // cilindro: fianco + coperchio a parte (cosi' la foto sopra esce dritta come sulle scatole)
    put(new THREE.CylinderGeometry(r, r, ch, 48, 1, true), side, x, y, z);
    put(new THREE.CircleGeometry(r, 48).rotateX(-Math.PI / 2), cap, x, y + ch / 2, z);
  };
  const m6 = (t, f) => [main, main, t, main, f, main]; // facce della scatola: +x, -x, sopra, sotto, davanti (+z), dietro
  if (photo && o.face === 'top') fitTex(tex, o.round ? 1 : w / d); else if (photo) fitTex(tex, w / h);
  switch (o.kind) {
    case 'table': case 'coffee': {
      const t = 0.03, lh = h - t;
      if (o.round) { drum(w / 2, t, 0, h - t / 2, 0, main, top); put(new THREE.CylinderGeometry(0.05, 0.05, lh, 24), dark, 0, lh / 2, 0); put(new THREE.CylinderGeometry(Math.min(0.25, w / 4), Math.min(0.25, w / 4), 0.02, 32), dark, 0, 0.01, 0); }
      else {
        box(w, t, d, 0, h - t / 2, 0, m6(top, main));
        const ix = Math.min(0.07, w / 4), iz = Math.min(0.07, d / 4);
        for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(0.05, lh, 0.05, sx * (w / 2 - ix), lh / 2, sz * (d / 2 - iz), dark);
      }
      break;
    }
    case 'chair': {
      const sh = Math.min(0.46, h * 0.55), lw = 0.035;
      box(w, 0.04, d, 0, sh - 0.02, 0, main);                                           // seduta
      box(w, h - sh, 0.03, 0, (h + sh) / 2, -d / 2 + 0.015, main);                      // schienale
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(lw, sh - 0.04, lw, sx * (w / 2 - 0.025), (sh - 0.04) / 2, sz * (d / 2 - 0.025), dark);
      break;
    }
    case 'cabinet': {
      const pl = Math.min(0.08, h / 4);
      box(w - 0.06, pl, d - 0.06, 0, pl / 2, 0, dark);                                  // zoccolo rientrato
      box(w, h - pl, d, 0, pl + (h - pl) / 2, 0, m6(top, front));
      if (!(photo && o.face === 'front')) {                                             // senza foto: anta e maniglie
        if (w >= 0.7) box(0.006, h - pl - 0.06, 0.004, 0, pl + (h - pl) / 2, d / 2 + 0.002, dark);
        for (const sx of w >= 0.7 ? [-0.05, 0.05] : [w * 0.28]) box(0.014, Math.min(0.14, h * 0.2), 0.014, sx, pl + (h - pl) * 0.55, d / 2 + 0.007, dark);
      }
      break;
    }
    case 'rug':
      if (o.round) drum(w / 2, h, 0, h / 2, 0, main, top); else box(w, h, d, 0, h / 2, 0, m6(top, main));
      break;
    default: // scatola: volume pieno, per provare l'ingombro di qualsiasi cosa
      box(w, h, d, 0, h / 2, 0, m6(top, front));
  }
  return g;
}

export function createObjects(ctx) {
  const { scene, camera, render } = ctx;
  let seq = 0, tab = 'move', drag = null, kind = 'table', ostep = 5; // ostep: passo dei tasti in cm
  const nodes = new Map(), texs = new Map();
  const newId = () => 'o' + Date.now().toString(36) + (seq++).toString(36);
  const num = (v, d) => (Number.isFinite(v) ? v : d);

  // ---- salvataggio ----
  function load() {
    try {
      const v = JSON.parse(localStorage.getItem(KEY));
      if (!Array.isArray(v)) return [];
      return v.filter((o) => o && KINDS[o.kind] && MATS[o.mat]).map((o) => {
        const K = KINDS[o.kind], r = {
          id: String(o.id), kind: o.kind, mat: o.mat, round: !!o.round && K.round,
          w: clamp(num(o.w, K.w), ...LIM.w), d: clamp(num(o.d, K.d), ...LIM.d), h: clamp(num(o.h, K.h), ...LIM.h),
          x: num(o.x, ROOM.L / 2), z: num(o.z, ROOM.W / 2), rot: num(o.rot, 0), face: K.faces.includes(o.face) ? o.face : K.faces[0] || null, img: null,
        };
        if (o.photo) { try { r.img = localStorage.getItem(IMG + r.id); } catch { /* senza foto */ } }
        fit(r); return r;
      });
    } catch { return []; }
  }
  let items = load();
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(items.map(({ img, ...r }) => ({ ...r, photo: !!img })))); return true; }
    catch { ctx.showErr('Spazio del telefono pieno: gli oggetti non vengono salvati. Togli qualche foto o oggetto.'); return false; }
  }
  function saveImg(o) {
    try { if (o.img) localStorage.setItem(IMG + o.id, o.img); else localStorage.removeItem(IMG + o.id); return true; }
    catch { o.img = null; ctx.showErr('Spazio del telefono pieno: la foto non si salva. Prova con un\'immagine piu\' piccola.'); return false; }
  }

  // ---- scena ----
  const get = (id) => items.find((o) => o.id === id) || null;
  const cur = () => get(ctx.selected());
  function texFor(o) { // la foto si carica una volta sola e il modello si rifa quando e' pronta
    if (!o.img) { texs.get(o.id)?.tex?.dispose(); texs.delete(o.id); return null; }
    let t = texs.get(o.id);
    if (!t || t.src !== o.img) {
      t?.tex?.dispose(); t = { src: o.img, tex: null }; texs.set(o.id, t);
      new THREE.TextureLoader().load(o.img, (tx) => { tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 4; if (texs.get(o.id) === t) { t.tex = tx; rebuild(o); } else tx.dispose(); });
    }
    return t.tex;
  }
  function place(o) { const n = nodes.get(o.id); if (!n) return; n.group.position.set(o.x, 0, o.z); n.group.rotation.y = rad(o.rot); render(); }
  function make(o, selected) {
    const { w, d, h } = eff(o), group = new THREE.Group();
    group.add(build(o, texFor(o)));
    if (o.kind !== 'rug') {
      const grow = 0.3, sh = new THREE.Mesh(new THREE.PlaneGeometry(w + grow, d + grow).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: shadowTex(o.round), transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
      sh.position.y = 0.004; sh.renderOrder = 1; group.add(sh);
    }
    const eg = o.round ? new THREE.EdgesGeometry(new THREE.CylinderGeometry(w / 2 + 0.01, w / 2 + 0.01, h + 0.01, 48), 30) : new THREE.EdgesGeometry(new THREE.BoxGeometry(w + 0.02, h + 0.01, d + 0.02));
    const outline = new THREE.LineSegments(eg, new THREE.LineBasicMaterial({ color: ACCENT }));
    outline.position.y = h / 2 + 0.005; outline.visible = !!selected; group.add(outline);
    scene.add(group); nodes.set(o.id, { group, outline });
    place(o);
  }
  function drop(id) {
    const n = nodes.get(id); if (!n) return;
    scene.remove(n.group);
    n.group.traverse((c) => { c.geometry?.dispose(); if (c.material) (Array.isArray(c.material) ? c.material : [c.material]).forEach((m) => m.dispose()); });
    nodes.delete(id);
  }
  function rebuild(o) { const n = nodes.get(o.id); const was = n ? n.outline.visible : false; drop(o.id); make(o, was); render(); }
  items.forEach((o) => make(o, false));

  // ---- punto del pavimento sotto un raggio / dove guarda la vista ----
  const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), hit = new THREE.Vector3(), dir = new THREE.Vector3();
  const floorPoint = (ray) => (ray.ray.intersectPlane(plane, hit) ? hit : null);
  function viewPoint(size) {
    const p = floorPoint(ctx.viewRay());
    if (p && p.x > 0 && p.x < ROOM.L && p.z > 0 && p.z < ROOM.W) return { x: p.x, z: p.z };
    camera.getWorldDirection(dir); const f = Math.hypot(dir.x, dir.z) || 1;
    const hf = 2 * Math.atan(Math.tan((camera.fov * Math.PI) / 360) * camera.aspect), k = clamp(((size || 0.5) / 2 / Math.tan(hf / 2)) * 1.15 + 0.4, 1.6, 3.6); // se non si vede il pavimento: davanti a chi guarda, tanto lontano da vederlo intero
    return { x: camera.position.x + (dir.x / f) * k, z: camera.position.z + (dir.z / f) * k };
  }
  function viewAxes() { // "avanti" e "destra" della vista, allineati alla stanza (i muri sono paralleli agli assi)
    camera.getWorldDirection(dir); let fx = dir.x, fz = dir.z;
    if (Math.hypot(fx, fz) < 0.3) { dir.set(0, 1, 0).applyQuaternion(camera.quaternion); fx = dir.x; fz = dir.z; } // dall'alto: avanti = verso l'alto dello schermo
    const f = Math.abs(fx) > Math.abs(fz) ? [Math.sign(fx), 0] : [0, Math.sign(fz) || -1];
    return { f, r: [-f[1], f[0]] };
  }

  // ---- azioni ----
  function add(k, size) {
    const K = KINDS[k], o = { id: newId(), kind: k, mat: K.mat, round: false, w: size.w, d: size.d, h: size.h, x: 0, z: 0, rot: 0, face: K.faces[0] || null, img: null };
    const p = viewPoint(Math.max(size.w, size.d)), { f } = viewAxes();
    o.x = p.x; o.z = p.z; o.rot = Math.round((Math.atan2(-f[0], -f[1]) * 180) / Math.PI + 360) % 360; // si presenta con il davanti verso di te
    fit(o); items.push(o); make(o, false); save(); render();
    ctx.select(o.id); ctx.frame(o.id); // si apre la scheda dei comandi e la vista punta sull'oggetto, sopra la scheda
  }
  function move(o, dx, dz) { o.x += dx; o.z += dz; fit(o); place(o); save(); }
  function rotate(o, deg) { o.rot = (((o.rot + deg) % 360) + 360) % 360; fit(o); place(o); save(); }
  function remove(o) { drop(o.id); texs.get(o.id)?.tex?.dispose(); texs.delete(o.id); items = items.filter((x) => x !== o); try { localStorage.removeItem(IMG + o.id); } catch { /* ok */ } save(); render(); }

  // ---- interfaccia: elenco ----
  function renderList(ul, selected, onPick) {
    ul.replaceChildren();
    for (const o of items) {
      const li = document.createElement('li'), b = document.createElement('button'), sm = document.createElement('small');
      b.type = 'button'; b.textContent = label(o); sm.textContent = sizeText(o); b.append(sm);
      if (o.id === selected) b.setAttribute('aria-current', 'true');
      b.onclick = () => onPick(o.id); li.append(b); ul.append(li);
    }
    $('o-empty').hidden = items.length > 0; $('o-clear').hidden = !items.length;
  }
  function label(o) { const same = items.filter((x) => x.kind === o.kind); return KINDS[o.kind].label + (same.length > 1 ? ` ${same.indexOf(o) + 1}` : ''); }

  // ---- interfaccia: modifica dell'oggetto scelto ----
  const press = (sel, on) => document.querySelectorAll(sel).forEach((b) => b.setAttribute('aria-pressed', String(on(b))));
  function syncInfo(o) { $('o-info').textContent = sizeText(o); $('o-gap').textContent = gapText(o); }
  function syncEditor(o) {
    const K = KINDS[o.kind];
    $('o-name').textContent = label(o); syncInfo(o);
    document.querySelectorAll('[data-otab]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.otab === tab)));
    document.querySelectorAll('[data-opanel]').forEach((p) => { p.hidden = p.dataset.opanel !== tab; });
    $('o-w').value = cm(o.w); $('o-d').value = cm(o.d); $('o-h').value = cm(o.h);
    $('o-w-l').firstChild.textContent = o.round ? 'Diametro' : 'Larghezza'; $('o-d-l').hidden = o.round;
    $('o-shape').hidden = !K.round; press('[data-shape]', (b) => (b.dataset.shape === 'round') === o.round);
    press('[data-mat]', (b) => b.dataset.mat === o.mat); $('o-mat-name').textContent = MATS[o.mat][0];
    $('o-photo-box').hidden = !K.faces.length; $('o-photo-hint').textContent = PHOTO_HINT[o.kind] || ''; $('o-face').hidden = !(o.img && K.faces.length > 1); $('o-photo-del').hidden = !o.img;
    press('[data-face]', (b) => b.dataset.face === o.face);
    document.querySelectorAll('[data-face]').forEach((b) => { b.hidden = !K.faces.includes(b.dataset.face); });
  }
  let timer = null;
  function applyDims(final) {
    const o = cur(); if (!o) return;
    const read = (id, [a, b], dflt) => { const v = parseFloat($(id).value.replace(',', '.')); return Number.isFinite(v) ? clamp(v / 100, a, b) : dflt; };
    o.w = read('o-w', LIM.w, o.w); o.d = read('o-d', LIM.d, o.d); o.h = read('o-h', LIM.h, o.h);
    fit(o); rebuild(o); save(); syncInfo(o);
    if (final) syncEditor(o);
  }
  ['o-w', 'o-d', 'o-h'].forEach((id) => {
    $(id).addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => applyDims(false), 450); }); // si vede mentre si scrive, senza scatti a ogni cifra
    $(id).addEventListener('change', () => { clearTimeout(timer); applyDims(true); });
  });
  document.querySelectorAll('[data-otab]').forEach((b) => { b.onclick = () => { tab = b.dataset.otab; const o = cur(); if (o) syncEditor(o); }; });
  document.querySelectorAll('[data-onudge]').forEach((b) => {
    b.onclick = () => {
      const o = cur(); if (!o) return;
      const { f, r } = viewAxes(), s = ostep / 100;
      const d = { up: f, down: [-f[0], -f[1]], right: r, left: [-r[0], -r[1]] }[b.dataset.onudge];
      move(o, d[0] * s, d[1] * s); syncInfo(o);
    };
  });
  $('o-step').onclick = () => { ostep = ostep === 1 ? 5 : ostep === 5 ? 20 : 1; $('o-step').textContent = `${ostep} cm`; };
  document.querySelectorAll('[data-orot]').forEach((b) => { b.onclick = () => { const o = cur(); if (o) { rotate(o, Number(b.dataset.orot)); syncInfo(o); } }; });
  $('o-here').onclick = () => {
    const o = cur(); if (!o) return;
    const p = viewPoint(); o.x = p.x; o.z = p.z; fit(o); place(o); save(); syncInfo(o);
  };
  document.querySelectorAll('[data-shape]').forEach((b) => { b.onclick = () => { const o = cur(); if (!o) return; o.round = b.dataset.shape === 'round'; fit(o); rebuild(o); save(); syncEditor(o); }; });
  document.querySelectorAll('[data-mat]').forEach((b) => { b.onclick = () => { const o = cur(); if (!o) return; o.mat = b.dataset.mat; rebuild(o); save(); syncEditor(o); }; });
  document.querySelectorAll('[data-face]').forEach((b) => { b.onclick = () => { const o = cur(); if (!o) return; o.face = b.dataset.face; rebuild(o); save(); syncEditor(o); }; });
  $('o-photo').onchange = async (e) => {
    const o = cur(), f = e.target.files[0]; e.target.value = '';
    if (!o || !f) return;
    try { o.img = await ctx.toDataUrl(f, 900); } catch { ctx.showErr('Non riesco a leggere quella foto.'); return; }
    saveImg(o); rebuild(o); save(); syncEditor(o);
  };
  $('o-photo-del').onclick = () => { const o = cur(); if (!o) return; o.img = null; saveImg(o); rebuild(o); save(); syncEditor(o); };
  $('o-copy').onclick = () => {
    const o = cur(); if (!o) return;
    const c = { ...o, id: newId(), x: o.x + 0.3, z: o.z + 0.3 }; fit(c);
    items.push(c); if (c.img) saveImg(c); make(c, false); save(); render(); ctx.select(c.id);
  };
  $('o-del').onclick = () => { const o = cur(); if (!o || !confirm(`Eliminare "${label(o)}" dalla stanza?`)) return; ctx.select(null); remove(o); ctx.refresh(); };
  $('o-clear').onclick = () => { if (!items.length || !confirm('Togliere tutti gli oggetti dalla stanza? I quadri restano.')) return; ctx.select(null); [...items].forEach(remove); ctx.refresh(); };
  $('o-empty-go').onclick = () => { ctx.openTab('add'); showAdd('object'); };

  // ---- interfaccia: nuovo oggetto ----
  function showAdd(which) {
    press('[data-add]', (b) => b.dataset.add === which);
    $('add-form').hidden = which !== 'painting'; $('obj-form').hidden = which !== 'object';
    ctx.refresh();
  }
  document.querySelectorAll('[data-add]').forEach((b) => { b.onclick = () => showAdd(b.dataset.add); });
  function pickKind(k) {
    kind = k; const K = KINDS[k];
    press('[data-kind]', (b) => b.dataset.kind === k);
    $('n-w').value = cm(K.w); $('n-d').value = cm(K.d); $('n-h').value = cm(K.h);
  }
  document.querySelectorAll('[data-kind]').forEach((b) => { b.onclick = () => pickKind(b.dataset.kind); });
  pickKind('table');
  $('obj-form').onsubmit = (e) => {
    e.preventDefault();
    const K = KINDS[kind], read = (id, [a, b], dflt) => { const v = parseFloat($(id).value.replace(',', '.')); return Number.isFinite(v) ? clamp(v / 100, a, b) : dflt; };
    add(kind, { w: read('n-w', LIM.w, K.w), d: read('n-d', LIM.d, K.d), h: read('n-h', LIM.h, K.h) });
  };

  return {
    items: () => items,
    get,
    pickables: () => { const out = []; for (const n of nodes.values()) n.group.traverse((c) => { if (c.isMesh && c.userData.oid) out.push(c); }); return out; },
    setOutline(id, on) { const n = nodes.get(id); if (n) { n.outline.visible = on; render(); } },
    renderList, syncEditor, syncInfo,
    // trascinare sul pavimento: il punto toccato resta sotto il dito
    beginDrag(id, ray) { const o = get(id), p = o && floorPoint(ray); if (!p) return false; drag = { id, dx: o.x - p.x, dz: o.z - p.z }; return true; },
    dragTo(ray) {
      const o = drag && get(drag.id), p = o && floorPoint(ray); if (!p) return;
      o.x = p.x + drag.dx; o.z = p.z + drag.dz;
      const [hx, hz] = half(o), near = 0.05; // vicino a un muro si appoggia
      if (o.x - hx < near) o.x = hx; else if (ROOM.L - o.x - hx < near) o.x = ROOM.L - hx;
      if (o.z - hz < near) o.z = hz; else if (ROOM.W - o.z - hz < near) o.z = ROOM.W - hz;
      fit(o); place(o); syncInfo(o);
    },
    endDrag() { if (drag) { drag = null; save(); } },
    dragging: () => !!drag,
  };
}
