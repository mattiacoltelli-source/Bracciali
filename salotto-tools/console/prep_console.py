"""Prepara i ritagli (colore + maschera) degli oggetti sopra la console dalle foto ravvicinate. Scrive in ASSETS (fuori dal repository: sono foto di casa)."""
import sys, os, json
sys.path.insert(0, '/tmp/claude-0/s/st3')
from seglib import *
A = '/tmp/claude-0/s/st3/assets'; os.makedirs(A, exist_ok=True)
params = {}

def keep_largest(m, extra_cut_row=None):
    n, lab, st, _ = cv2.connectedComponentsWithStats((m > 127).astype(np.uint8))
    k = 1 + np.argmax(st[1:, 4]); out = ((lab == k) * 255).astype(np.uint8)
    if extra_cut_row is not None: out[extra_cut_row:, :] = 0
    return out

def save(name, c, m, **kw):
    cv2.imwrite(f'{A}/{name}_rgb.png', c); cv2.imwrite(f'{A}/{name}_mask.png', m); params[name] = kw
    overlay(c, m, f'/tmp/claude-0/s/st3/work/fin_{name}.jpg'); print(name, c.shape, int((m > 0).sum()))

im1, s1 = load('df1f1615'); im2, s2 = load('da59d0fd')
def crop(im, s, box): x0, y0, x1, y1 = [int(v * s) for v in box]; return im[y0:y1, x0:x1].copy(), (x0, y0)

# --- Art ---
box = (195, 225, 385, 440); c, o = crop(im1, s1, box); m = cv2.imread('work/mask_art.png', 0)
cut = int((423 - box[1]) * s1); m = keep_largest(m, cut)
save('art', c, m, src='df1f1615', s=s1, base_px=[(262 - box[0]) * s1, cut], top_row=(243 - box[1]) * s1, height_m=0.094)
# --- Pennywise (corpo, sopra la pozza) ---
box = (690, 225, 895, 490); c, o = crop(im1, s1, box); m = cv2.imread('work/mask_pw.png', 0)
cut = int((432 - box[1]) * s1); m = keep_largest(m, cut)
save('pw', c, m, src='df1f1615', s=s1, base_px=[(808 - box[0]) * s1, cut], top_row=(243 - box[1]) * s1, height_m=0.105)
# --- Mandalorian (sopra la base) ---
box = (225, 335, 345, 525); c, o = crop(im2, s2, box); m = cv2.imread('work/mask_mando.png', 0)
cut = int((488 - box[1]) * s2); m = keep_largest(m, cut)
save('mando', c, m, src='da59d0fd', s=s2, base_px=[(286 - box[0]) * s2, cut], top_row=(346 - box[1]) * s2, height_m=0.094)
json.dump(params, open(f'{A}/params.json', 'w'), indent=1)
