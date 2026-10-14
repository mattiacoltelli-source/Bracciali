import * as THREE from 'three';
import { ROOM, WALLS, OPENINGS } from './room.js';

const mat = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.9, metalness: 0, ...o });
const M = {
  wall: mat('#f1efe9'),
  ceiling: mat('#f6f5f1'),
  white: mat('#ecebe6'),
  dark: mat('#2e3033'),
  black: mat('#141416', { roughness: 0.5 }),
  wood: mat('#6d4a33', { roughness: 0.6 }),
  walnut: mat('#5a3b28', { roughness: 0.55 }),
  cream: mat('#c1baab'),
  fabric: mat('#4c5155', { roughness: 1 }),
  brown: mat('#4a2c20', { roughness: 0.55 }),
  brass: mat('#b8985a', { roughness: 0.35, metalness: 0.6 }),
  bronze: mat('#a58c5f', { roughness: 0.4, metalness: 0.5 }),
  hall: mat('#1d1b19', { roughness: 1 }),
  glow: new THREE.MeshStandardMaterial({ color: '#ffd9a0', emissive: '#ffcf8a', emissiveIntensity: 1.4 }),
};
const back = (m) => { const c = m.clone(); c.side = THREE.BackSide; return c; };

function marbleTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  g.fillStyle = '#4b4a47';
  g.fillRect(0, 0, 512, 512);
  let seed = 7;
  const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (let i = 0; i < 40; i++) { // nuvole di tono
    g.fillStyle = `rgba(${rnd() < 0.5 ? '150,140,120' : '25,25,25'},${0.05 + rnd() * 0.1})`;
    g.beginPath();
    g.ellipse(rnd() * 512, rnd() * 512, 40 + rnd() * 120, 15 + rnd() * 50, rnd() * 3, 0, 7);
    g.fill();
  }
  for (let i = 0; i < 16; i++) { // venature
    g.strokeStyle = `rgba(${rnd() < 0.5 ? '210,200,180' : '15,15,15'},${0.1 + rnd() * 0.22})`;
    g.lineWidth = 0.6 + rnd() * 1.6;
    g.beginPath();
    let x = rnd() * 512, y = rnd() * 512;
    g.moveTo(x, y);
    for (let k = 0; k < 6; k++) { x += 40 + rnd() * 60; y += (rnd() - 0.5) * 90; g.lineTo(x, y); }
    g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  t.repeat.set(ROOM.L / 1.2, ROOM.W / 1.2);
  t.anisotropy = 4;
  return t;
}

export function artTexture(colors) {
  const c = document.createElement('canvas');
  c.width = 128; c.height = 128;
  const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 128);
  gr.addColorStop(0, colors[0]); gr.addColorStop(0.55, colors[1]); gr.addColorStop(1, colors[2]);
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  g.fillStyle = 'rgba(0,0,0,.18)';
  g.beginPath(); g.moveTo(0, 128); g.lineTo(50, 60); g.lineTo(90, 128); g.fill();
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const V = (a) => new THREE.Vector3(...a);

// Gruppo con il riferimento locale della parete: u lungo la parete, y in alto, z verso l'interno.
export function wallGroup(id) {
  const w = WALLS[id];
  const g = new THREE.Group();
  g.applyMatrix4(new THREE.Matrix4().makeBasis(V(w.U), new THREE.Vector3(0, 1, 0), V(w.N)).setPosition(V(w.O)));
  g.updateMatrixWorld(true);
  return g;
}

function box(parent, w, h, d, material, x, y0, z) { // x,z = centro; y0 = base
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  m.position.set(x, y0 + h / 2, z);
  parent.add(m);
  return m;
}

function buildOpening(g, o, u0, u1) {
  const w = u1 - u0, h = o.y1 - o.y0, cx = (u0 + u1) / 2, cy = (o.y0 + o.y1) / 2;
  const hidden = new THREE.MeshBasicMaterial({ visible: false });
  const inset = (depth, material) => { // spalle dell'apertura, viste dall'interno (senza fondo)
    const bm = back(material);
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, depth), [bm, bm, bm, bm, bm, hidden]);
    m.position.set(cx, cy, -depth / 2);
    g.add(m);
  };
  const frame = (t, material, z = 0.01) => {
    box(g, t, h, 0.05, material, u0 + t / 2, o.y0, z);
    box(g, t, h, 0.05, material, u1 - t / 2, o.y0, z);
    box(g, w - 2 * t, t, 0.05, material, cx, o.y1 - t, z);
    if (o.y0 > 0) box(g, w - 2 * t, t, 0.05, material, cx, o.y0, z);
  };
  if (o.kind === 'passage') { inset(0.2, M.white); const d = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.9), back(M.hall)); d.position.set(cx, cy, -0.65); g.add(d); }
  if (o.kind === 'door-open') { inset(0.12, M.white); const d = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.9), back(M.hall)); d.position.set(cx, cy, -0.55); g.add(d); frame(0.07, M.brown); }
  if (o.kind === 'door-closed') {
    inset(0.12, M.white); frame(0.08, M.brown);
    box(g, w - 0.16, h - 0.08, 0.05, M.brown, cx, o.y0, -0.03);
    box(g, 0.1, 0.03, 0.05, M.brass, u0 + 0.2, 1.0, 0.03);
  }
  if (o.kind === 'window') {
    inset(0.3, M.white);
    const sky = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: '#cfe0f2' }));
    sky.position.set(cx, cy, -0.3);
    g.add(sky);
    frame(0.06, M.bronze, -0.02);
    box(g, 0.05, h - 0.12, 0.05, M.bronze, cx, o.y0 + 0.06, -0.02);
    const glass = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.12, h - 0.12), new THREE.MeshStandardMaterial({ color: '#8fb1c9', transparent: true, opacity: 0.18, roughness: 0.1, depthWrite: false }));
    glass.position.set(cx, cy, -0.01);
    g.add(glass);
    box(g, w + 0.16, 0.04, 0.12, M.white, cx, o.y0 - 0.03, 0.05); // davanzale
  }
}

