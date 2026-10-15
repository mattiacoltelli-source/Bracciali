"""Allinea lo splat del divano alle foto registrate massimizzando la correlazione (NCC) fra le foto e i punti dello splat proiettati.
Uso: photo_align.py <spz> """
import os, sys, time
os.environ.setdefault('FRAME_EXT', '1')
sys.path.insert(0, '/tmp/claude-0/s/splat'); sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2, spzload
from scipy.optimize import minimize
from plane import FR
path = sys.argv[1]
tf = np.load('/tmp/claude-0/s/splat/V3_tf.npz'); th, a, b, FL = float(tf['th']), float(tf['offW']), float(tf['offF']), float(tf['FL'])
nx = np.array([np.cos(th), np.sin(th)]); nzm = np.array([np.cos(th - np.pi / 2), np.sin(th - np.pi / 2)])
g = spzload.load(path); P = g['pos']; C = g['rgb']; A = g['alpha']
med = np.median(P, axis=0); r = np.linalg.norm(P - med, axis=1)
m = (r < 9) & (A > 0.4); P, C = P[m], C[m]
xz = P[:, [0, 2]]
Q0 = np.stack([xz @ nx - a + 7.1, P[:, 1] - FL, 4.5 - (xz @ nzm - b)], 1)
sel = (Q0[:, 0] > 3.3) & (Q0[:, 0] < 7.2) & (Q0[:, 2] > 1.5) & (Q0[:, 2] < 4.6) & (Q0[:, 1] > 0.03) & (Q0[:, 1] < 1.4)
Q0 = Q0[sel]; G = (C[sel] @ np.array([0.114, 0.587, 0.299])[::-1][::-1]).astype(np.float32)   # luminanza (rgb)
G = (C[sel][:, 0] * 0.299 + C[sel][:, 1] * 0.587 + C[sel][:, 2] * 0.114).astype(np.float32)
rng = np.random.default_rng(0)
if len(Q0) > 70000:
    k = rng.choice(len(Q0), 70000, replace=False); Q0, G = Q0[k], G[k]
print('punti splat usati', len(Q0))
fr = FR(); SC = 0.2
CAMS = ['78a53194', '60e39c52', '23446e1f', 'ca7a6257', 'a03ce4c7', '896e2721', '679522f2']
photos = {}
for c in CAMS:
    im = fr.image(c, SC); gimg = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    photos[c] = cv2.GaussianBlur(gimg, (0, 0), 1.5)
c0 = np.array([5.3, 1.0, 3.0])
def apply(p, X):
    s, yaw, tx, ty, tz = p
    cs, sn = np.cos(yaw), np.sin(yaw)
    Y = (X - c0) * s
    return np.stack([cs * Y[:, 0] + sn * Y[:, 2], Y[:, 1], -sn * Y[:, 0] + cs * Y[:, 2]], 1) + c0 + np.array([tx, ty, tz])
def synth(cam, X):
    h, w = photos[cam].shape
    uv, z = fr.project(cam, X); uv = uv * SC
    ok = (z > 0.3) & (uv[:, 0] >= 1) & (uv[:, 0] < w - 2) & (uv[:, 1] >= 1) & (uv[:, 1] < h - 2)
    idx = np.nonzero(ok)[0]; idx = idx[np.argsort(-z[idx])]
    img = np.zeros((h, w), np.float32); cnt = np.zeros((h, w), np.float32)
    xi = np.round(uv[idx, 0]).astype(int); yi = np.round(uv[idx, 1]).astype(int)
    img[yi, xi] = G[idx]; cnt[yi, xi] = 1
    return img, cnt
def cost(p, verbose=False):
    X = apply(p, Q0); tot = 0.0; n = 0
    for cam in CAMS:
        img, cnt = synth(cam, X)
        k = cv2.dilate(cnt, np.ones((5, 5), np.uint8))
        a_ = cv2.GaussianBlur(img * cnt, (0, 0), 2.0); wsum = cv2.GaussianBlur(cnt, (0, 0), 2.0)
        sm = a_ / np.maximum(wsum, 1e-3)
        mask = (cv2.erode(k, np.ones((3, 3), np.uint8)) > 0) & (wsum > 0.08)
        if mask.sum() < 500: continue
        ph = photos[cam]
        x1 = sm[mask]; x2 = ph[mask]
        x1 = x1 - x1.mean(); x2 = x2 - x2.mean()
        ncc = float((x1 * x2).sum() / (np.sqrt((x1 * x1).sum() * (x2 * x2).sum()) + 1e-9))
        if verbose: print('  ', cam, 'NCC', round(ncc, 3), 'px', int(mask.sum()))
        tot += ncc; n += 1
    return -tot / max(n, 1)
p0 = np.array([float(sys.argv[2]) if len(sys.argv) > 2 else 1.0, 0.0, 0.0, 0.0, 0.0])
t0 = time.time(); print('costo iniziale', cost(p0, True), round(time.time() - t0, 1), 's')
best = p0.copy(); bc = cost(p0)
steps = [np.array([0.01, 0.01, 0.04, 0.03, 0.04]), np.array([0.005, 0.005, 0.02, 0.015, 0.02]), np.array([0.0025, 0.0025, 0.01, 0.008, 0.01]), np.array([0.001, 0.001, 0.005, 0.004, 0.005])]
for st in steps:
    for it in range(8):
        improved = False
        for i in range(1, 5):
            for sg in (-1, 1):
                q = best.copy(); q[i] += sg * st[i]
                c = cost(q)
                if c < bc - 1e-5: bc = c; best = q; improved = True
        if not improved: break
    print('passo', st, '->', best.round(4), 'costo', round(bc, 4), round(time.time() - t0), 's', flush=True)
print('finale'); cost(best, True)
np.save('/tmp/claude-0/s/splat/V3_photo_align_s1.npy', best)
