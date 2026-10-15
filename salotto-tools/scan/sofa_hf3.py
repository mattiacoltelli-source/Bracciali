"""Terza parte: colori delle celle dalla nuvola dello splat + esportazione per il pacchetto (PNG quote 16 bit in RGB, JPEG colori).
Uso: python3 -I sofa_hf3.py <spz> [cell_out=0.02]"""
import os, sys, time, json
sys.path.insert(0, '/tmp/claude-0/s/splat'); sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2, spzload
from scipy.spatial import cKDTree
from fill import push_pull
path = sys.argv[1]; OUT_CELL = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02
d = np.load('/tmp/claude-0/s/sofa/hf_fill.npz'); H = d['H']; fp = d['fp']; X0 = float(d['X0']); Z0 = float(d['Z0']); CELL = float(d['CELL'])
nzc, nxc = H.shape
tf = np.load('/tmp/claude-0/s/splat/V3_tf.npz'); th, a, b, FL = float(tf['th']), float(tf['offW']), float(tf['offF']), float(tf['FL'])
par = np.load('/tmp/claude-0/s/splat/V3_photo_align_s1.npy')
nx = np.array([np.cos(th), np.sin(th)]); nzm = np.array([np.cos(th - np.pi / 2), np.sin(th - np.pi / 2)])
g = spzload.load(path); P = g['pos']; C = g['rgb']; A = g['alpha']
med = np.median(P, axis=0); r = np.linalg.norm(P - med, axis=1)
m = (r < 9) & (A > 0.35); P, C = P[m], C[m]
xz = P[:, [0, 2]]
Q = np.stack([xz @ nx - a + 7.1, P[:, 1] - FL, 4.5 - (xz @ nzm - b)], 1)
c0 = np.array([5.3, 1.0, 3.0]); s_, yaw, tx, ty, tz = par; cs, sn = np.cos(yaw), np.sin(yaw)
Y = (Q - c0) * s_; Q = np.stack([cs * Y[:, 0] + sn * Y[:, 2], Y[:, 1], -sn * Y[:, 0] + cs * Y[:, 2]], 1) + c0 + np.array([tx, ty, tz])
sel = (Q[:, 0] > X0 - 0.05) & (Q[:, 0] < X0 + nxc * CELL + 0.05) & (Q[:, 2] > Z0 - 0.05) & (Q[:, 2] < Z0 + nzc * CELL + 0.05) & (Q[:, 1] > 0.04) & (Q[:, 1] < 1.35)
Q, C = Q[sel], C[sel]
EXCL = [(3.30, 3.87, 3.58, 4.47), (3.88, 4.27, 3.23, 3.62)]
keep = np.ones(len(Q), bool)
for (xa, xb, za, zb) in EXCL: keep &= ~((Q[:, 0] > xa) & (Q[:, 0] < xb) & (Q[:, 2] > za) & (Q[:, 2] < zb))
Q, C = Q[keep], C[keep]
# colori: fuori dalla zona dei cuscini si scartano punti chiari o molto saturi (intonaco, oggetti vicini): il tessuto del divano e' grigio scuro
lum = C[:, 0] * 0.299 + C[:, 1] * 0.587 + C[:, 2] * 0.114; sat = C.max(1) - C.min(1)
cush = (Q[:, 0] > 6.30) & (Q[:, 0] < 6.98) & (Q[:, 2] > 2.35) & (Q[:, 2] < 4.15)
okc = cush | ((lum < 0.42) & (sat < 0.20))
Qc, Cc = Q[okc], C[okc]
tree = cKDTree(Qc[:, [0, 2]])
xs = X0 + (np.arange(nxc) + 0.5) * CELL; zs = Z0 + (np.arange(nzc) + 0.5) * CELL
XX, ZZ = np.meshgrid(xs, zs)
nb = tree.query_ball_point(np.stack([XX.ravel(), ZZ.ravel()], 1), r=0.035)
Q, C = Qc, Cc
col = np.zeros((XX.size, 3), np.float32); wsum = np.zeros(XX.size, np.float32)
Hf = H.ravel(); fpf = fp.ravel()
for i, idx in enumerate(nb):
    if not fpf[i] or not idx: continue
    idx = np.array(idx); dy = np.abs(Q[idx, 1] - Hf[i]); ok = dy < 0.05
    if not ok.any(): continue
    idx = idx[ok]; dd = np.hypot(Q[idx, 0] - XX.ravel()[i], Q[idx, 2] - ZZ.ravel()[i])
    wgt = 1.0 / (1.0 + (dd / 0.02) ** 2) / (1.0 + (dy[ok] / 0.02) ** 2)
    col[i] = (C[idx] * wgt[:, None]).sum(0); wsum[i] = wgt.sum()
