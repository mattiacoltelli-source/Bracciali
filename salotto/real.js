// Salotto "a foto": la stanza ricostruita dalle foto reali, caricata da un pacchetto cifrato (AES-GCM).
// Il pacchetto sta nel repo (pubblico) ma si legge solo con la chiave, che sta nel telefono: pareti, pavimento e mobili sono foto di casa.
import * as THREE from 'three';
import { ROOM, WALLS } from './room.js';

const PACK_URL = 'pack/salotto.bin?v=2'; // alzare il numero quando il pacchetto cambia: la cache del telefono lo rinnova
const KEY_STORE = 'salotto.key';
const b64u = (s) => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), (c) => c.charCodeAt(0));

let memKey = null;
// La chiave arriva nel frammento del link (#k=...): non viaggia mai verso il server. Si salva nel telefono e si toglie dall'indirizzo.
export function readKey() {
  const m = /[#&]k=([A-Za-z0-9_-]+)/.exec(location.hash);
  if (m) {
    memKey = m[1];
    try { localStorage.setItem(KEY_STORE, m[1]); } catch { /* resta in memoria */ }
    try { history.replaceState(null, '', location.pathname + location.search); } catch { /* ok */ }
    return m[1];
  }
  if (memKey) return memKey;
  try { return localStorage.getItem(KEY_STORE); } catch { return null; }
}
export function saveKey(k) {
  const v = String(k || '').trim().replace(/^.*k=/, '');
  if (!/^[A-Za-z0-9_-]{43}$/.test(v)) return false;
  memKey = v;
  try { localStorage.setItem(KEY_STORE, v); } catch { /* ok */ }
  return true;
}
export const hasKey = () => !!readKey();

async function fetchPack(onStatus) {
  onStatus?.('Scarico la stanza…');
  let res;
  try { res = await fetch(PACK_URL); } catch { throw new Error('rete'); }
  if (!res.ok) throw new Error(res.status === 404 ? 'assente' : 'rete');
  if (!res.body) return new Uint8Array(await res.arrayBuffer());
  // la lunghezza dichiarata serve solo per la percentuale (con la compressione può non coincidere)
  const len = res.headers.get('content-encoding') ? 0 : Number(res.headers.get('content-length')) || 0;
  const chunks = [];
  let got = 0;
  const rd = res.body.getReader();
  try {
    for (;;) {
      const { done, value } = await rd.read();
      if (done) break;
      chunks.push(value); got += value.length;
      if (len && got <= len) onStatus?.(`Scarico la stanza… ${Math.round((got / len) * 100)}%`);
    }
  } catch { throw new Error('rete'); }
  const out = new Uint8Array(got);
  let o = 0;
  for (const c of chunks) { out.set(c, o); o += c.length; }
  return out;
}

async function decryptPack(u8, keyB64) {
  if (u8.length < 40 || String.fromCharCode(u8[0], u8[1], u8[2], u8[3]) !== 'SLT1') throw new Error('pacchetto');
  let key;
  try { key = await crypto.subtle.importKey('raw', b64u(keyB64), 'AES-GCM', false, ['decrypt']); } catch { throw new Error('chiave'); }
  try { return await crypto.subtle.decrypt({ name: 'AES-GCM', iv: u8.subarray(4, 16) }, key, u8.subarray(16)); } catch { throw new Error('chiave'); }
}

const FACE = { // origine, destra, su (dal fuori) di ogni faccia di una scatola
  '+z': (a, b) => ({ o: [a[0], a[1], b[2]], r: [1, 0, 0], u: [0, 1, 0], w: b[0] - a[0], h: b[1] - a[1], n: [0, 0, 1], sh: 0.86 }),
  '-z': (a, b) => ({ o: [b[0], a[1], a[2]], r: [-1, 0, 0], u: [0, 1, 0], w: b[0] - a[0], h: b[1] - a[1], n: [0, 0, -1], sh: 0.7 }),
  '+x': (a, b) => ({ o: [b[0], a[1], b[2]], r: [0, 0, -1], u: [0, 1, 0], w: b[2] - a[2], h: b[1] - a[1], n: [1, 0, 0], sh: 0.78 }),
  '-x': (a, b) => ({ o: [a[0], a[1], a[2]], r: [0, 0, 1], u: [0, 1, 0], w: b[2] - a[2], h: b[1] - a[1], n: [-1, 0, 0], sh: 0.78 }),
  '+y': (a, b) => ({ o: [a[0], b[1], b[2]], r: [1, 0, 0], u: [0, 0, -1], w: b[0] - a[0], h: b[2] - a[2], n: [0, 1, 0], sh: 1.0 }),
};

// scatola con gli spigoli smussati (come RoundedBoxGeometry di three, senza dipendenze): per il divano
function roundedGeo(w, h, d, r) {
  r = Math.min(w / 2, h / 2, d / 2, r);
  const n = 5; // dispari: la fascia centrale resta piatta
  const g = new THREE.BoxGeometry(1, 1, 1, n, n, n);
  const pos = g.attributes.position, nor = g.attributes.normal;
  const half = 0.5 / n, v = new THREE.Vector3(), q = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i);
    q.set(v.x - Math.sign(v.x) * half, v.y - Math.sign(v.y) * half, v.z - Math.sign(v.z) * half).normalize();
    pos.setXYZ(i, (w / 2 - r) * Math.sign(v.x) + q.x * r, (h / 2 - r) * Math.sign(v.y) + q.y * r, (d / 2 - r) * Math.sign(v.z) + q.z * r);
    nor.setXYZ(i, q.x, q.y, q.z);
  }
  return g;
}
// tinta unita con luce "cotta" nei vertici: più chiaro sopra, più scuro sui fianchi e in basso
function roundedMesh(b) {
  const [a, c] = [b.min, b.max];
  const g = roundedGeo(c[0] - a[0], c[1] - a[1], c[2] - a[2], b.round);
  const pos = g.attributes.position, nor = g.attributes.normal;
  const base = new THREE.Color(b.color), col = new Float32Array(pos.count * 3), hh = c[1] - a[1];
  for (let i = 0; i < pos.count; i++) {
    const nx = nor.getX(i), ny = nor.getY(i), nz = nor.getZ(i);
    const k = (0.7 + 0.36 * Math.max(0, ny) + 0.08 * Math.max(0, -nz) + 0.05 * Math.max(0, -nx)) * (0.8 + 0.2 * Math.min(1, (pos.getY(i) + hh / 2) / 0.2));
    col[i * 3] = Math.min(1, base.r * k); col[i * 3 + 1] = Math.min(1, base.g * k); col[i * 3 + 2] = Math.min(1, base.b * k);
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, toneMapped: false }));
  m.position.set((a[0] + c[0]) / 2, (a[1] + c[1]) / 2, (a[2] + c[2]) / 2);
  return m;
}

