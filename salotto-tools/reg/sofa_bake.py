"""Texture del divano (campo di quote) dalle foto: ogni texel (1 cm) sta sulla superficie del divano; peso per vista (angolo, distanza, bordo),
occlusione dal campo di quote stesso e dagli altri mobili, guadagni di esposizione per camera.
Uso: python3 sofa_bake.py [scala_foto=0.5] [tag=v1]"""
import os, sys, time
os.environ.setdefault('FRAME_EXT', '1')
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
from bake2 import remap
from bake4 import view_weight, solve_gains, box_hit
from cams_sel import select
from fill import push_pull
from scene_def import BOXES

scale = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
tag = sys.argv[2] if len(sys.argv) > 2 else 'v1'
d = np.load('/tmp/claude-0/s/reg/out/sofa_hf_final.npz')
H2 = d['H'].astype(np.float32); fp2 = d['fp'].astype(bool); X0 = float(d['X0']); Z0 = float(d['Z0']); CELL = float(d['CELL'])
nz2, nx2 = H2.shape
# estendo le quote oltre l'impronta (il bordo non deve scendere a 0 quando si interpola)
w = fp2.astype(np.float32)
Hx = push_pull(np.dstack([np.where(fp2, H2, 0)] * 3).astype(np.float32), w, levels=6)[..., 0]
Hx = np.where(fp2, H2, Hx).astype(np.float32)
UP = int(os.environ.get("SOFA_UP", 2))
Hup = cv2.resize(Hx, (nx2 * UP, nz2 * UP), interpolation=cv2.INTER_LINEAR)
fpu = cv2.resize(fp2.astype(np.uint8), (nx2 * UP, nz2 * UP), interpolation=cv2.INTER_NEAREST) > 0
nzu, nxu = Hup.shape; cu = CELL / UP
xs = X0 + (np.arange(nxu) + 0.5) * cu; zs = Z0 + (np.arange(nzu) + 0.5) * cu
XX, ZZ = np.meshgrid(xs, zs)
P = np.stack([XX.ravel(), Hup.ravel(), ZZ.ravel()], 1)
# normali dal gradiente della quota levigata
Hs = cv2.GaussianBlur(Hup, (0, 0), 2.0)
gz, gx = np.gradient(Hs, cu)
Nrm = np.stack([-gx.ravel(), np.ones(Hs.size), -gz.ravel()], 1); Nrm /= np.linalg.norm(Nrm, axis=1, keepdims=True)

def hf_occluded(C, P, nsteps=56, tol=0.025):
    """True dove il segmento camera->punto passa sotto la superficie del divano (campo di quote a 2 cm)."""
    n = len(P); occ = np.zeros(n, bool)
    dvec = P - C
    L = np.linalg.norm(dvec, axis=1)
    ts = np.linspace(0.02, 1.0, nsteps, endpoint=False)
    Hmax = float(Hx.max())
    for t in ts:
        S = C + dvec * t
        # il campione piu' vicino alla superficie del punto non conta (rumore): niente controllo negli ultimi 4 cm
        near = (1 - t) * L < 0.04
        ix = np.floor((S[:, 0] - X0) / CELL).astype(int); iz = np.floor((S[:, 2] - Z0) / CELL).astype(int)
        ok = (ix >= 0) & (ix < nx2) & (iz >= 0) & (iz < nz2) & (S[:, 1] < Hmax + 0.02) & ~near
        if not ok.any(): continue
        h = np.zeros(n, np.float32); h[ok] = np.where(fp2[iz[ok], ix[ok]], H2[iz[ok], ix[ok]], 0)
        occ |= ok & (S[:, 1] < h - tol)
    return occ

