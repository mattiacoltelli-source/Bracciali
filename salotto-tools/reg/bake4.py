"""Bake di texture da piu' foto su superfici arbitrarie (muri, pavimento, facce dei mobili), con occlusione a scatole."""
import sys, time
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
from bake2 import remap

def box_hit(C, P, boxes, skip=None):
    """True per i punti P che dalla camera C sono nascosti da una delle scatole (lo,hi)."""
    hit = np.zeros(len(P), bool)
    d = P - C
    with np.errstate(divide='ignore', invalid='ignore'):
        for b in boxes:
            if skip is not None and b.get('name') == skip: continue
            lo, hi = np.array(b['min'], float), np.array(b['max'], float)
            t1 = (lo - C) / d; t2 = (hi - C) / d
            tmin = np.nanmax(np.minimum(t1, t2), axis=1); tmax = np.nanmin(np.maximum(t1, t2), axis=1)
            tmin = np.nan_to_num(tmin, nan=-1); tmax = np.nan_to_num(tmax, nan=-1)
            hit |= (tmax >= np.maximum(tmin, 0.0)) & (tmin < 0.985)
    return hit

def view_weight(fr, n, P, normal, uv, z, img_shape, margin=60.0, cos_pow=1.5, dist_pow=1.0, min_cos=0.12):
    C = fr.cams[n]['C']
    v = C - P
    d = np.linalg.norm(v, axis=1)
    cosv = (v @ normal) / np.maximum(d, 1e-6)
    h, w = img_shape[:2]
    inside = (z > 0.1) & (uv[:, 0] >= 0) & (uv[:, 0] < w - 1) & (uv[:, 1] >= 0) & (uv[:, 1] < h - 1)
    edge = np.minimum.reduce([uv[:, 0], w - 1 - uv[:, 0], uv[:, 1], h - 1 - uv[:, 1]])
    fall = np.clip(edge / margin, 0, 1); fall = fall * fall * (3 - 2 * fall)
    facing = np.clip((cosv - min_cos) / 0.45, 0, 1)
    return inside * (cosv > 0.05) * fall * facing * (np.maximum(cosv, 0) ** cos_pow) / np.maximum(d, 0.4) ** dist_pow

def solve_gains(layers, cams, tag='', verbose=True):
    gains = {n: np.ones(3) for n in cams}
    idx = {n: i for i, n in enumerate(cams)}
    rows, rhs, wts = [], [], []
    for a in range(len(cams)):
        for b in range(a + 1, len(cams)):
            ca, wa = layers[cams[a]]; cb, wb = layers[cams[b]]
            m = (wa > 0.05 * wa.max() + 1e-12) & (wb > 0.05 * wb.max() + 1e-12)
            if m.sum() < 400: continue
            ra = np.log(np.maximum(np.median(ca[m], axis=0), 1.0)); rb = np.log(np.maximum(np.median(cb[m], axis=0), 1.0))
            rows.append((a, b)); rhs.append(rb - ra); wts.append(np.sqrt(m.sum()))
    if rows:
        A = np.zeros((len(rows) + 1, len(cams))); y = np.zeros((len(rows) + 1, 3))
        for k, ((a, b), r_, w_) in enumerate(zip(rows, rhs, wts)):
            A[k, a] = w_; A[k, b] = -w_; y[k] = r_ * w_
        A[-1, :] = 0.05
        sol = np.linalg.lstsq(A, y, rcond=None)[0]
        for n in cams: gains[n] = np.exp(sol[idx[n]])
        if verbose: print(tag, 'guadagni:', {n: np.round(g, 2).tolist() for n, g in gains.items() if abs(g - 1).max() > 0.02}, flush=True)
    return gains

def bake(fr, P, normal, shape, cams=None, boxes=None, skip=None, scale=0.5, power=3.0, smooth=0, gain=True, tag='', verbose=True, cos_pow=1.5, dist_pow=1.0, margin=60.0, min_cos=0.12, exclude=()):
    """Ritorna (immagine uint8 BGR, valid bool, tot pesi)."""
    ny, nx = shape
    cams = [n for n in (cams or sorted(fr.cams)) if n not in exclude]
    normal = np.asarray(normal, float)
    layers = {}
    for n in cams:
        img = fr.image(n, scale)
        uv, z = fr.project(n, P); uv = uv * scale
        w = view_weight(fr, n, P, normal, uv, z, img.shape, margin=margin, cos_pow=cos_pow, dist_pow=dist_pow, min_cos=min_cos)
        if boxes: w = w * (~box_hit(fr.cams[n]['C'], P, boxes, skip))
        wm = w.reshape(ny, nx).astype(np.float32)
        if wm.max() <= 0: continue
        col = remap(img, uv, (ny, nx)).astype(np.float32)
        if smooth > 0:   # sfuma i pesi ma solo dentro la zona visibile: niente aloni dove la vista e' occlusa o fuori dall'immagine
            k = int(2 * smooth) * 2 + 1
            vis = cv2.erode((wm > 0).astype(np.uint8), np.ones((k, k), np.uint8)).astype(np.float32)
            wm = cv2.GaussianBlur(wm, (0, 0), smooth) * vis
        layers[n] = (col, wm)
        if verbose: print(tag, n, 'cop', round(float((wm > 0).mean()), 3), flush=True)
    cams = list(layers)
    if not cams: return np.zeros((ny, nx, 3), np.uint8), np.zeros((ny, nx), bool), np.zeros((ny, nx))
    gains = solve_gains(layers, cams, tag, verbose) if gain and len(cams) > 1 else {n: np.ones(3) for n in cams}
    acc = np.zeros((ny, nx, 3), np.float64); tot = np.zeros((ny, nx), np.float64)
    for n in cams:
        col, wm = layers[n]
        wp = wm.astype(np.float64) ** power
        acc += (col * gains[n][None, None, :]) * wp[..., None]; tot += wp
    out = acc / np.maximum(tot, 1e-30)[..., None]
    valid = tot > 1e-12 * max(1.0, tot.max()) * 1e-3
    return np.clip(out, 0, 255).astype(np.uint8), valid, tot

def wall_points(fr, wid, ppm, y_top=None):
    from bake2 import wall_def
    O, U, N, length = wall_def(fr, wid)
    nx, ny = int(round(length * ppm)), int(round(fr.H * ppm))
    us = (np.arange(nx) + 0.5) / ppm; ys = fr.H - (np.arange(ny) + 0.5) / ppm
    UU, YY = np.meshgrid(us, ys)
    P = O[None, :] + UU.reshape(-1, 1) * U[None, :] + np.stack([np.zeros(UU.size), YY.ravel(), np.zeros(UU.size)], 1)
    return P, N, (ny, nx)

def floor_points(fr, ppm, y=0.0):
    nx, nz = int(round(fr.L * ppm)), int(round(fr.W * ppm))
    xs = (np.arange(nx) + 0.5) / ppm; zs = (np.arange(nz) + 0.5) / ppm
    X, Z = np.meshgrid(xs, zs)
    return np.stack([X.ravel(), np.full(X.size, y), Z.ravel()], 1), (nz, nx)
