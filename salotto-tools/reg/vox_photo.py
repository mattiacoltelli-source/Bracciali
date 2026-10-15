"""Ricolora i voxel con i colori delle foto: per ogni voxel (centro + normale stimata dai vicini) si campionano le foto che lo vedono meglio e si prende la mediana.
Uso: python3 vox_photo.py <tag> [scala_foto=0.5]   (legge/riscrive /tmp/claude-0/s/sofa/vox_<tag>.bin)"""
import os, sys, json
os.environ.setdefault('FRAME_EXT', '1')
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
from cams_sel import select
from scipy.spatial import cKDTree
tag = sys.argv[1]; SC = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
D = '/tmp/claude-0/s/sofa'
meta = json.load(open(f'{D}/vox_{tag}.json')); raw = np.fromfile(f'{D}/vox_{tag}.bin', np.uint8).reshape(-1, 9)
if os.path.exists(f'{D}/vox_{tag}_orig.bin'): raw = np.fromfile(f'{D}/vox_{tag}_orig.bin', np.uint8).reshape(-1, 9)   # parto sempre dai colori della scansione
else: raw.tofile(f'{D}/vox_{tag}_orig.bin')
ii = np.stack([raw[:, 0].astype(int) | (raw[:, 1].astype(int) << 8), raw[:, 2].astype(int) | (raw[:, 3].astype(int) << 8), raw[:, 4].astype(int) | (raw[:, 5].astype(int) << 8)], 1)
P = np.stack([meta['x0'] + (ii[:, 0] + 0.5) * meta['cell'], meta['y0'] + (ii[:, 1] + 0.5) * meta['cell'], meta['z0'] + (ii[:, 2] + 0.5) * meta['cell']], 1)
col0 = raw[:, 6:9].astype(np.float32) / 255.0      # RGB della scansione
tree = cKDTree(P)
nb = tree.query_ball_point(P, r=meta['cell'] * 3.2)
N = np.zeros_like(P)
for i, idx in enumerate(nb):
    c = P[idx].mean(0); v = P[i] - c
    N[i] = v / (np.linalg.norm(v) + 1e-6) if np.linalg.norm(v) > 1e-4 else np.array([0, 1.0, 0])
fr = FR(); names = select(fr)
imgs = {c: fr.image(c, SC) for c in names}
samples = np.full((len(P), len(names), 3), np.nan, np.float32); wts = np.zeros((len(P), len(names)), np.float32)
for k, c in enumerate(names):
    C = fr.cams[c]['C']; v = C - P; dist = np.linalg.norm(v, axis=1); cosv = (v * N).sum(1) / np.maximum(dist, 1e-6)
    uv, z = fr.project(c, P); uv = uv * SC
    h, w = imgs[c].shape[:2]
    ok = (z > 0.3) & (uv[:, 0] >= 2) & (uv[:, 0] < w - 3) & (uv[:, 1] >= 2) & (uv[:, 1] < h - 3) & (cosv > 0.25)
    idx = np.nonzero(ok)[0]
    if len(idx) == 0: continue
    mx = uv[idx, 0].astype(np.float32); my = uv[idx, 1].astype(np.float32)
    # media 3x3 per ridurre il rumore
    blur = cv2.blur(imgs[c], (3, 3))
    col = cv2.remap(blur, mx.reshape(-1, 1), my.reshape(-1, 1), cv2.INTER_LINEAR).reshape(-1, 3)[:, ::-1].astype(np.float32) / 255.0
    samples[idx, k] = col; wts[idx, k] = (np.maximum(cosv[idx], 0) ** 2) / np.maximum(dist[idx], 0.5)
# colore finale: mediana pesata dei 4 campioni migliori; se nessuna foto vede il voxel, resta il colore della scansione
out = col0.copy(); used = 0
for i in range(len(P)):
    w = wts[i]; o = np.argsort(-w)[:4]; o = o[w[o] > 0]
    if len(o) == 0: continue
    s = samples[i, o]
    out[i] = np.median(s, axis=0) if len(o) >= 3 else s.mean(0)
    used += 1
print('voxel', len(P), 'ricolorati dalle foto', used)
# guadagno medio rispetto alla scansione (solo per informazione)
print('luminanza media: scansione %.3f  foto %.3f' % (col0.mean(), out.mean()))
rec = raw.copy(); rec[:, 6:9] = np.clip(out * 255, 0, 255).astype(np.uint8)
rec.tofile(f'{D}/vox_{tag}.bin')
