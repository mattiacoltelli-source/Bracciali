// Scansione fotorealistica (Gaussian splatting) della stanza: caricata dal telefono, mai inviata altrove.
// I quadri si appendono toccando la parete della scansione; posizioni salvate nel sistema della scansione.
import * as THREE from 'three';
import { artTexture } from './scene.js';

const DEPTH = 0.03;
const XF_KEY = 'salotto.scan.v1';
const V = (...a) => new THREE.Vector3(...a);
const cm = (v) => Math.round(v * 100);
const $ = (id) => document.getElementById(id);

// ---- piccolo archivio nel browser per tenere il file della scansione ----
const idb = () => new Promise((res, rej) => { const r = indexedDB.open('salotto-scan', 1); r.onupgradeneeded = () => r.result.createObjectStore('kv'); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
async function idbPut(k, v) { const db = await idb(); return new Promise((res, rej) => { const t = db.transaction('kv', 'readwrite'); t.objectStore('kv').put(v, k); t.oncomplete = res; t.onerror = () => rej(t.error); }); }
async function idbGet(k) { const db = await idb(); return new Promise((res, rej) => { const q = db.transaction('kv').objectStore('kv').get(k); q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); }); }
async function idbDel(k) { const db = await idb(); return new Promise((res, rej) => { const t = db.transaction('kv', 'readwrite'); t.objectStore('kv').delete(k); t.oncomplete = res; t.onerror = () => rej(t.error); }); }

// ---- geometria: piano che passa per dei punti (autovettore più piccolo della covarianza) ----
function smallestEigenvector(a) {
  const v = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  for (let it = 0; it < 32; it++) {
    let p = 0, q = 1, max = Math.abs(a[0][1]);
    if (Math.abs(a[0][2]) > max) { p = 0; q = 2; max = Math.abs(a[0][2]); }
    if (Math.abs(a[1][2]) > max) { p = 1; q = 2; max = Math.abs(a[1][2]); }
    if (max < 1e-14) break;
    const th = (a[q][q] - a[p][p]) / (2 * a[p][q]);
    const t = Math.sign(th || 1) / (Math.abs(th) + Math.sqrt(th * th + 1));
    const c = 1 / Math.sqrt(t * t + 1), s = t * c;
    const app = a[p][p], aqq = a[q][q], apq = a[p][q];
    a[p][p] = app - t * apq; a[q][q] = aqq + t * apq; a[p][q] = a[q][p] = 0;
    for (let r = 0; r < 3; r++) if (r !== p && r !== q) { const x = a[r][p], y = a[r][q]; a[r][p] = a[p][r] = c * x - s * y; a[r][q] = a[q][r] = s * x + c * y; }
    for (let r = 0; r < 3; r++) { const x = v[r][p], y = v[r][q]; v[r][p] = c * x - s * y; v[r][q] = s * x + c * y; }
  }
  let k = 0;
  for (let i = 1; i < 3; i++) if (a[i][i] < a[k][k]) k = i;
  return V(v[0][k], v[1][k], v[2][k]).normalize();
}
export function fitPlane(pts) {
  const c = V();
  pts.forEach((p) => c.add(p));
  c.multiplyScalar(1 / pts.length);
  const m = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (const p of pts) { const d = [p.x - c.x, p.y - c.y, p.z - c.z]; for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) m[i][j] += d[i] * d[j]; }
  return { c, n: smallestEigenvector(m) };
}

// pareti verticali: l'orientamento si ricava dalla vista dall'alto (retta nel piano x-z), molto più stabile
function fitLineXZ(pts) {
  let cx = 0, cz = 0;
  pts.forEach((p) => { cx += p.x; cz += p.z; });
  cx /= pts.length; cz /= pts.length;
  let a = 0, b = 0, c = 0;
  pts.forEach((p) => { const dx = p.x - cx, dz = p.z - cz; a += dx * dx; b += dx * dz; c += dz * dz; });
  const lmin = (a + c) / 2 - Math.sqrt(((a - c) / 2) ** 2 + b * b);
  let n = Math.abs(b) > 1e-12 ? V(b, 0, lmin - a) : (a < c ? V(1, 0, 0) : V(0, 0, 1));
  n.normalize();
  return { c: V(cx, 0, cz), n };
}

