"""Seconda parte: impronta, riempimento buchi, levigatura, colori. Uso: python3 -I sofa_hf2.py <spz>"""
import os, sys, time
sys.path.insert(0, '/tmp/claude-0/s/splat'); sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2, spzload
from scipy.spatial import cKDTree
from fill import push_pull
path = sys.argv[1]
d = np.load('/tmp/claude-0/s/sofa/hf_raw.npz'); H = d['H']; Hn = d['Hn']; X0 = float(d['X0']); Z0 = float(d['Z0']); CELL = float(d['CELL'])
nzc, nxc = H.shape
# --- impronta ---
ZMAX = 4.43
zc = Z0 + (np.arange(nzc) + 0.5) * CELL
fp = ((np.nan_to_num(H, nan=0) > 0.30) & (zc[:, None] < ZMAX)).astype(np.uint8)
fp = cv2.morphologyEx(fp, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
n, lab, stats, _ = cv2.connectedComponentsWithStats(fp, connectivity=4)
big = max(range(1, n), key=lambda i: stats[i, cv2.CC_STAT_AREA]); print('componente principale', stats[big, cv2.CC_STAT_AREA], 'celle')
fp = (lab == big).astype(np.uint8)
# riempi i buchi interni
ff = fp.copy(); mask = np.zeros((nzc + 2, nxc + 2), np.uint8)
inv = (1 - fp).astype(np.uint8); cv2.floodFill(inv, mask, (0, 0), 2)
holes = (inv == 1); fp[holes] = 1
fp = cv2.morphologyEx(fp, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
fp = (cv2.GaussianBlur(fp.astype(np.float32), (0, 0), 3.0) > 0.5).astype(np.uint8)
# contorno rettilineo: il divano e' fatto di rettangoli. Blocchi di 4,5 cm (3 celle) a maggioranza, piu' lo schienale intero (scatola misurata)
bs = 3
hh_, ww_ = fp.shape
small = cv2.resize(fp.astype(np.float32), (ww_ // bs, hh_ // bs), interpolation=cv2.INTER_AREA) > 0.5
fp = cv2.resize(small.astype(np.uint8), (ww_ // bs * bs, hh_ // bs * bs), interpolation=cv2.INTER_NEAREST)
fp = np.pad(fp, ((0, hh_ - fp.shape[0]), (0, ww_ - fp.shape[1])))
xs_c = X0 + (np.arange(nxc) + 0.5) * CELL
# schienale: da x 4.98 a 6.79, da z 4.08 al muro (4.5) meno 4 cm
bx = (xs_c >= 4.98) & (xs_c <= 6.79); bz = (zc >= 4.08) & (zc <= 4.46)
fp[np.ix_(bz, bx)] = 1
fp = fp.astype(np.uint8)
print('celle impronta', int(fp.sum()))
# --- quote: tolgo i valori fuori dall'impronta, riempio i buchi con push-pull, poi levigo preservando i salti ---
H0 = H; H = Hn
valid = np.isfinite(H) & (fp > 0) & (np.nan_to_num(H, nan=0) > 0.28)
w = valid.astype(np.float32)
# tolgo i punti isolati alti: mediana locale
Hm = np.where(valid, H, 0).astype(np.float32)
med = cv2.medianBlur((np.clip(Hm / 1.275, 0, 1) * 255).astype(np.uint8), 5).astype(np.float32) / 255 * 1.275
bad = valid & (np.abs(H - med) > 0.10)
w[bad] = 0
fill = push_pull(np.dstack([np.where(w > 0, H, 0)] * 3).astype(np.float32), w, levels=7)[..., 0]
Hf = np.where(w > 0, H, fill).astype(np.float32)
Hf = np.where(fp > 0, Hf, 0)
# bilaterale (preserva i gradini del divano)
Hs = cv2.bilateralFilter(Hf, d=7, sigmaColor=0.04, sigmaSpace=2.0)
Hs = np.where(fp > 0, Hs, 0).astype(np.float32)
Hs = np.clip(Hs, 0, 1.2)
np.savez_compressed('/tmp/claude-0/s/sofa/hf_fill.npz', H=Hs, fp=fp, X0=X0, Z0=Z0, CELL=CELL)
v = np.clip(Hs / 1.1, 0, 1)
col = cv2.applyColorMap((v * 255).astype(np.uint8), cv2.COLORMAP_JET); col[fp == 0] = 0
cv2.imwrite('/tmp/claude-0/s/sofa/hf_fill.png', cv2.resize(col, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
print('H min/max nell\'impronta', float(Hs[fp > 0].min()), float(Hs[fp > 0].max()))