col = col.reshape(nzc, nxc, 3); wsum = wsum.reshape(nzc, nxc)
valid = (wsum > 0.25) & (fp > 0)
print('celle impronta', int(fp.sum()), 'con colore', int(valid.sum()))
colm = col / np.maximum(wsum, 1e-6)[..., None]
fill = push_pull(colm.astype(np.float32), valid.astype(np.float32), levels=7)
colf = np.where(valid[..., None], colm, fill)
colf = cv2.GaussianBlur(colf.astype(np.float32), (0, 0), 1.0)
bgr = (np.clip(colf[..., ::-1], 0, 1) * 255).astype(np.uint8); bgr[fp == 0] = (60, 60, 60)
cv2.imwrite('/tmp/claude-0/s/sofa/hf_color.png', cv2.resize(bgr, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
# ricampiona a OUT_CELL
f = CELL / OUT_CELL
onx, onz = int(round(nxc * f)), int(round(nzc * f))
Ho = cv2.resize(H, (onx, onz), interpolation=cv2.INTER_AREA)
fpo = cv2.resize(fp.astype(np.float32), (onx, onz), interpolation=cv2.INTER_AREA) > 0.5
# in prossimita del bordo l'area-media abbassa le quote: ricalcolo con media pesata sulla sola impronta
num = cv2.resize(np.where(fp > 0, H, 0).astype(np.float32), (onx, onz), interpolation=cv2.INTER_AREA); den = cv2.resize(fp.astype(np.float32), (onx, onz), interpolation=cv2.INTER_AREA)
Ho = np.where(den > 0.5, num / np.maximum(den, 1e-6), 0).astype(np.float32); Ho[~fpo] = 0
cob = cv2.resize(bgr, (onx, onz), interpolation=cv2.INTER_AREA)
np.savez_compressed('/tmp/claude-0/s/sofa/hf_final.npz', H=Ho, fp=fpo, bgr=cob, X0=X0, Z0=Z0, CELL=OUT_CELL)
YMAX = 1.275
v16 = np.clip(np.round(Ho / YMAX * 65535), 0, 65535).astype(np.uint16)
rgb = np.dstack([np.zeros_like(v16, np.uint8), (v16 & 255).astype(np.uint8), (v16 >> 8).astype(np.uint8)])    # BGR per OpenCV: B=0, G=basso, R=alto
cv2.imwrite('/tmp/claude-0/s/sofa/sofa_h.png', rgb, [cv2.IMWRITE_PNG_COMPRESSION, 9])
cv2.imwrite('/tmp/claude-0/s/sofa/sofa_c.jpg', cob, [cv2.IMWRITE_JPEG_QUALITY, 90])
meta = dict(x0=X0, z0=Z0, cell=OUT_CELL, nx=onx, nz=onz, ymax=YMAX)
json.dump(meta, open('/tmp/claude-0/s/sofa/sofa_meta.json', 'w'))
print('esportato', meta, 'png', os.path.getsize('/tmp/claude-0/s/sofa/sofa_h.png'), 'jpg', os.path.getsize('/tmp/claude-0/s/sofa/sofa_c.jpg'))
