import sys, json, time
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from frame import make_frame

WALLS = {   # O, U, N come in room.js
    'T': dict(O=(0, 0, 0), U=(1, 0, 0), N=(0, 0, 1)),
    'W': dict(O=('L', 0, 0), U=(0, 0, 1), N=(-1, 0, 0)),
    'F': dict(O=('L', 0, 'W'), U=(-1, 0, 0), N=(0, 0, -1)),
    'A': dict(O=(0, 0, 'W'), U=(0, 0, -1), N=(1, 0, 0)),
}
def wall_def(fr, wid):
    w = WALLS[wid]
    sub = {'L': fr.L, 'W': fr.W}
    O = np.array([sub.get(v, v) for v in w['O']], float)
    return O, np.array(w['U'], float), np.array(w['N'], float), (fr.L if wid in 'TF' else fr.W)

def remap(img, uv, shape):
    ny, nx = shape
    mx = np.nan_to_num(uv[:, 0], nan=-1e4).astype(np.float32).reshape(ny, nx)
    my = np.nan_to_num(uv[:, 1], nan=-1e4).astype(np.float32).reshape(ny, nx)
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))

def view_weights(fr, n, P, normal, uv, z, shape, img_shape, margin=40.0):
    """Peso di ogni punto per la camera n: orientamento, distanza (risoluzione), distanza dal bordo."""
    C = fr.cams[n]['C']
    v = C - P
    d = np.linalg.norm(v, axis=1)
    cosv = np.abs(v @ normal) / np.maximum(d, 1e-6)
    h, w = img_shape[:2]
    inside = (z > 0.1) & (uv[:, 0] >= 0) & (uv[:, 0] < w - 1) & (uv[:, 1] >= 0) & (uv[:, 1] < h - 1)
    edge = np.minimum.reduce([uv[:, 0], w - 1 - uv[:, 0], uv[:, 1], h - 1 - uv[:, 1]])
    fall = np.clip(edge / margin, 0, 1); fall = fall * fall * (3 - 2 * fall)
    facing = np.clip((cosv - 0.15) / 0.5, 0, 1)
    # il lato della parete verso cui guarda la camera: la camera deve stare dal lato della normale
    side = ((v @ normal) > 0.05)
    wgt = inside * side * fall * facing * (cosv ** 2) / np.maximum(d, 0.3)
    return wgt.reshape(shape), d.reshape(shape)

def bake_surface(fr, P, normal, shape, cam_names, power=4.0, save_dir=None, tag='', scale=1.0, exclude=None, verbose=True):
    """P: Nx3 punti 3D dei texel (riga per riga). Ritorna (immagine BGR float, peso totale, mappa delle camere migliori)."""
    ny, nx = shape
    acc = np.zeros((ny, nx, 3), np.float64); tot = np.zeros((ny, nx), np.float64)
    best = np.full((ny, nx), -1, np.int32); bw = np.zeros((ny, nx))
    layers = {}
    for ci, n in enumerate(cam_names):
        img = fr.image(n, scale)
        uv, z = fr.project(n, P)
        uv = uv * scale
        w, d = view_weights(fr, n, P, normal, uv, z, shape, img.shape)
        if exclude and n in exclude: w = w * 0
        col = remap(img, uv, shape).astype(np.float64)
        layers[n] = (col, w)
        wp = w ** power
        acc += col * wp[..., None]; tot += wp
        upd = w > bw
        best[upd] = ci; bw[upd] = w[upd]
        if verbose: print(tag, n, 'copertura', round(float((w > 0).mean()), 3), flush=True)
    out = acc / np.maximum(tot, 1e-12)[..., None]
    return out, tot, best, layers
