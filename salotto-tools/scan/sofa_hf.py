"""Divano: campo di quote (heightfield) dallo splat registrato sulle foto. Scrive sofa_hf.npz con H, colori, maschera.
Uso: python3 -I sofa_hf.py <spz>"""
import os, sys, time
sys.path.insert(0, '/tmp/claude-0/s/splat')
import numpy as np, cv2, spzload
from scipy.spatial import cKDTree
path = sys.argv[1]
tf = np.load('/tmp/claude-0/s/splat/V3_tf.npz'); th, a, b, FL = float(tf['th']), float(tf['offW']), float(tf['offF']), float(tf['FL'])
par = np.load('/tmp/claude-0/s/splat/V3_photo_align_s1.npy')
nx = np.array([np.cos(th), np.sin(th)]); nzm = np.array([np.cos(th - np.pi / 2), np.sin(th - np.pi / 2)])
g = spzload.load(path); P = g['pos']; C = g['rgb']; A = g['alpha']; S = g['scale']
med = np.median(P, axis=0); r = np.linalg.norm(P - med, axis=1)
m = (r < 9) & (A > 0.35); P, C, A, S = P[m], C[m], A[m], S[m]
xz = P[:, [0, 2]]
Q = np.stack([xz @ nx - a + 7.1, P[:, 1] - FL, 4.5 - (xz @ nzm - b)], 1)
c0 = np.array([5.3, 1.0, 3.0]); s_, yaw, tx, ty, tz = par; cs, sn = np.cos(yaw), np.sin(yaw)
Y = (Q - c0) * s_; Q = np.stack([cs * Y[:, 0] + sn * Y[:, 2], Y[:, 1], -sn * Y[:, 0] + cs * Y[:, 2]], 1) + c0 + np.array([tx, ty, tz])
X0, X1, Z0, Z1 = 3.30, 6.84, 1.50, 4.55
CELL = 0.015
sel = (Q[:, 0] > X0 - 0.05) & (Q[:, 0] < X1 + 0.05) & (Q[:, 2] > Z0 - 0.05) & (Q[:, 2] < Z1 + 0.05) & (Q[:, 1] > 0.04) & (Q[:, 1] < 1.35)
Q, C = Q[sel], C[sel]
print('punti nella zona', len(Q))
# oggetti che non fanno parte del divano: tavolino, totem (rettangoli in pianta, qualsiasi quota)
EXCL = [(3.30, 3.83, 3.62, 4.43), (3.92, 4.23, 3.27, 3.58)]
keep = np.ones(len(Q), bool)
for (xa, xb, za, zb) in EXCL: keep &= ~((Q[:, 0] > xa) & (Q[:, 0] < xb) & (Q[:, 2] > za) & (Q[:, 2] < zb))
Q, C = Q[keep], C[keep]
print('dopo esclusioni', len(Q))
nxc = int(round((X1 - X0) / CELL)); nzc = int(round((Z1 - Z0) / CELL))
xs = X0 + (np.arange(nxc) + 0.5) * CELL; zs = Z0 + (np.arange(nzc) + 0.5) * CELL
XX, ZZ = np.meshgrid(xs, zs)
R = 0.035
def heights(Qp):
    tree = cKDTree(Qp[:, [0, 2]])
    nb = tree.query_ball_point(np.stack([XX.ravel(), ZZ.ravel()], 1), r=R)
    H = np.full(XX.size, np.nan, np.float32); N = np.zeros(XX.size, np.int32)
    for i, idx in enumerate(nb):
        if len(idx) < 4: continue
        y = Qp[idx, 1]; ys = np.sort(y)[::-1]
        for k in range(0, len(ys) - 3):
            top = ys[k]
            cnt = np.searchsorted(-ys, -(top - 0.03), side='right') - k
            if cnt >= 4:
                H[i] = np.median(ys[k:k + cnt]); N[i] = cnt; break
    return H.reshape(nzc, nxc), N.reshape(nzc, nxc)
t0 = time.time()
H, N = heights(Q)
# senza i cuscini (scatole orientate da cushions_fit.json): la superficie sotto si ricava dai dintorni
import json
cush = json.load(open('/tmp/claude-0/s/sofa/cushions_fit.json'))
inside = np.zeros(len(Q), bool)
for c in cush:
    ax = np.array(c['axes']); cen = np.array(c['c']); sz = np.array(c['size']) * 1.06 / 2 + np.array([0.04, 0.04, 0.04])
    loc = (Q - cen) @ ax.T
    inside |= (np.abs(loc) < sz).all(axis=1)
print('punti dentro i cuscini', int(inside.sum()))
Hn, Nn = heights(Q[~inside])
print('altezze calcolate', round(time.time() - t0, 1), 's; celle con quota:', int(np.isfinite(H).sum()), 'senza cuscini:', int(np.isfinite(Hn).sum()), 'su', H.size)
np.savez_compressed('/tmp/claude-0/s/sofa/hf_raw.npz', H=H, N=N, Hn=Hn, Nn=Nn, X0=X0, Z0=Z0, CELL=CELL)
v = np.nan_to_num(H, nan=0); v = np.clip(v / 1.1, 0, 1)
col = cv2.applyColorMap((v * 255).astype(np.uint8), cv2.COLORMAP_JET); col[~np.isfinite(H)] = 0
cv2.imwrite('/tmp/claude-0/s/sofa/hf_raw.png', cv2.resize(col, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