export function createScan(ctx) {
  const { renderer, scene, camera, controls } = ctx;
  const cv = renderer.domElement;
  const layer = new THREE.Group(); // quadri e segni nella scansione
  layer.visible = false;
  scene.add(layer);
  const sobjs = new Map();
  const cams = {};
  let mode = 'model', mesh = null, spark = null, sparkMod = null, tool = null, tdata = null;
  let xf = { floorSet: false, bright: 0.85 };
  let stored = null;

  const status = (t) => { $('s-status').textContent = t || ''; };
  const pill = (t) => { $('tool-pill').hidden = !t; $('tool-text').textContent = t || ''; document.body.classList.toggle('tooling', !!t); if (t) $('hint').classList.add('off'); }; // durante uno strumento la barra in basso sparisce: serve tutto lo schermo
  function saveXf() {
    if (!mesh) return;
    xf = { ...xf, q: mesh.quaternion.toArray(), s: mesh.scale.x, pos: mesh.position.toArray() };
    try { localStorage.setItem(XF_KEY, JSON.stringify(xf)); } catch { /* ok */ }
  }

  // ---------- caricamento ----------
  async function loadSpark() {
    if (!sparkMod) {
      sparkMod = await import('./vendor/spark.module.min.js');
      spark = new sparkMod.SparkRenderer({ renderer, onDirty: () => ctx.render() });
      scene.add(spark);
    }
    return sparkMod;
  }
  async function attach(buf, name, restoring) {
    status('Elaboro la scansione… (può richiedere qualche secondo)');
    const { SplatMesh } = await loadSpark();
    if (mesh) { scene.remove(mesh); mesh.dispose(); mesh = null; }
    const m = new SplatMesh({ fileBytes: buf, fileName: name, raycastable: true });
    await m.initialized;
    mesh = m;
    scene.add(mesh);
    let saved = null;
    if (restoring) { try { saved = JSON.parse(localStorage.getItem(XF_KEY)); } catch { /* ok */ } }
    if (saved && saved.q) {
      xf = saved;
      mesh.quaternion.fromArray(saved.q); mesh.scale.setScalar(saved.s); mesh.position.fromArray(saved.pos);
    } else {
      xf = { floorSet: false, bright: xf.bright };
      mesh.quaternion.set(1, 0, 0, 0); // le scansioni escono quasi sempre capovolte (y verso il basso)
      const r = robust();
      const ext = Math.max(r.hi.x - r.lo.x, r.hi.y - r.lo.y, r.hi.z - r.lo.z);
      if (ext < 2 || ext > 30) mesh.scale.setScalar(8 / ext); // scala di partenza: da correggere con la misura
      recenter(false);
    }
    mesh.visible = mode === 'scan';
    const n = mesh.packedSplats?.numSplats ?? mesh.extSplats?.numSplats;
    $('s-tools').hidden = false; $('s-remove').hidden = false; $('s-reopen').hidden = true;
    $('s-bright').value = Math.round(xf.bright * 100);
    status(`Scansione pronta${n ? ` · ${(n / 1e6).toFixed(2)} milioni di punti` : ''}. Segui i passi 1 e 2 per raddrizzarla e metterla in scala.`);
    for (const p of ctx.paintings()) if (p.scan) makeS(p);
    saveXf();
    syncClean();
    cams.scan = null;
    if (mode === 'scan') { viewInside(); ctx.refreshPanels(); ctx.render(); } else setMode('scan', true);
  }
  function viewInside() {
    camera.position.set(0, 1.4, 0);
    controls.target.set(0.8, 1.4, 0);
    controls.update();
  }
  // estremi "robusti" (percentili): i punti vaganti lontani non falsano centro e dimensioni
  function robust() {
    mesh.updateMatrixWorld(true);
    const total = mesh.packedSplats?.numSplats ?? mesh.extSplats?.numSplats ?? 0;
    const stride = Math.max(1, Math.floor(total / 50000));
    const xs = [], ys = [], zs = [], v = V();
    mesh.forEachSplat((i, c) => { if (i % stride) return; v.copy(c).applyMatrix4(mesh.matrixWorld); xs.push(v.x); ys.push(v.y); zs.push(v.z); });
    const q = (a, f) => { a.sort((x, y) => x - y); return a.length ? a[Math.min(a.length - 1, Math.floor(f * a.length))] : 0; };
    return { med: V(q(xs, 0.5), q(ys, 0.5), q(zs, 0.5)), lo: V(q(xs, 0.02), q(ys, 0.02), q(zs, 0.02)), hi: V(q(xs, 0.98), q(ys, 0.98), q(zs, 0.98)) };
  }
  function recenter(view = true) {
    const r = robust();
    mesh.position.x -= r.med.x; mesh.position.z -= r.med.z; mesh.position.y -= r.lo.y;
    mesh.updateMatrixWorld(true);
    if (view) viewInside();
    saveXf(); updateAll();
  }
  async function loadFile(file) {
    if (file.type.startsWith('video/') || /\.(mp4|mov|m4v|webm|3gp|mkv)$/i.test(file.name)) {
      $('s-video-help').open = true;
      status('Questo è un video, non una scansione 3D: va prima trasformato in .ply o .spz (vedi qui sotto).');
      return;
    }
    if (file.size > 200e6 && !confirm(`Il file pesa ${Math.round(file.size / 1e6)} MB: sul telefono potrebbe bloccarsi. Provare lo stesso?`)) return;
    try {
      const buf = await file.arrayBuffer();
      await attach(buf, file.name, false);
      stored = { name: file.name, size: file.size };
      idbPut('file', { name: file.name, blob: new Blob([buf]) }).catch(() => ctx.showErr('Scansione troppo grande per essere ricordata: dovrai ricaricarla la prossima volta.'));
    } catch (e) {
      console.error(e);
      status('');
      ctx.showErr('Non riesco a leggere questa scansione. Prova con un file .ply o .spz.');
    }
  }

  // ---------- modo ----------
  function setMode(m, fresh) {
    if (m === mode || (m === 'scan' && !mesh)) return;
    cams[mode] = { p: camera.position.clone(), t: controls.target.clone() };
    endTool(true);
    mode = m;
    ctx.roomRoot.visible = m === 'model';
    layer.visible = m === 'scan';
    if (mesh) mesh.visible = m === 'scan';
    if (m === 'scan' && (fresh || !cams.scan)) viewInside();
    else if (cams[m]) { camera.position.copy(cams[m].p); controls.target.copy(cams[m].t); controls.update(); }
    document.querySelectorAll('[data-smode]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.smode === m)));
    ctx.refreshPanels();
    ctx.render();
  }

  // ---------- quadri nella scansione ----------
  function softShadow() {
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const g = c.getContext('2d');
    const gr = g.createRadialGradient(32, 32, 14, 32, 32, 32);
    gr.addColorStop(0, 'rgba(0,0,0,.9)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  }
  const shadowTex = softShadow();
  function makeS(p) {
    removeS(p.id);
    if (!p.scan) return;
    const grey = (xf.bright ?? 0.85);
    const side = new THREE.MeshBasicMaterial({ color: new THREE.Color('#d9d5cd').multiplyScalar(grey), toneMapped: false });
    const front = new THREE.MeshBasicMaterial({ color: new THREE.Color(grey, grey, grey), toneMapped: false });
    if (p.img) new THREE.TextureLoader().load(p.img, (t) => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; front.map = t; front.needsUpdate = true; ctx.render(); });
    else front.map = artTexture(p.art || ['#999', '#ccc', '#666']);
    const box = new THREE.Mesh(new THREE.BoxGeometry(p.w, p.h, DEPTH), [side, side, side, side, front, side]);
    box.userData.pid = p.id;
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(p.w * 1.3, p.h * 1.3), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, opacity: 0.4, depthWrite: false }));
    shadow.position.set(0, -0.015, -DEPTH / 2 - 0.003);
    shadow.renderOrder = 10;
    const outline = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(p.w + 0.02, p.h + 0.02, DEPTH + 0.01)), new THREE.LineBasicMaterial({ color: '#ff8a3d' }));
    outline.visible = ctx.selected() === p.id;
    const group = new THREE.Group();
    group.add(shadow, box, outline);
    layer.add(group);
    sobjs.set(p.id, { group, box, outline, front, side, shadow });
    placeS(p);
  }
  function removeS(id) {
    const o = sobjs.get(id);
    if (!o) return;
    layer.remove(o.group);
    o.box.geometry.dispose(); o.outline.geometry.dispose(); o.shadow.geometry.dispose();
    o.front.map?.dispose(); o.front.dispose(); o.side.dispose(); o.shadow.material.dispose();
    sobjs.delete(id);
  }
  // posa del quadro nel mondo: p.scan = { p, n } nel sistema della scansione
  function basis(p) {
    mesh.updateMatrixWorld(true);
    const pw = V(...p.scan.p).applyMatrix4(mesh.matrixWorld);
    const nw = V(...p.scan.n).applyQuaternion(mesh.quaternion).normalize();
    const up = V(0, 1, 0);
    let y = up.clone().sub(nw.clone().multiplyScalar(up.dot(nw)));
    if (y.lengthSq() < 1e-6) y = V(0, 0, -1); // pavimento o soffitto
    y.normalize();
    const x = new THREE.Vector3().crossVectors(y, nw).normalize(); // a destra, guardando la parete dall'interno
    return { pw, nw, x, y };
  }
  function placeS(p) {
    const o = sobjs.get(p.id);
    if (!o || !mesh || !p.scan) return;
    const b = basis(p);
    o.group.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(b.x, b.y, b.nw));
    o.group.position.copy(b.pw).addScaledVector(b.nw, DEPTH / 2 + 0.004);
    ctx.render();
  }
  const updateAll = () => { for (const p of ctx.paintings()) if (p.scan) placeS(p); };
  function setBright(v) {
    xf.bright = v;
    for (const o of sobjs.values()) { o.front.color.setScalar(v); o.side.color.set('#d9d5cd').multiplyScalar(v); }
    saveXf(); ctx.render();
  }

  // ---------- puntamento sulla scansione ----------
  const ray = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  function setRay(x, y) {
    const r = cv.getBoundingClientRect();
    ndc.set(((x - r.left) / r.width) * 2 - 1, -((y - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
  }
  function hit(x, y) {
    setRay(x, y);
    const h = ray.intersectObject(mesh, false);
    return h.length ? h[0].point.clone() : null;
  }
  function wallPlane(x, y) { // piano locale attorno al tocco: fascia larga in orizzontale, dove conta l'orientamento
    const c = hit(x, y);
    if (!c) return null;
    const pts = [c];
    for (let i = -4; i <= 4; i++) for (let j = -2; j <= 2; j++) { if (!i && !j) continue; const q = hit(x + i * 16, y + j * 24); if (q) pts.push(q); }
    if (pts.length < 10) return null;
    const robustFit = (fit) => { // due passate: scarta i punti lontani dal piano
      let f = fit(pts);
      const dist = (q) => Math.abs(q.clone().sub(f.c).dot(f.n));
      const d = pts.map(dist).sort((a, b) => a - b);
      const lim = Math.max(d[Math.floor(d.length / 2)] * 3, 1e-4);
      const keep = pts.filter((q) => dist(q) <= lim);
      return keep.length >= 8 ? fit(keep) : f;
    };
    let f = robustFit(fitPlane);
    if (xf.floorSet && Math.abs(f.n.y) < 0.7) f = robustFit(fitLineXZ); // parete verticale: conta solo la vista dall'alto
    if (f.n.dot(camera.position.clone().sub(c)) < 0) f.n.negate();
    return { p: c.clone().sub(f.n.clone().multiplyScalar(c.clone().sub(f.c).dot(f.n))), n: f.n };
  }

  // ---------- strumenti ----------
  function startTool(name, text) {
    tool = name; tdata = [];
    ctx.closeSheet();
    pill(text);
    cv.style.cursor = 'crosshair';
  }
  function endTool(silent) {
    const was = tool;
    tool = null; tdata = null;
    clearMarks();
    pill('');
    cv.style.cursor = '';
    if (!silent && was) ctx.openTab(was === 'hang' ? 'paintings' : 'scan');
  }
  const marks = [];
  function mark(pt) {
    const r = 0.012 * Math.max(0.5, camera.position.distanceTo(pt));
    const m = new THREE.Mesh(new THREE.SphereGeometry(r, 12, 8), new THREE.MeshBasicMaterial({ color: '#ff8a3d', depthTest: false }));
    m.position.copy(pt); m.renderOrder = 30;
    layer.add(m); marks.push(m); ctx.render();
  }
  function clearMarks() { marks.splice(0).forEach((m) => { layer.remove(m); m.geometry.dispose(); m.material.dispose(); }); ctx.render(); }
  function camMap(fn) { camera.position.copy(fn(camera.position.clone())); controls.target.copy(fn(controls.target.clone())); controls.update(); }

  function tapFloor(e) {
    const q = hit(e.clientX, e.clientY);
    if (!q) { ctx.showErr('Non trovo la scansione lì: tocca un punto del pavimento.'); return; }
    tdata.push(q); mark(q);
    if (tdata.length < 3) { pill(`Pavimento: punto ${tdata.length + 1} di 3`); return; }
    const [a, b, c] = tdata;
    const ab = b.clone().sub(a), ac = c.clone().sub(a), n = new THREE.Vector3().crossVectors(ab, ac);
    if (n.length() / Math.max(ab.length() * ac.length(), 1e-9) < 0.2) { tdata = []; clearMarks(); pill('Punti troppo allineati: riprova, più distanti (1 di 3)'); return; }
    n.normalize();
    if (n.dot(camera.position.clone().sub(a)) < 0) n.negate();
    const q0 = new THREE.Quaternion().setFromUnitVectors(n, V(0, 1, 0));
    const pos0 = mesh.position.clone(), local = mesh.worldToLocal(a.clone());
    mesh.quaternion.premultiply(q0);
    mesh.position.copy(pos0);
    mesh.updateMatrixWorld(true);
    const dy = mesh.localToWorld(local.clone()).y;
    mesh.position.y -= dy;
    mesh.updateMatrixWorld(true);
    camMap((x) => { x.sub(pos0).applyQuaternion(q0).add(pos0); x.y -= dy; return x; });
    xf.floorSet = true;
    saveXf(); updateAll(); ctx.save(); cleanText(); applyClean();
    status('Pavimento impostato: la scansione è dritta e il pavimento è a quota zero.');
    endTool();
  }
  function tapMeasure(e) {
    const q = hit(e.clientX, e.clientY);
    if (!q) { ctx.showErr('Non trovo la scansione lì: tocca un punto della scansione.'); return; }
    tdata.push(q); mark(q);
    if (tdata.length < 2) { pill('Misura: tocca il secondo punto'); return; }
    const d = tdata[0].distanceTo(tdata[1]);
    tool = null; pill(''); cv.style.cursor = '';
    measured = { a: tdata[0].clone(), d };
    $('s-measured').textContent = `Misurato: ${cm(d)} cm con la scala attuale. Scrivi la misura vera e premi "Imposta scala".`;
    ctx.openTab('scan');
    setTimeout(clearMarks, 4000);
  }
  let measured = null;
  function applyScale() {
    const real = Number($('s-real').value);
    if (!measured || !(real > 0)) { ctx.showErr('Prima misura due punti e scrivi la misura vera.'); return; }
    const f = real / 100 / measured.d;
    const pv = measured.a.clone();
    if (xf.floorSet) pv.y = 0;
    mesh.position.copy(pv.clone().add(mesh.position.clone().sub(pv).multiplyScalar(f)));
    mesh.scale.multiplyScalar(f);
    camMap((x) => pv.clone().add(x.sub(pv).multiplyScalar(f)));
    mesh.updateMatrixWorld(true);
    measured = null; clearMarks();
    $('s-measured').textContent = `Scala impostata (×${f.toFixed(2)}). Controlla con un'altra misura nota.`;
    saveXf(); updateAll();
  }
  function tapHang(e) {
    const p = ctx.byId(ctx.selected());
    if (!p) { endTool(); return; }
    const w = wallPlane(e.clientX, e.clientY);
    if (!w) { ctx.showErr('Non trovo la parete lì: tocca un punto della scansione.'); return; }
    mesh.updateMatrixWorld(true);
    const inv = mesh.quaternion.clone().invert();
    p.scan = { p: mesh.worldToLocal(w.p.clone()).toArray(), n: w.n.clone().applyQuaternion(inv).toArray() };
    if (!sobjs.has(p.id)) makeS(p); else placeS(p);
    ctx.save();
    ctx.refreshPanels();
    pill('Quadro appeso. Tocca un altro punto per spostarlo');
  }
  function tapSelect(e) {
    setRay(e.clientX, e.clientY);
    const h = ray.intersectObjects([...sobjs.values()].map((o) => o.box), false)[0];
    ctx.select(h ? h.object.userData.pid : null);
  }

  // ---------- tocchi sul canvas ----------
  let down = null;
  cv.addEventListener('pointerdown', (e) => { down = mode === 'scan' && mesh ? { x: e.clientX, y: e.clientY, moved: false } : null; });
  cv.addEventListener('pointermove', (e) => { if (down && Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6) down.moved = true; });
  cv.addEventListener('pointerup', (e) => {
    const d = down; down = null;
    if (!d || d.moved || mode !== 'scan' || !mesh) return;
    if (tool === 'floor') tapFloor(e);
    else if (tool === 'measure') tapMeasure(e);
    else if (tool === 'hang') tapHang(e);
    else if (tool === 'erase') tapErase(e);
    else tapSelect(e);
  });

  // ---------- pulizia: nebbia, taglio sotto il pavimento, gomma per i punti per aria ----------
  const FOG_MIN = 0.5 / 255, MAX_ERASE = 40;
  let cutEdit = null, cutSdf = null, eraseEdit = null;
  function applyClean() {
    if (!spark || !sparkMod) return;
    spark.minAlpha = FOG_MIN + 0.3 * (xf.fog || 0) ** 2;
    if (!cutEdit) {
      cutEdit = new sparkMod.SplatEdit({ rgbaBlendMode: sparkMod.SplatEditRgbaBlendMode.MULTIPLY });
      cutSdf = new sparkMod.SplatEditSdf({ type: sparkMod.SplatEditSdfType.PLANE, opacity: 0 });
      cutSdf.rotation.x = -Math.PI / 2; // normale verso l'alto
      cutEdit.add(cutSdf);
      scene.add(cutEdit);
    }
    cutEdit.visible = !!xf.floorSet && (xf.cut || 0) > 0;
    cutSdf.position.y = -(xf.cut || 0) / 100;
    ctx.render();
  }
  function buildErase() {
    if (eraseEdit) { eraseEdit.parent?.remove(eraseEdit); eraseEdit = null; }
    const list = xf.erase || [];
    if (mesh && sparkMod && list.length) {
      eraseEdit = new sparkMod.SplatEdit({ rgbaBlendMode: sparkMod.SplatEditRgbaBlendMode.MULTIPLY });
      for (const [x, y, z, r] of list) {
        const d = new sparkMod.SplatEditSdf({ type: sparkMod.SplatEditSdfType.SPHERE, radius: r, opacity: 0 });
        d.position.set(x, y, z);
        eraseEdit.add(d);
      }
      mesh.add(eraseEdit);
    }
    ctx.render();
  }
  function cleanText() {
    $('s-cut-v').textContent = !xf.floorSet ? 'Spento. Serve il passo 1 (pavimento).' : (xf.cut || 0) > 0 ? `Tolgo ciò che sta più di ${xf.cut} cm sotto il pavimento.` : 'Spento. Alza piano piano finché spariscono i riflessi; se il pavimento si buca, abbassa.';
    const n = (xf.erase || []).length;
    $('s-erased').textContent = n ? `Zone cancellate: ${n}.` : '';
  }
  function syncClean() { // dopo aver caricato o riaperto una scansione
    $('s-fog').value = Math.round((xf.fog || 0) * 100);
    $('s-cut').value = xf.cut || 0;
    cleanText(); applyClean(); buildErase();
  }
  function tapErase(e) {
    const q = hit(e.clientX, e.clientY);
    if (!q) { ctx.showErr('Non trovo punti lì: tocca un punto sospeso.'); return; }
    if ((xf.erase || []).length >= MAX_ERASE) { ctx.showErr('Troppe zone cancellate: annullane qualcuna.'); return; }
    mesh.updateMatrixWorld(true);
    const l = mesh.worldToLocal(q.clone());
    (xf.erase ||= []).push([l.x, l.y, l.z, Number($('s-eraser').value) / 100 / mesh.scale.x]);
    saveXf(); buildErase(); cleanText();
    pill(`Cancellate ${xf.erase.length} zone · tocca un altro punto o premi Fine`);
  }

  // ---------- pannello ----------
  $('s-file').onchange = (e) => { const f = e.target.files[0]; if (f) loadFile(f); e.target.value = ''; };
  $('s-reopen').onclick = async () => {
    try { const r = await idbGet('file'); if (r) await attach(await r.blob.arrayBuffer(), r.name, true); }
    catch (e) { console.error(e); ctx.showErr('Non riesco a riaprire la scansione salvata.'); }
  };
  $('s-remove').onclick = async () => {
    if (!confirm('Rimuovere la scansione dal telefono? I quadri appesi lì perdono la posizione.')) return;
    setMode('model');
    if (mesh) { scene.remove(mesh); mesh.dispose(); mesh = null; }
    for (const id of [...sobjs.keys()]) removeS(id);
    for (const p of ctx.paintings()) delete p.scan;
    await idbDel('file').catch(() => {});
    try { localStorage.removeItem(XF_KEY); } catch { /* ok */ }
    stored = null; xf = { floorSet: false, bright: 0.85 };
    eraseEdit = null; applyClean();
    $('s-tools').hidden = true; $('s-remove').hidden = true; status('Scansione rimossa.');
    ctx.save(); ctx.refreshPanels(); ctx.render();
  };
  document.querySelectorAll('[data-smode]').forEach((b) => { b.onclick = () => setMode(b.dataset.smode); });
  const rot = (axis, deg) => { mesh.quaternion.premultiply(new THREE.Quaternion().setFromAxisAngle(axis, (deg * Math.PI) / 180)); xf.floorSet = false; recenter(true); ctx.save(); };
  $('s-flip').onclick = () => mesh && rot(V(1, 0, 0), 180);
  $('s-roll').onclick = () => mesh && rot(V(1, 0, 0), 90);
  $('s-floor').onclick = () => mesh && startTool('floor', 'Pavimento: punto 1 di 3 (guarda in basso finché vedi il pavimento)');
  $('s-measure').onclick = () => mesh && startTool('measure', 'Misura: tocca il primo punto');
  $('s-apply').onclick = applyScale;
  document.querySelectorAll('[data-real]').forEach((b) => { b.onclick = () => { $('s-real').value = b.dataset.real; }; });
  $('s-bright').oninput = (e) => setBright(Number(e.target.value) / 100);
  $('s-fog').oninput = (e) => { xf.fog = Number(e.target.value) / 100; applyClean(); };
  $('s-fog').onchange = () => saveXf();
  $('s-cut').oninput = (e) => { xf.cut = Number(e.target.value); cleanText(); applyClean(); };
  $('s-cut').onchange = () => saveXf();
  $('s-erase').onclick = () => mesh && startTool('erase', 'Tocca i punti sospesi da cancellare');
  $('s-undo').onclick = () => { if (xf.erase?.length) { xf.erase.pop(); saveXf(); buildErase(); cleanText(); } };
  $('s-undoall').onclick = () => { if (xf.erase?.length && confirm('Ripristinare tutti i punti cancellati?')) { xf.erase = []; saveXf(); buildErase(); cleanText(); } };
  $('tool-done').onclick = () => endTool();

  return {
    active: () => mode === 'scan' && !!mesh,
    setMode,
    async onOpen() {
      if (mesh) return;
      try {
        const r = await idbGet('file');
        if (r) { stored = r; $('s-reopen').hidden = false; $('s-reopen').textContent = `Riapri l'ultima scansione: ${r.name} (${(r.blob.size / 1e6).toFixed(0)} MB)`; }
      } catch { /* niente archivio */ }
    },
    hideOutlines(hide) { for (const [pid, o] of sobjs) o.outline.visible = !hide && pid === ctx.selected(); },
    onSelect(id) { for (const [pid, o] of sobjs) o.outline.visible = pid === id; ctx.render(); },
    info(p) {
      if (!p.scan) return 'Non ancora appeso nella scansione: premi "Appendi nella scansione".';
      const b = basis(p);
      const h = xf.floorSet ? `bordo basso a ${cm(b.pw.y - p.h / 2)} cm da terra` : 'pavimento non impostato (passo 1)';
      return `Nella scansione · ${h} · ${cm(p.w)}×${cm(p.h)} cm`;
    },
    nudge(p, d, step) {
      if (!p.scan) return;
      const b = basis(p);
      const mv = d === 'left' ? b.x.clone().multiplyScalar(-step) : d === 'right' ? b.x.clone().multiplyScalar(step) : d === 'up' ? b.y.clone().multiplyScalar(step) : b.y.clone().multiplyScalar(-step);
      p.scan.p = mesh.worldToLocal(b.pw.clone().add(mv)).toArray();
      placeS(p); ctx.save();
    },
    rebuild(p) { if (mesh && p.scan) makeS(p); },
    remove(id) { removeS(id); },
    reset() { for (const id of [...sobjs.keys()]) removeS(id); },
    startHang() {
      if (!mesh || !ctx.byId(ctx.selected())) return;
      startTool('hang', 'Tocca la parete dove appendere il quadro');
    },
  };
}
