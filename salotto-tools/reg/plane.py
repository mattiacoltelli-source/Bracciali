"""Strumenti per piani arbitrari: immagine "messa a fuoco" su un piano e misura di coerenza tra le viste (plane sweep)."""
import sys
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from frame import make_frame
from bake3 import view_w
from bake2 import remap

_fr = None
def FR():
    global _fr
    if _fr is None: _fr = make_frame()
    return _fr

def grid_points(axis, value, a_rng, b_rng, ppm):
    """axis: 'x','y','z' = coordinata fissa. a,b = le altre due nell'ordine (x,y,z). Ritorna P (Nx3), shape (nb, na), asse a, asse b."""
    ia, ib = [i for i in range(3) if 'xyz'[i] != axis]
    na = int(round((a_rng[1] - a_rng[0]) * ppm)); nb = int(round((b_rng[1] - b_rng[0]) * ppm))
    A = a_rng[0] + (np.arange(na) + 0.5) / ppm
    B = b_rng[1] - (np.arange(nb) + 0.5) / ppm      # la riga 0 e' in alto (b massimo): per y e' naturale; per z: 0 in alto = z massimo
    AA, BB = np.meshgrid(A, B)
    P = np.zeros((AA.size, 3)); P[:, 'xyz'.index(axis)] = value; P[:, ia] = AA.ravel(); P[:, ib] = BB.ravel()
    return P, (nb, na), ia, ib

def sample_views(P, normal, shape, cams=None, scale=0.5, gray=False, margin=40.0, min_cos=0.12, gamma=1.0):
    fr = FR(); ny, nx = shape
    cams = cams or sorted(fr.cams)
    out = {}
    for n in cams:
        img = fr.image(n, scale)
        if gray: img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        uv, z = fr.project(n, P); uv = uv * scale
        w, inside = view_w(fr, n, P, np.asarray(normal, float), uv, z, img.shape, margin=margin)
        col = remap(img, uv, (ny, nx)).astype(np.float32)
        out[n] = (col, w.reshape(ny, nx).astype(np.float32))
    return out

def focus_image(views, power=2.0):
    ny, nx = next(iter(views.values()))[1].shape
    acc = 0; tot = np.zeros((ny, nx), np.float64)
    for n, (col, w) in views.items():
        wp = (w.astype(np.float64)) ** power
        acc = acc + (col.astype(np.float64) * (wp[..., None] if col.ndim == 3 else wp)); tot += wp
    return (acc / np.maximum(tot, 1e-12)[..., None] if np.ndim(acc) == 3 else acc / np.maximum(tot, 1e-12)), tot

def consistency(views, roi=None, wmin_rel=0.15):
    """costo = deviazione media tra le viste (dopo aver tolto media e normalizzato) sulla regione; piu' basso = piano giusto."""
    ny, nx = next(iter(views.values()))[1].shape
    if roi is None: roi = np.ones((ny, nx), bool)
    sel = []
    wmax = max(v[1].max() for v in views.values()) + 1e-12
    for n, (col, w) in views.items():
        m = roi & (w > wmin_rel * wmax * 0.2)
        if m.sum() < 0.5 * roi.sum(): continue
        g = col if col.ndim == 2 else col.mean(axis=2)
        g = cv2.GaussianBlur(g, (0, 0), 1.2)
        gm = g[roi]; mu = gm.mean(); sd = gm.std() + 1e-3
        sel.append((g - mu) / sd)
    if len(sel) < 3: return None, len(sel)
    S = np.stack(sel)
    return float(S[:, roi].std(axis=0).mean()), len(sel)

def sweep(axis, vals, a_rng, b_rng, normal, ppm=250, roi_rect=None, scale=0.5, cams=None):
    res = []
    for v in vals:
        P, shape, ia, ib = grid_points(axis, v, a_rng, b_rng, ppm)
        views = sample_views(P, normal, shape, cams, scale, gray=True)
        roi = None
        c, k = consistency(views, roi)
        res.append((v, c, k))
    return res

def tenengrad(img):
    gx = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3)
    return float((gx * gx + gy * gy).mean())

def sharp_sweep(axis, vals, a_rng, b_rng, normal, ppm=300, scale=0.5, cams=None, power=1.0, direction='both'):
    out = []
    for v in vals:
        P, shape, ia, ib = grid_points(axis, v, a_rng, b_rng, ppm)
        views = sample_views(P, normal, shape, cams, scale, gray=True)
        img, tot = focus_image(views, power=power)
        out.append((v, tenengrad(img.astype(np.float32)), int(sum((w > 0.02 * max(1e-9, max(x[1].max() for x in views.values()))).mean() > 0.5 for _, w in views.values()))))
    return out
