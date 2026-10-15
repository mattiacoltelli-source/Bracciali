"""Cuscini dalla scansione del divano: punti beige/senape, cluster, scatola orientata (PCA)."""
import os
import sys
sys.path.insert(0, '/tmp/claude-0/s/splat')
import numpy as np, spzload, json
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial import cKDTree
path = os.environ['SPZ_FILE']
tf = np.load('/tmp/claude-0/s/splat/V3_tf.npz'); th, a, b, FL = float(tf['th']), float(tf['offW']), float(tf['offF']), float(tf['FL'])
par = np.load('/tmp/claude-0/s/splat/V3_photo_align_s1.npy')
nx = np.array([np.cos(th), np.sin(th)]); nzm = np.array([np.cos(th - np.pi / 2), np.sin(th - np.pi / 2)])
g = spzload.load(path); P = g['pos']; C = g['rgb']; A = g['alpha']
med = np.median(P, axis=0); r = np.linalg.norm(P - med, axis=1)
m = (r < 9) & (A > 0.45); P, C = P[m], C[m]
xz = P[:, [0, 2]]
Q = np.stack([xz @ nx - a + 7.1, P[:, 1] - FL, 4.5 - (xz @ nzm - b)], 1)
c0 = np.array([5.3, 1.0, 3.0]); s_, yaw, tx, ty, tz = par; cs, sn = np.cos(yaw), np.sin(yaw)
Y = (Q - c0) * s_; Q = np.stack([cs * Y[:, 0] + sn * Y[:, 2], Y[:, 1], -sn * Y[:, 0] + cs * Y[:, 2]], 1) + c0 + np.array([tx, ty, tz])
reg = (Q[:, 0] > 5.6) & (Q[:, 0] < 7.1) & (Q[:, 2] > 2.2) & (Q[:, 2] < 4.4) & (Q[:, 1] > 0.3) & (Q[:, 1] < 1.0)
Qr, Cr = Q[reg], C[reg]
lum = Cr.mean(1); sat = Cr.max(1) - Cr.min(1)
beige = (lum > 0.50) & (sat > 0.04) & (sat < 0.30) & (Cr[:, 0] >= Cr[:, 2])
must = (Cr[:, 0] > 0.40) & (Cr[:, 0] - Cr[:, 2] > 0.22) & (Cr[:, 1] > 0.22) & (Cr[:, 1] < 0.6) & (lum < 0.6)
print('beige', beige.sum(), 'senape', must.sum())
res = []
for name, mask in (('beige', beige), ('senape', must)):
    pts = Qr[mask]; col = Cr[mask]
    if len(pts) < 50: continue
    Z = linkage(pts[::max(1, len(pts) // 4000)], 'single')
    sub = pts[::max(1, len(pts) // 4000)]
    lab = fcluster(Z, 0.06, 'distance')
    tree = cKDTree(sub); _, nn = tree.query(pts); labs = lab[nn]
    for l in np.unique(labs):
        sel = labs == l
        if sel.sum() < 150: continue
        X = pts[sel]; c = X.mean(0)
        u_, s, vt = np.linalg.svd(X - c, full_matrices=False)
        proj = (X - c) @ vt.T
        ext = np.percentile(proj, [3, 97], axis=0)
        size = ext[1] - ext[0]; cen = c + ((ext[0] + ext[1]) / 2) @ vt
        colm = (np.median(col[sel], axis=0) * 255).astype(int)
        print(name, 'n', int(sel.sum()), 'centro', cen.round(3), 'dimensioni(PCA)', size.round(3), 'assi\n', vt.round(2), 'colore', colm)
        res.append(dict(name=name, n=int(sel.sum()), c=cen.tolist(), size=size.tolist(), axes=vt.tolist(), color=colm.tolist()))
json.dump(res, open('/tmp/claude-0/s/sofa/cushions_raw.json', 'w'), indent=1)