fr = FR(); names = select(fr)
others = [dict(min=b['min'], max=b['max'], name=b['name']) for b in BOXES if not b['name'].startswith('s_')]
others = [dict(min=(np.array(b['min']) - 0.01).tolist(), max=(np.array(b['max']) + 0.01).tolist(), name=b['name']) for b in others]
layers = {}; t0 = time.time()
for n in names:
    img = fr.image(n, scale)
    uv, z = fr.project(n, P); uv = uv * scale
    wv = view_weight(fr, n, P, Nrm, uv, z, img.shape, margin=40.0, cos_pow=1.0, dist_pow=1.0, min_cos=0.10) if False else None
    C = fr.cams[n]['C']
    v = C - P; dist = np.linalg.norm(v, axis=1); cosv = (v * Nrm).sum(1) / np.maximum(dist, 1e-6)
    h_, w_ = img.shape[:2]
    inside = (z > 0.1) & (uv[:, 0] >= 0) & (uv[:, 0] < w_ - 1) & (uv[:, 1] >= 0) & (uv[:, 1] < h_ - 1)
    edge = np.minimum.reduce([uv[:, 0], w_ - 1 - uv[:, 0], uv[:, 1], h_ - 1 - uv[:, 1]])
    fall = np.clip(edge / 40.0, 0, 1); fall = fall * fall * (3 - 2 * fall)
    facing = np.clip((cosv - 0.10) / 0.45, 0, 1)
    wv = inside * (cosv > 0.05) * fall * facing * (np.maximum(cosv, 0) ** 1.0) / np.maximum(dist, 0.4)
    wv = wv * fpu.ravel()
    if (wv > 0).sum() < 2000: continue
    cand = wv > 0
    occ = np.zeros(len(P), bool)
    occ[cand] = hf_occluded(C, P[cand]) | box_hit(C, P[cand], others)
    wv = wv * (~occ)
    wm = wv.reshape(nzu, nxu).astype(np.float32)
    if wm.max() <= 0: continue
    k = 9
    vis = cv2.erode((wm > 0).astype(np.uint8), np.ones((k, k), np.uint8)).astype(np.float32)
    wm = cv2.GaussianBlur(wm, (0, 0), 1.5) * vis
    col = remap(img, uv, (nzu, nxu)).astype(np.float32)
    layers[n] = (col, wm)
    print(n, 'copertura', round(float((wm > 0)[fpu].mean()), 3), round(time.time() - t0), 's', flush=True)
cams = list(layers)
gains = solve_gains(layers, cams, 'divano', True)
acc = np.zeros((nzu, nxu, 3), np.float64); tot = np.zeros((nzu, nxu), np.float64)
for n in cams:
    col, wm = layers[n]; wp = wm.astype(np.float64) ** 3.0
    acc += (col * gains[n][None, None, :]) * wp[..., None]; tot += wp
out = (acc / np.maximum(tot, 1e-30)[..., None]).clip(0, 255).astype(np.uint8)
valid = (tot > 1e-12 * max(1.0, tot.max()) * 1e-3) & fpu
# sotto i cuscini (oggetti a parte) la superficie del divano non si vede: quei texel si riempiono dai dintorni
import json
cush = json.load(open('/tmp/claude-0/s/sofa/cushions_fit.json'))
cm = np.zeros((nzu, nxu), np.uint8)
for c in cush:
    ax = np.array(c['axes']); cen = np.array(c['c']); hs = np.array(c['size']) * 1.06 / 2 + 0.03
    corners = np.array([[sx * hs[0], sy * hs[1], sz * hs[2]] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    Wc = cen + corners @ ax
    pxz = np.stack([((Wc[:, 0] - X0) / cu), ((Wc[:, 2] - Z0) / cu)], 1).astype(np.int32)
    cv2.fillConvexPoly(cm, cv2.convexHull(pxz), 1)
valid &= ~(cm > 0)
print('texel validi', round(float(valid[fpu].mean()), 3), 'su', int(fpu.sum()))
np.savez_compressed(f'/tmp/claude-0/s/reg/out/sofa_bake_{tag}.npz', img=out, valid=valid, fp=fpu, Hup=Hup, X0=X0, Z0=Z0, cu=cu)
vis_img = out.copy(); vis_img[~valid & fpu] = (0, 0, 255); vis_img[~fpu] = (60, 60, 60)
cv2.imwrite(f'/tmp/claude-0/s/reg/out/sofa_bake_{tag}.jpg', cv2.resize(vis_img, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR), [cv2.IMWRITE_JPEG_QUALITY, 90])