export function buildRoom(scene) {
  const pieces = []; // pezzi di muro per il raycast
  const groups = {};
  for (const id of Object.keys(WALLS)) {
    const w = WALLS[id];
    const g = wallGroup(id);
    groups[id] = g;
    scene.add(g);
    const ops = (OPENINGS[id] || [])
      .map((o) => ({ ...o, u0: Math.min(w.toU(o.s0), w.toU(o.s1)), u1: Math.max(w.toU(o.s0), w.toU(o.s1)) }))
      .sort((a, b) => a.u0 - b.u0);
    const rect = (u0, u1, y0, y1) => {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(u1 - u0, y1 - y0), M.wall);
      m.position.set((u0 + u1) / 2, (y0 + y1) / 2, 0);
      m.userData.wall = id;
      g.add(m);
      pieces.push(m);
    };
    let cur = 0;
    for (const o of ops) {
      if (o.u0 > cur) rect(cur, o.u0, 0, ROOM.H);
      if (o.y0 > 0) rect(o.u0, o.u1, 0, o.y0);
      if (o.y1 < ROOM.H) rect(o.u0, o.u1, o.y1, ROOM.H);
      buildOpening(g, o, o.u0, o.u1);
      cur = o.u1;
    }
    if (cur < w.len) rect(cur, w.len, 0, ROOM.H);
    // battiscopa e cornice (interrotti dalle aperture che arrivano a terra)
    let c2 = 0;
    const skirt = (a, b) => { if (b - a > 0.01) box(g, b - a, 0.09, 0.012, mat('#6a5646', { roughness: 0.5 }), (a + b) / 2, 0, 0.006); };
    for (const o of ops) { if (o.y0 === 0) { skirt(c2, o.u0); c2 = o.u1; } }
    skirt(c2, w.len);
    box(g, w.len, 0.1, 0.1, M.white, w.len / 2, ROOM.H - 0.1, 0.05);
  }

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.L, ROOM.W), new THREE.MeshStandardMaterial({ map: marbleTexture(), roughness: 0.28, metalness: 0.05 }));
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(ROOM.L / 2, 0, ROOM.W / 2);
  scene.add(floor);
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.L, ROOM.W), M.ceiling);
  ceil.rotation.x = Math.PI / 2;
  ceil.position.set(ROOM.L / 2, ROOM.H, ROOM.W / 2);
  scene.add(ceil);

  buildBeams(scene);
  buildFurniture(scene);
  return { pieces, groups };
}

function buildBeams(scene) {
  for (const x of [2.3, ROOM.L - 2.3]) { // stime: posizione, larghezza 40 cm, discesa 20 cm
    box(scene, 0.4, 0.2, ROOM.W, M.white, x, ROOM.H - 0.2, ROOM.W / 2);
    box(scene, 0.03, 0.03, ROOM.W - 0.9, M.black, x, ROOM.H - 0.23, ROOM.W / 2); // binario
    for (let i = 0; i < 4; i++) {
      const z = 0.9 + i * 0.9;
      const s = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.14, 14), M.black);
      s.position.set(x, ROOM.H - 0.31, z);
      s.rotation.x = (i % 2 ? 0.5 : -0.5);
      scene.add(s);
      const tip = new THREE.Mesh(new THREE.CircleGeometry(0.032, 14), M.glow);
      tip.position.set(0, -0.0705, 0);
      tip.rotation.x = Math.PI / 2;
      s.add(tip);
    }
  }
}

