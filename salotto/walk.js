// Camminare nella stanza in prima persona: joystick a sinistra, trascina per guardare (tastiera: WASD o frecce).
// Collisioni con i muri e i mobili del pacchetto; da seduti il divano non fa da ostacolo.
import { ROOM } from './room.js';

const R = 0.22; // raggio del corpo
const SPEED = 1.45; // m/s
const $ = (id) => document.getElementById(id);

export function createWalk(ctx) {
  const { camera, controls, canvas, render, real } = ctx;
  const hud = $('walk-hud'), joy = $('joy'), knob = $('joy-knob');
  let on = false, last = 0, dirty = false;
  const st = { x: 1.6, z: 3.9, yaw: 0, pitch: 0, eye: 1.6 };
  const j = { x: 0, z: 0, id: null };
  const kb = { x: 0, z: 0, keys: new Set() };
  let look = null;

  const colliders = () => real.colliders;
  const inRoom = (x, z) => x >= R + 0.04 && x <= ROOM.L - R - 0.04 && z >= R + 0.04 && z <= ROOM.W - R - 0.04;
  // quanto il corpo (cerchio) entra nei mobili: >0 = dentro; serve a uscire da un mobile se ci si trova dentro (teletrasporto) senza attraversarlo
  function pen(x, z) {
    let worst = -1;
    const seated = st.eye < 1.3;
    for (const c of colliders()) {
      if (seated && c.grp === 'sofa') continue;
      if (c.max[1] < 0.25 || c.min[1] > st.eye) continue;
      const dx = Math.max(c.min[0] - x, 0, x - c.max[0]), dz = Math.max(c.min[2] - z, 0, z - c.max[2]);
      const out = Math.hypot(dx, dz);
      const d = out > 0 ? out : -Math.min(x - c.min[0], c.max[0] - x, z - c.min[2], c.max[2] - z);
      worst = Math.max(worst, R - d);
    }
    return worst;
  }
  function move(dx, dz) {
    const p0 = pen(st.x, st.z);
    const ok = (x, z) => inRoom(x, z) && (() => { const p = pen(x, z); return p <= 0 || p <= p0 + 1e-6; })();
    const nx = st.x + dx, nz = st.z + dz;
    if (ok(nx, nz)) { st.x = nx; st.z = nz; }
    else if (ok(nx, st.z)) st.x = nx;
    else if (ok(st.x, nz)) st.z = nz;
  }
  function apply() {
    camera.rotation.order = 'YXZ';
    camera.rotation.set(st.pitch, st.yaw, 0);
    camera.position.set(st.x, st.eye, st.z);
    dirty = true;
  }
  const fovFor = () => (camera.aspect < 1 ? 78 : 66);

  function place(pos, at, eye) { // da una "vista": posizione e punto guardato
    st.x = Math.min(Math.max(pos[0], R + 0.05), ROOM.L - R - 0.05);
    st.z = Math.min(Math.max(pos[2], R + 0.05), ROOM.W - R - 0.05);
    if (eye) st.eye = eye;
    const dx = at[0] - pos[0], dz = at[2] - pos[2], dy = at[1] - pos[1];
    st.yaw = Math.atan2(-dx, -dz);
    st.pitch = Math.max(-1.2, Math.min(1.2, Math.atan2(dy, Math.hypot(dx, dz))));
    apply(); render();
  }
  function enter(sp) {
    if (on) return;
    on = true;
    controls.enabled = false;
    camera.fov = fovFor(); camera.updateProjectionMatrix();
    const s = sp || real.spawn;
    st.eye = 1.6; st.pitch = 0;
    st.x = s.pos[0]; st.z = s.pos[2]; st.yaw = s.yaw || 0;
    document.querySelectorAll('[data-eye]').forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.eye) === st.eye)));
    hud.hidden = false;
    document.body.classList.add('walking');
    apply(); render();
  }
  function exit() {
    if (!on) return;
    on = false;
    hud.hidden = true;
    document.body.classList.remove('walking');
    j.x = j.z = 0; j.id = null; kb.keys.clear(); kb.x = kb.z = 0; look = null;
    knob.style.transform = '';
    camera.fov = 60; camera.updateProjectionMatrix();
    const f = [-Math.sin(st.yaw) * Math.cos(st.pitch), Math.sin(st.pitch), -Math.cos(st.yaw) * Math.cos(st.pitch)];
    controls.target.set(st.x + f[0] * 0.8, st.eye + f[1] * 0.8, st.z + f[2] * 0.8);
    controls.enabled = true;
    controls.update(); render();
  }

  // --- guardare: trascinare sulla scena ---
  canvas.addEventListener('pointerdown', (e) => { if (on && !look) look = { id: e.pointerId, x: e.clientX, y: e.clientY }; });
  canvas.addEventListener('pointermove', (e) => {
    if (!on || !look || look.id !== e.pointerId) return;
    const k = (camera.fov * Math.PI / 180) / canvas.clientHeight; // rad per pixel: segue il dito
    st.yaw += (e.clientX - look.x) * k * 1.1;
    st.pitch = Math.max(-1.25, Math.min(1.25, st.pitch + (e.clientY - look.y) * k * 1.1));
    look.x = e.clientX; look.y = e.clientY;
    apply();
  });
  const endLook = (e) => { if (look && look.id === e.pointerId) look = null; };
  canvas.addEventListener('pointerup', endLook);
  canvas.addEventListener('pointercancel', endLook);

  // --- muoversi: joystick ---
  const setJoy = (e) => {
    const r = joy.getBoundingClientRect(), rad = r.width / 2;
    let dx = (e.clientX - (r.left + rad)) / rad, dy = (e.clientY - (r.top + rad)) / rad;
    const m = Math.hypot(dx, dy);
    if (m > 1) { dx /= m; dy /= m; }
    j.x = dx; j.z = -dy;
    knob.style.transform = `translate(${dx * rad * 0.62}px, ${dy * rad * 0.62}px)`;
  };
  joy.addEventListener('pointerdown', (e) => { if (j.id === null) { j.id = e.pointerId; joy.setPointerCapture(e.pointerId); setJoy(e); } });
  joy.addEventListener('pointermove', (e) => { if (e.pointerId === j.id) setJoy(e); });
  const endJoy = (e) => { if (e.pointerId === j.id) { j.id = null; j.x = j.z = 0; knob.style.transform = ''; } };
  joy.addEventListener('pointerup', endJoy);
  joy.addEventListener('pointercancel', endJoy);

  // --- tastiera ---
  const KEYS = { w: [0, 1], arrowup: [0, 1], z: [0, 1], s: [0, -1], arrowdown: [0, -1], a: [-1, 0], q: [-1, 0], arrowleft: [-1, 0], d: [1, 0], arrowright: [1, 0] };
  const kbSync = () => { kb.x = kb.z = 0; kb.keys.forEach((k) => { kb.x += KEYS[k][0]; kb.z += KEYS[k][1]; }); };
  addEventListener('keydown', (e) => { const k = e.key.toLowerCase(); if (on && KEYS[k] && !/input|textarea/i.test(e.target.tagName)) { kb.keys.add(k); kbSync(); e.preventDefault(); } });
  addEventListener('keyup', (e) => { kb.keys.delete(e.key.toLowerCase()); kbSync(); });
  addEventListener('blur', () => { kb.keys.clear(); kbSync(); });

  $('walk-exit').onclick = () => exit();
  document.querySelectorAll('[data-eye]').forEach((b) => {
    b.onclick = () => {
      st.eye = Number(b.dataset.eye);
      document.querySelectorAll('[data-eye]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      apply(); render();
    };
  });

  return {
    active: () => on,
    enter, exit, place,
    refov() { if (on) { camera.fov = fovFor(); camera.updateProjectionMatrix(); render(); } },
    // da chiamare a ogni frame: ritorna true se la vista è cambiata
    step(now) {
      if (!on) return false;
      const dt = Math.min(0.05, (now - last) / 1000 || 0); last = now;
      let ix = j.x + kb.x, iz = j.z + kb.z;
      const m = Math.hypot(ix, iz);
      if (m > 1) { ix /= m; iz /= m; }
      if (m > 0.05) {
        const sp = SPEED * dt, s = Math.sin(st.yaw), c = Math.cos(st.yaw);
        move((-s * iz + c * ix) * sp, (-c * iz - s * ix) * sp);
        apply();
      }
      const d = dirty; dirty = false;
      return d;
    },
  };
}
