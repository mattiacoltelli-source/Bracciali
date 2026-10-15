import os
import sys
sys.path.insert(0, '/tmp/claude-0/s/splat')
import numpy as np, spzload
path = os.environ['SPZ_FILE']
tf = np.load('/tmp/claude-0/s/splat/V3_tf.npz'); th, a, b, FL = float(tf['th']), float(tf['offW']), float(tf['offF']), float(tf['FL'])
par = np.load('/tmp/claude-0/s/splat/V3_photo_align_s1.npy')
nx = np.array([np.cos(th), np.sin(th)]); nzm = np.array([np.cos(th - np.pi / 2), np.sin(th - np.pi / 2)])
g = spzload.load(path); P = g['pos']; C = g['rgb']; A = g['alpha']; S = g['scale']
med = np.median(P, axis=0); r = np.linalg.norm(P - med, axis=1)
m = (r < 9) & (A > 0.4); P, C, S = P[m], C[m], S[m]
xz = P[:, [0, 2]]
Q = np.stack([xz @ nx - a + 7.1, P[:, 1] - FL, 4.5 - (xz @ nzm - b)], 1)
c0 = np.array([5.3, 1.0, 3.0]); s_, yaw, tx, ty, tz = par; cs, sn = np.cos(yaw), np.sin(yaw)
Y = (Q - c0) * s_; Q = np.stack([cs * Y[:, 0] + sn * Y[:, 2], Y[:, 1], -sn * Y[:, 0] + cs * Y[:, 2]], 1) + c0 + np.array([tx, ty, tz])
np.savez_compressed('/tmp/claude-0/s/splat/V3_room.npz', Q=Q.astype(np.float32), C=C.astype(np.float32), S=S.astype(np.float32))
print('V3_room', len(Q))
sel = (Q[:, 0] > 3.2) & (Q[:, 0] < 4.6) & (Q[:, 2] > 3.1) & (Q[:, 2] < 4.55) & (Q[:, 1] > 0.0) & (Q[:, 1] < 0.9)
print('zona tavolino/totem', sel.sum())
import cv2
Qs, Cs = Q[sel], C[sel]
def view(ax_h, ax_v, rng_h, rng_v, ppm, name, dax, dsign, flip=True):
    W = int((rng_h[1] - rng_h[0]) * ppm); H = int((rng_v[1] - rng_v[0]) * ppm)
    img = np.zeros((H, W, 3), np.uint8); zb = np.full((H, W), -1e9, np.float32)
    x = ((Qs[:, ax_h] - rng_h[0]) * ppm).astype(int); y = ((Qs[:, ax_v] - rng_v[0]) * ppm).astype(int); y = H - 1 - y if flip else y
    d = dsign * Qs[:, dax]; ok = (x >= 0) & (x < W) & (y >= 0) & (y < H)
    for k in np.argsort(d):
        if ok[k] and d[k] >= zb[y[k], x[k]]: zb[y[k], x[k]] = d[k]; img[y[k], x[k]] = (Cs[k][::-1] * 255).astype(np.uint8)
    img = cv2.dilate(img, np.ones((2, 2), np.uint8))
    for a_ in np.arange(np.ceil(rng_h[0] * 10) / 10, rng_h[1], 0.1):
        X = int((a_ - rng_h[0]) * ppm); cv2.line(img, (X, 0), (X, 8), (0, 255, 255), 1); cv2.putText(img, f'{a_:.1f}', (X + 2, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    for b_ in np.arange(np.ceil(rng_v[0] * 10) / 10, rng_v[1], 0.1):
        Y = int((b_ - rng_v[0]) * ppm); Y = H - 1 - Y if flip else Y
        cv2.line(img, (0, Y), (8, Y), (0, 255, 255), 1); cv2.putText(img, f'{b_:.1f}', (10, Y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    cv2.imwrite(name, img); print(name, img.shape)
view(0, 1, (3.2, 4.6), (0.0, 0.9), 500, '/tmp/claude-0/s/sofa/tav_front.png', 2, 1)      # dal lato z grande (parete F) verso la TV: x orizzontale, y verticale, vicino = z grande
view(2, 1, (3.1, 4.55), (0.0, 0.9), 500, '/tmp/claude-0/s/sofa/tav_side.png', 0, 1)