function buildFurniture(scene) {
  const { L, W } = ROOM;
  // --- parete TV (z = 0, s = x) ---
  box(scene, 0.83, 1.3, 0.35, M.dark, 4.345, 0.78, 0.175); // pensile alto
  [1.0, 1.4, 1.8].forEach((y) => box(scene, 0.21, 0.03, 0.22, M.walnut, 3.825, y, 0.11));
  box(scene, 2.54, 0.42, 0.42, M.cream, 5.45, 0.17, 0.21); // base TV
  box(scene, 2.85, 0.04, 0.45, M.walnut, 5.725, 0.59, 0.225);
  box(scene, 0.43, 0.42, 0.42, M.walnut, 6.935, 0.17, 0.21);
  box(scene, 1.45, 0.82, 0.05, new THREE.MeshStandardMaterial({ color: '#0c0d10', roughness: 0.3, emissive: '#10161f', emissiveIntensity: 0.6 }), 5.755, 0.70, 0.12);
  box(scene, 0.9, 0.06, 0.1, M.black, 5.76, 0.63, 0.2);
  for (const [a, b, ps] of [[5.0, 5.93, [5.15, 5.46, 5.77]], [6.22, 7.26, [6.4, 6.72, 7.04]]]) {
    box(scene, b - a, 0.03, 0.1, M.dark, (a + b) / 2, 1.77, 0.05);
    ps.forEach((x, i) => {
      box(scene, 0.22, 0.3, 0.025, M.black, x, 1.8, 0.05);
      box(scene, 0.19, 0.27, 0.005, mat(['#c9b8a8', '#cfd6dc', '#e2b13c', '#2c5f9a', '#3a77b8', '#2b2b2b'][(ps[0] > 6 ? 3 : 0) + i]), x, 1.815, 0.065);
    });
  }
  box(scene, 0.08, 0.08, 0.02, M.white, 2.02, 1.35, 0.01); // termostato
  box(scene, 0.09, 0.11, 0.015, M.dark, 2.0, 1.05, 0.008); // interruttori

  // --- parete split (x = 0, s = z dall'ingresso: z = W - s) ---
  box(scene, 0.45, 0.6, 2.04, M.dark, 0.225, 0.18, W - 3.18); // credenza
  box(scene, 0.47, 0.02, 2.06, mat('#26282a'), 0.235, 0.78, W - 3.18);
  box(scene, 0.2, 0.29, 0.84, M.white, 0.1, 2.55, W - 1.38); // climatizzatore
  box(scene, 0.1, 0.64, 0.66, M.white, 0.05, 0.08, W - 0.44); // radiatore

  // --- parete ingresso (z = W, s = x dall'angolo split) ---
  for (const x of [2.63, 2.77]) box(scene, 0.03, 0.57, 0.04, M.glow, x, 1.46, W - 0.03); // applique

  // --- divano a L (stime: 3 m lungo l'ingresso, chaise lungo la finestra) ---
  const sofa = new THREE.Group();
  scene.add(sofa);
  const x1 = L - 0.28, xA = x1 - 3.0, zF = W - 0.95;
  box(sofa, 3.0, 0.45, 0.95, M.fabric, (xA + x1) / 2, 0.1, W - 0.475); // seduta principale
  box(sofa, 3.0, 0.5, 0.25, M.fabric, (xA + x1) / 2, 0.55, W - 0.125); // schienale
  box(sofa, 0.95, 0.45, 1.25, M.fabric, x1 - 0.475, 0.1, zF - 0.625); // chaise
  box(sofa, 0.2, 0.3, 1.25, M.fabric, x1 - 0.1, 0.55, zF - 0.625); // schienale basso
  box(sofa, 0.25, 0.65, 0.95, M.fabric, xA + 0.125, 0.1, W - 0.475); // bracciolo
  // --- consolle dietro la chaise (parete finestra) ---
  box(scene, 0.28, 0.03, 1.7, M.walnut, L - 0.14, 0.75, W - 0.85);
  for (const [dx, dz] of [[0.03, 0.03], [0.25, 0.03], [0.03, 1.67], [0.25, 1.67]]) box(scene, 0.03, 0.75, 0.03, M.black, L - 0.28 + dx, 0, W - 1.7 + dz);
  box(scene, 0.1, 0.3, 0.2, mat('#7a1f1f'), L - 0.14, 0.78, W - 0.8);
  const lamp = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.35, 8), M.black);
  lamp.position.set(L - 0.14, 0.78 + 0.175, W - 0.25);
  scene.add(lamp);
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.07, 0.09, 14), M.black);
  shade.position.set(L - 0.14, 0.78 + 0.4, W - 0.25);
  scene.add(shade);
  box(scene, 0.1, 0.7, 0.9, M.white, L - 0.05, 0.08, 1.17); // radiatore finestra
}

export function addLights(scene) {
  scene.add(new THREE.HemisphereLight('#ffffff', '#9a9285', 1.25));
  const d = new THREE.DirectionalLight('#fff4e0', 0.9);
  d.position.set(3, 8, 6);
  scene.add(d);
  for (const x of [2.3, ROOM.L - 2.3]) {
    for (const z of [1.2, 3.3]) {
      const p = new THREE.PointLight('#fff8ee', 2.6, 6, 1.6);
      p.position.set(x, ROOM.H - 0.5, z);
      scene.add(p);
    }
  }
}
