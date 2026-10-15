"""Oggetti sopra la console: voxel da 6 mm ricavati dalla scansione registrata. Scrive vox.bin (u16 ix,iy,iz + rgb = 9 byte) e vox_meta.json."""
import sys, json
import numpy as np
from scipy.ndimage import convolve
d = np.load('/tmp/claude-0/s/splat/V5_room.npz'); Q = d['Q']; C = d['C']; S = d['S']
CELL = 0.006
X0, X1, Y0, Y1, Z0, Z1 = 6.84, 7.07, 0.778, 1.40, 2.70, 4.30
sel = (Q[:, 0] > X0) & (Q[:, 0] < X1) & (Q[:, 1] > Y0) & (Q[:, 1] < Y1) & (Q[:, 2] > Z0) & (Q[:, 2] < Z1)
P = Q[sel]; Cs = C[sel]; Ss = S[sel].mean(1)
print('punti candidati', len(P), '| scala splat mediana', float(np.median(Ss)))
ix = np.floor((P[:, 0] - X0) / CELL).astype(int); iy = np.floor((P[:, 1] - Y0) / CELL).astype(int); iz = np.floor((P[:, 2] - Z0) / CELL).astype(int)
nx, ny, nz = ix.max() + 1, iy.max() + 1, iz.max() + 1
print('griglia', nx, ny, nz)
cnt = np.zeros((nx, ny, nz), np.float32); acc = np.zeros((nx, ny, nz, 3), np.float32)
np.add.at(cnt, (ix, iy, iz), 1.0)
for k in range(3): np.add.at(acc[..., k], (ix, iy, iz), Cs[:, k])
occ = cnt >= 2
# i punti isolati (nessun vicino entro 1 voxel) sono rumore
nb = convolve(occ.astype(np.float32), np.ones((3, 3, 3), np.float32), mode='constant') - occ
occ &= nb >= 3
print('voxel occupati', int(occ.sum()))
ii = np.argwhere(occ)
col = (acc[occ] / cnt[occ][:, None])
col = np.clip(col * 255, 0, 255).astype(np.uint8)
rec = np.zeros((len(ii), 9), np.uint8)
for j in range(3):
    rec[:, 2 * j] = (ii[:, j] & 255); rec[:, 2 * j + 1] = (ii[:, j] >> 8)
rec[:, 6:9] = col
open('/tmp/claude-0/s/sofa/vox.bin', 'wb').write(rec.tobytes())
meta = dict(x0=X0, y0=Y0, z0=Z0, cell=CELL, n=int(len(ii)))
json.dump(meta, open('/tmp/claude-0/s/sofa/vox_meta.json', 'w')); print(meta)
# anteprima: vista dalla stanza
import cv2
W = nz; H = ny
img = np.zeros((H, W, 3), np.uint8); zb = np.full((H, W), 1e9)
for (a, b, c_), cc in zip(ii, col):
    if a < zb[b, c_]: zb[b, c_] = a; img[H - 1 - b, c_] = cc[::-1]
cv2.imwrite('/tmp/claude-0/s/sofa/vox_preview.png', cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
