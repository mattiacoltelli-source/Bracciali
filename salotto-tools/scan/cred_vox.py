"""Oggetti sopra la credenza (vaso, portabottiglie, ciotola...): voxel da 6 mm dal primo scan registrato."""
import os
import sys, json
sys.path.insert(0, '/tmp/claude-0/s/splat')
import numpy as np, spzload, cv2
from scipy.ndimage import convolve
path = os.environ['SPZ_FILE']
w = np.load('/tmp/claude-0/s/splat/V1_geo.npz'); n = w['n']; off = float(w['off']); FL = float(w['FL'])
t = np.array([-n[1], n[0]])
par = np.load('/tmp/claude-0/s/splat/V1_align.npy')
g = spzload.load(path); P = g['pos']; C = g['rgb']; A = g['alpha']; S = g['scale']
med = np.median(P, axis=0); r = np.linalg.norm(P - med, axis=1)
m = (r < 8) & (A > 0.4); P, C, S = P[m], C[m], S[m]
v = off - (P[:, [0, 2]] @ n)
if (v > 0).sum() < (v < 0).sum(): v = -v
u = P[:, [0, 2]] @ t
Q = np.stack([v, P[:, 1] - FL, 3.788 - u], 1)
c0 = np.array([0.3, 1.0, 1.4]); s_, yaw, tx, ty, tz = par; cs, sn = np.cos(yaw), np.sin(yaw)
Y = (Q - c0) * s_; Q = np.stack([cs * Y[:, 0] + sn * Y[:, 2], Y[:, 1], -sn * Y[:, 0] + cs * Y[:, 2]], 1) + c0 + np.array([tx, ty, tz])
Q[:, 1] -= 0.025      # il piano della credenza (0.825 dopo l'allineamento) va a 0.80 come misurato sulle foto
np.savez_compressed('/tmp/claude-0/s/splat/V1_room.npz', Q=Q.astype(np.float32), C=C.astype(np.float32), S=S.astype(np.float32))
# quota del piano della credenza dopo l'allineamento
st = (Q[:, 0] > 0.1) & (Q[:, 0] < 0.4) & (Q[:, 2] > 1.2) & (Q[:, 2] < 1.5) & (Q[:, 1] > 0.7) & (Q[:, 1] < 0.9)
hh, e = np.histogram(Q[st, 1], bins=np.arange(0.7, 0.9, 0.005)); print('quota piano (allineato):', ' '.join(f'{e[i]:.3f}:{hh[i]}' for i in range(len(hh)) if hh[i] > 40))
st2 = (np.abs(Q[:, 1] - 0.80) < 0.02) & (Q[:, 2] > 1.2) & (Q[:, 2] < 1.5) & (Q[:, 0] > -0.1) & (Q[:, 0] < 0.8)
hh, e = np.histogram(Q[st2, 0], bins=np.arange(-0.1, 0.8, 0.02)); print('profilo x del piano:', ' '.join(f'{e[i]:.2f}:{hh[i]}' for i in range(len(hh)) if hh[i] > 15))
TOP = 0.80
CELL = 0.010
X0, X1, Y0, Y1, Z0, Z1 = 0.05, 0.50, TOP + 0.004, 1.40, 0.30, 2.35
sel = (Q[:, 0] > X0) & (Q[:, 0] < X1) & (Q[:, 1] > Y0) & (Q[:, 1] < Y1) & (Q[:, 2] > Z0) & (Q[:, 2] < Z1)
# il quadro Sneaker (appoggiato al muro) e' un oggetto a parte
paint = (Q[:, 0] < 0.17) & (Q[:, 2] > 0.70) & (Q[:, 2] < 1.55) & (Q[:, 1] > 0.80) & (Q[:, 1] < 1.40)
sel &= ~paint
Pq = Q[sel]; Cs = C[sel]
print('punti candidati', len(Pq))
ix = np.floor((Pq[:, 0] - X0) / CELL).astype(int); iy = np.floor((Pq[:, 1] - Y0) / CELL).astype(int); iz = np.floor((Pq[:, 2] - Z0) / CELL).astype(int)
nx, ny, nz = ix.max() + 1, iy.max() + 1, iz.max() + 1; print('griglia', nx, ny, nz)
cnt = np.zeros((nx, ny, nz), np.float32); acc = np.zeros((nx, ny, nz, 3), np.float32)
np.add.at(cnt, (ix, iy, iz), 1.0)
for k in range(3): np.add.at(acc[..., k], (ix, iy, iz), Cs[:, k])
occ = cnt >= 1
from scipy.ndimage import binary_closing
occ = binary_closing(occ, structure=np.ones((3, 3, 3), bool), iterations=1) | occ
nb = convolve(occ.astype(np.float32), np.ones((3, 3, 3), np.float32), mode='constant') - occ
occ &= nb >= 4
# colori: media dei punti nel voxel; per i voxel di chiusura (senza punti) prendo il colore dei vicini
colg = np.zeros((nx, ny, nz, 3), np.float32); have = cnt > 0
colg[have] = acc[have] / cnt[have][:, None]
from scipy.ndimage import distance_transform_edt
if (~have & occ).any():
    _, inds = distance_transform_edt(~have, return_indices=True)
    colg = colg[inds[0], inds[1], inds[2]]
acc = colg; cnt = np.ones_like(cnt)
print('voxel occupati', int(occ.sum()))
from scipy.ndimage import binary_erosion
occ = occ & ~binary_erosion(occ, structure=np.array([[[0,0,0],[0,1,0],[0,0,0]],[[0,1,0],[1,1,1],[0,1,0]],[[0,0,0],[0,1,0],[0,0,0]]], bool), border_value=0)   # solo la superficie
print('voxel di superficie', int(occ.sum()))
ii = np.argwhere(occ); col = np.clip(acc[occ] * 255, 0, 255).astype(np.uint8)
rec = np.zeros((len(ii), 9), np.uint8)
for j in range(3):
    rec[:, 2 * j] = (ii[:, j] & 255); rec[:, 2 * j + 1] = (ii[:, j] >> 8)
rec[:, 6:9] = col
open('/tmp/claude-0/s/sofa/vox_credenza.bin', 'wb').write(rec.tobytes())
meta = dict(x0=X0, y0=Y0, z0=Z0, cell=CELL, n=int(len(ii)))
json.dump(meta, open('/tmp/claude-0/s/sofa/vox_credenza.json', 'w')); print(meta)
# anteprima dalla stanza (x verso la parete -> guardo con z orizzontale)
W_ = nz; H_ = ny
img = np.zeros((H_, W_, 3), np.uint8); zb = np.full((H_, W_), 1e9)
for (a, b_, c_), cc in zip(ii, col):
    if a < zb[b_, c_]: zb[b_, c_] = a; img[H_ - 1 - b_, c_] = cc[::-1]
cv2.imwrite('/tmp/claude-0/s/sofa/vox_cred_preview.png', cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