// oggetti morbidi inclinati (cuscini): scatola smussata centrata, ruotata
function softItem(it) {
  const h = [it.size[0] / 2, it.size[1] / 2, it.size[2] / 2];
  const m = roundedMesh({ min: [-h[0], -h[1], -h[2]], max: h, color: it.color, round: it.round || 0.05 });
  m.position.set(...it.c);
  m.rotation.set(0, it.ry || 0, it.rz || 0, 'YXZ');
  return m;
}

function ceilingTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(64, 64, 8, 64, 64, 90);
  gr.addColorStop(0, '#f5f3ee'); gr.addColorStop(1, '#e4e1da');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function createReal(ctx) {
  const { renderer, roomRoot, groups, pieces, render } = ctx;
  const group = new THREE.Group();
  group.visible = false;
  roomRoot.add(group);
  // il modello a blocchi si nasconde quando si guarda la stanza a foto (i quadri restano); travi, binari e cornicione si rifanno qui
  const gset = new Set(Object.values(groups));
  const blockTop = roomRoot.children.filter((o) => o !== group && !gset.has(o) && !o.userData.keep);
  const blockWall = Object.values(groups).flatMap((g) => g.children.filter((o) => !o.userData.keep));
  const wallMeshes = [];
  const arts = {};
  let pack = null, loading = null, on = false;
  const loader = new THREE.TextureLoader();
  const aniso = Math.min(8, renderer.capabilities.getMaxAnisotropy());

  const tex = async (blob) => {
    const url = URL.createObjectURL(blob);
    try {
      const t = await loader.loadAsync(url);
      t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = aniso;
      return t;
    } finally { URL.revokeObjectURL(url); }
  };

  // travi (posizioni e misure dalle foto), binari con i faretti e cornicione: non illuminati, con una sfumatura fissa per faccia
  function buildCeilingStuff(parent) {
    const base = new THREE.Color('#efede8');
    const mk = (k) => new THREE.MeshBasicMaterial({ color: base.clone().multiplyScalar(k), toneMapped: false });
    const black = new THREE.MeshBasicMaterial({ color: '#0f0f11', toneMapped: false });
    const warm = new THREE.MeshBasicMaterial({ color: '#fff0cc', toneMapped: false });
    const BEAM = { w: 0.33, drop: 0.14 };
    for (const cx of [2.38, 5.22]) {
      const beam = new THREE.Mesh(new THREE.BoxGeometry(BEAM.w, BEAM.drop, ROOM.W), [mk(0.86), mk(0.82), mk(0.97), mk(0.97), mk(0.9), mk(0.9)]);
      beam.position.set(cx, ROOM.H - BEAM.drop / 2, ROOM.W / 2);
      const rail = new THREE.Mesh(new THREE.BoxGeometry(0.028, 0.028, ROOM.W - 0.9), black);
      rail.position.set(cx, ROOM.H - BEAM.drop - 0.014, ROOM.W / 2);
      parent.add(beam, rail);
      for (let i = 0; i < 4; i++) {
        const z = 0.95 + i * 0.85;
        const spot = new THREE.Mesh(new THREE.CylinderGeometry(0.038, 0.034, 0.13, 14), black);
        spot.position.set(cx, ROOM.H - BEAM.drop - 0.09, z);
        spot.rotation.x = i % 2 ? 0.5 : -0.5;
        const tip = new THREE.Mesh(new THREE.CircleGeometry(0.03, 14), warm);
        tip.position.set(0, -0.0655, 0); tip.rotation.x = Math.PI / 2;
        spot.add(tip);
        parent.add(spot);
      }
    }
    const cm = mk(0.96);
    for (const [w, x, z, ry] of [[ROOM.L, ROOM.L / 2, 0.035, 0], [ROOM.L, ROOM.L / 2, ROOM.W - 0.035, 0], [ROOM.W, 0.035, ROOM.W / 2, Math.PI / 2], [ROOM.W, ROOM.L - 0.035, ROOM.W / 2, Math.PI / 2]]) {
      const c = new THREE.Mesh(new THREE.BoxGeometry(w, 0.1, 0.07), cm);
      c.position.set(x, ROOM.H - 0.05, z); c.rotation.y = ry;
      parent.add(c);
    }
  }

  async function build(plain, onStatus) {
    const dv = new DataView(plain);
    const mlen = dv.getUint32(0, true);
    const man = JSON.parse(new TextDecoder().decode(new Uint8Array(plain, 4, mlen)));
    const base = 4 + mlen;
    const T = {};
    const stage = new THREE.Group(), walls = [];
    const names = Object.keys(man.images);
    let k = 0;
    for (const name of names) {
      const im = man.images[name];
      onStatus?.(`Preparo le foto… ${++k}/${names.length}`);
      T[name] = await tex(new Blob([new Uint8Array(plain, base + im.o, im.n)], { type: im.t }));
    }
    const basic = (map, o = {}) => new THREE.MeshBasicMaterial({ map, toneMapped: false, ...o });
    // pareti: un piano per parete, nel riferimento della parete (u lungo, y in alto, z verso l'interno)
    for (const id of Object.keys(WALLS)) {
      if (!man.walls[id]) continue;
      const w = WALLS[id];
      const m = new THREE.Mesh(new THREE.PlaneGeometry(w.len, ROOM.H), basic(T[man.walls[id]]));
      m.position.set(w.len / 2, ROOM.H / 2, 0);
      m.userData.wall = id;
      m.visible = false;
      walls.push(m);
    }
    // pavimento (l'immagine ha in alto la parete TV) e soffitto
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.L, ROOM.W), basic(T[man.floor]));
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(ROOM.L / 2, 0, ROOM.W / 2);
    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.L, ROOM.W), basic(ceilingTexture()));
    ceil.rotation.x = Math.PI / 2;
    ceil.position.set(ROOM.L / 2, ROOM.H, ROOM.W / 2);
    stage.add(floor, ceil);
    // mobili: tutte le facce con foto in una sola mesh (atlante), le altre a tinta unita in un'altra
    const [aw, ah] = man.atlasSize;
    const P = { t: { pos: [], uv: [], idx: [] }, f: { pos: [], col: [], idx: [] } };
    const col = new THREE.Color();
    const solid = [];
    for (const b of man.boxes) {
      const a = b.min, c = b.max;
      if (b.solid !== false) solid.push({ min: a, max: c, grp: b.grp || '' });
      if (b.round) { stage.add(roundedMesh(b)); continue; }
      col.set(b.color);
      const faces = [...new Set([...Object.keys(b.faces || {}), ...(b.flat || [])])];
      for (const f of faces) {
        const d = FACE[f](a, c);
        const corner = (i, j) => [d.o[0] + d.r[0] * d.w * i + d.u[0] * d.h * j, d.o[1] + d.r[1] * d.w * i + d.u[1] * d.h * j, d.o[2] + d.r[2] * d.w * i + d.u[2] * d.h * j];
        const q = [corner(0, 0), corner(1, 0), corner(1, 1), corner(0, 1)];
        const baked = b.faces && b.faces[f];
        const S = baked ? P.t : P.f;
        const i0 = S.pos.length / 3;
        q.forEach((p) => S.pos.push(...p));
        if (baked) {
          const [x0, y0, x1, y1] = baked;
          const u0 = (x0 + 0.5) / aw, u1 = (x1 - 0.5) / aw, v0 = 1 - (y1 - 0.5) / ah, v1 = 1 - (y0 + 0.5) / ah; // v=0 in basso (texture capovolta)
          S.uv.push(u0, v0, u1, v0, u1, v1, u0, v1);
        } else {
          const s = d.sh;
          for (let i = 0; i < 4; i++) S.col.push(Math.min(1, col.r * s), Math.min(1, col.g * s), Math.min(1, col.b * s));
        }
        S.idx.push(i0, i0 + 1, i0 + 2, i0, i0 + 2, i0 + 3);
      }
    }
    const geo = (S, withUv) => {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(S.pos, 3));
      if (withUv) g.setAttribute('uv', new THREE.Float32BufferAttribute(S.uv, 2)); else g.setAttribute('color', new THREE.Float32BufferAttribute(S.col, 3));
      g.setIndex(S.idx);
      return g;
    };
    if (P.t.idx.length) stage.add(new THREE.Mesh(geo(P.t, true), basic(T[man.atlas])));
    if (P.f.idx.length) stage.add(new THREE.Mesh(geo(P.f, false), new THREE.MeshBasicMaterial({ vertexColors: true, toneMapped: false })));
    buildCeilingStuff(stage);
    for (const it of man.items || []) stage.add(softItem(it));
    for (const p of man.prims || []) { // piccoli oggetti (la lampada nera sulla consolle)
      if (p.t !== 'cyl') continue;
      const m = new THREE.Mesh(new THREE.CylinderGeometry(p.r1, p.r0, p.h, 16), new THREE.MeshBasicMaterial({ color: p.color, toneMapped: false }));
      m.position.set(p.p[0], p.p[1] + p.h / 2, p.p[2]);
      stage.add(m);
    }
    for (const id of Object.keys(man.art || {})) arts[id] = T[man.art[id]];
    group.add(stage);
    for (const m of walls) { groups[m.userData.wall].add(m); pieces.push(m); wallMeshes.push(m); }
    pack = { solid, spawn: man.spawn || { pos: [1.6, 1.6, 3.9], yaw: 0 }, floorTex: T[man.floor] };
  }

  const api = {
    get ready() { return !!pack; },
    get on() { return on; },
    get colliders() { return pack ? pack.solid : []; },
    get spawn() { return pack?.spawn; },
    art: (id) => arts[id] || null,
    // 'ok' | 'nokey' | 'badkey' | 'assente' | 'rete' | 'pacchetto' | 'errore'
    load(onStatus) {
      if (pack) return Promise.resolve('ok');
      if (loading) return loading;
      loading = (async () => {
        const key = readKey();
        if (!key) return 'nokey';
        try {
          const raw = await fetchPack(onStatus);
          onStatus?.('Apro la stanza…');
          const plain = await decryptPack(raw, key);
          await build(plain, onStatus);
          return 'ok';
        } catch (e) {
          const m = String(e && e.message);
          return ['chiave', 'assente', 'rete', 'pacchetto'].includes(m) ? (m === 'chiave' ? 'badkey' : m) : 'errore';
        }
      })().then((r) => { loading = null; return r; });
      return loading;
    },
    setLook(v) {
      on = !!v && !!pack;
      blockTop.forEach((o) => { o.visible = !on; });
      blockWall.forEach((o) => { o.visible = !on; });
      wallMeshes.forEach((o) => { o.visible = on; });
      group.visible = on;
      render();
      return on;
    },
  };
  return api;
}
