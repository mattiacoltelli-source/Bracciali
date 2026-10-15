"""Allinea lo scan della credenza (primo .spz) alla stanza con l'NCC fra foto e punti proiettati."""
import os, sys, time
os.environ.setdefault('FRAME_EXT', '1')
sys.path.insert(0, '/tmp/claude-0/s/splat'); sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2, spzload
from plane import FR
path = os.environ['SPZ_FILE']
w = np.load('/tmp/claude-0/s/splat/V1_geo.npz'); n = w['n']; off = float(w['off']); FL = float(w['FL'])
t = np.array([-n[1], n[0]])
g = spzload.load(path); P = g['pos']; C = g['rgb']; A = g['alpha']; S = g['scale']
med = np.median(P, axis=0); r = np.linalg.norm(P - med, axis=1)
m = (r < 8) & (A > 0.4); P, C, S = P[m], C[m], S[m]
v = off - (P[:, [0, 2]] @ n)
if (v > 0).sum() < (v < 0).sum(): v = -v
u = P[:, [0, 2]] @ t
Q0 = np.stack([v, P[:, 1] - FL, 3.788 - u], 1)
sel = (Q0[:, 0] > -0.1) & (Q0[:, 0] < 1.0) & (Q0[:, 2] > 0.1) & (Q0[:, 2] < 2.6) & (Q0[:, 1] > 0.05) & (Q0[:, 1] < 2.2)
Q0 = Q0[sel]; Cs = C[sel]; print('punti nella zona', len(Q0))
G = (Cs[:, 0] * 0.299 + Cs[:, 1] * 0.587 + Cs[:, 2] * 0.114).astype(np.float32)
if len(Q0) > 70000:
    k = np.random.default_rng(0).choice(len(Q0), 70000, replace=False); Q0, G = Q0[k], G[k]
fr = FR(); SC = 0.25
CAMS = ['3039c671', '8ebbe415', '6d89137e', '60e39c52', '4bd3d963', '939e9457', '85ba8931', '36b5d801', '4d2e8ed4', '23446e1f']
photos = {}
for c in CAMS:
    im = fr.image(c, SC); photos[c] = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0, (0, 0), 1.2)
c0 = np.array([0.3, 1.0, 1.4])
def apply(p, X):
    s, yaw, tx, ty, tz = p
    cs, sn = np.cos(yaw), np.sin(yaw); Y = (X - c0) * s
    return np.stack([cs * Y[:, 0] + sn * Y[:, 2], Y[:, 1], -sn * Y[:, 0] + cs * Y[:, 2]], 1) + c0 + np.array([tx, ty, tz])
def synth(cam, X):
    h, w_ = photos[cam].shape
    uv, z = fr.project(cam, X); uv = uv * SC
    ok = (z > 0.3) & (uv[:, 0] >= 1) & (uv[:, 0] < w_ - 2) & (uv[:, 1] >= 1) & (uv[:, 1] < h - 2)
    idx = np.nonzero(ok)[0]; idx = idx[np.argsort(-z[idx])]
    img = np.zeros((h, w_), np.float32); cnt = np.zeros((h, w_), np.float32)
    xi = np.round(uv[idx, 0]).astype(int); yi = np.round(uv[idx, 1]).astype(int)
    img[yi, xi] = G[idx]; cnt[yi, xi] = 1
    return img, cnt
def cost(p, verbose=False):
    X = apply(p, Q0); tot = 0.0; nn = 0
    for cam in CAMS:
        img, cnt = synth(cam, X)
        a_ = cv2.GaussianBlur(img * cnt, (0, 0), 2.0); wsum = cv2.GaussianBlur(cnt, (0, 0), 2.0)
        sm = a_ / np.maximum(wsum, 1e-3); mask = (wsum > 0.08)
        if mask.sum() < 300: continue
        x1 = sm[mask]; x2 = photos[cam][mask]; x1 = x1 - x1.mean(); x2 = x2 - x2.mean()
        ncc = float((x1 * x2).sum() / (np.sqrt((x1 * x1).sum() * (x2 * x2).sum()) + 1e-9))
        if verbose: print('  ', cam, 'NCC', round(ncc, 3), 'px', int(mask.sum()))
        tot += ncc; nn += 1
    return -tot / max(nn, 1)
p0 = np.array([1.0, 0.0, 0.0, 0.0, 0.0]); t0 = time.time()
print('iniziale', round(cost(p0, True), 4))
best = p0.copy(); bc = cost(p0)
steps = [np.array([0.03, 0.03, 0.12, 0.06, 0.12]), np.array([0.015, 0.015, 0.06, 0.03, 0.06]), np.array([0.008, 0.008, 0.03, 0.015, 0.03]), np.array([0.004, 0.004, 0.015, 0.008, 0.015]), np.array([0.002, 0.002, 0.008, 0.004, 0.008])]
for st in steps:
    for it in range(12):
        improved = False
        for i in range(5):
            for sg in (-1, 1):
                q = best.copy(); q[i] += sg * st[i]; c = cost(q)
                if c < bc - 1e-5: bc = c; best = q; improved = True
        if not improved: break
    print('passo', st, '->', best.round(4), 'costo', round(bc, 4), round(time.time() - t0), 's', flush=True)
print('finale'); cost(best, True)
np.save('/tmp/claude-0/s/splat/V1_align.npy', best)
