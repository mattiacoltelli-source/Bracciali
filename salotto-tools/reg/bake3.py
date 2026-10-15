import sys, json, time
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from frame import make_frame
from bake2 import WALLS, wall_def, remap

class Occ:
    """Occlusori: scatole (con margine) e maschere nello spazio immagine dai punti dello SfM (ben supportati) che stanno dentro
    la stanza, lontani dai piani e non vicini alle pareti in alto (decorazioni a muro)."""
    def __init__(self, fr, boxes=None, margin=0.06, dmin=0.12, rad_m=0.09, scale=0.5, min_track=3, max_err=1.5, deco_depth=0.26, deco_y=1.0, min_support=2):
        self.fr = fr; self.scale = scale; self.rad_m = rad_m; self.min_support = min_support
        self.boxes = [(np.array(b['min']) - margin, np.array(b['max']) + margin) for b in (boxes or [])]
        pts = [p for p in fr.r.points3D.values() if p.track.length() >= min_track and p.error <= max_err]
        P = np.array([p.xyz for p in pts])
        Pr = fr.sfm_to_room(P)
        L, W, H = fr.L, fr.W, fr.H
        inside = (Pr[:, 0] > 0.02) & (Pr[:, 0] < L - 0.02) & (Pr[:, 2] > 0.02) & (Pr[:, 2] < W - 0.02) & (Pr[:, 1] > 0.03) & (Pr[:, 1] < H - 0.03)
        dwall = np.minimum.reduce([Pr[:, 0], L - Pr[:, 0], Pr[:, 2], W - Pr[:, 2]])
        d = np.minimum(dwall, np.minimum(Pr[:, 1], H - Pr[:, 1]))
        deco = (dwall < deco_depth) & (Pr[:, 1] > deco_y)
        self.pts = Pr[inside & (d > dmin) & ~deco]
        self.masks = {}; self.disks = {}
        print('punti occlusori:', len(self.pts), 'su', len(P), flush=True)
    def disk(self, r):
        if r not in self.disks:
            yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
            self.disks[r] = (xx * xx + yy * yy <= r * r).astype(np.int16)
        return self.disks[r]
    def mask(self, n, shape):
        key = (n, shape)
        if key in self.masks: return self.masks[key]
        fr = self.fr; h, w = shape
        uv, z = fr.project(n, self.pts); uv = uv * self.scale
        dist = np.linalg.norm(self.pts - fr.cams[n]['C'], axis=1)
        acc = np.zeros((h, w), np.int16)
        f = fr.f * self.scale
        for (u, v), dd, zz in zip(uv, dist, z):
            if zz <= 0.1 or not (-60 < u < w + 60 and -60 < v < h + 60): continue
            r = int(max(3, min(100, f * self.rad_m / max(dd, 0.3))))
            dk = self.disk(r); u0, v0 = int(u) - r, int(v) - r
            x0, y0, x1, y1 = max(u0, 0), max(v0, 0), min(u0 + 2 * r + 1, w), min(v0 + 2 * r + 1, h)
            if x1 <= x0 or y1 <= y0: continue
            acc[y0:y1, x0:x1] += dk[y0 - v0:y1 - v0, x0 - u0:x1 - u0]
        m = ((acc >= self.min_support) * 255).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        self.masks[key] = m
        return m
    def box_hit(self, C, P):
        hit = np.zeros(len(P), bool)
        d = P - C
        with np.errstate(divide='ignore', invalid='ignore'):
            for lo, hi in self.boxes:
                t1 = (lo - C) / d; t2 = (hi - C) / d
                tmin = np.minimum(t1, t2).max(axis=1); tmax = np.maximum(t1, t2).min(axis=1)
                tmin = np.nan_to_num(tmin, nan=-1); tmax = np.nan_to_num(tmax, nan=-1)
                hit |= (tmax >= np.maximum(tmin, 0.0)) & (tmin < 0.985)
        return hit

def view_w(fr, n, P, normal, uv, z, img_shape, margin=60.0):
    C = fr.cams[n]['C']
    v = C - P
    d = np.linalg.norm(v, axis=1)
    cosv = np.abs(v @ normal) / np.maximum(d, 1e-6)
    h, w = img_shape[:2]
    inside = (z > 0.1) & (uv[:, 0] >= 0) & (uv[:, 0] < w - 1) & (uv[:, 1] >= 0) & (uv[:, 1] < h - 1)
    edge = np.minimum.reduce([uv[:, 0], w - 1 - uv[:, 0], uv[:, 1], h - 1 - uv[:, 1]])
    fall = np.clip(edge / margin, 0, 1); fall = fall * fall * (3 - 2 * fall)
    facing = np.clip((cosv - 0.12) / 0.45, 0, 1)
    side = ((v @ normal) > 0.05)
    return inside * side * fall * facing * (cosv ** 1.5) / np.maximum(d, 0.4), inside

def bake(fr, P, normal, shape, cams, occ=None, scale=0.5, power=3.0, smooth=0, tag='', gain=True, verbose=True):
    ny, nx = shape
    layers = {}
    for n in cams:
        img = fr.image(n, scale)
        uv, z = fr.project(n, P); uv = uv * scale
        w, inside = view_w(fr, n, P, normal, uv, z, img.shape)
        if occ is not None:
            m = occ.mask(n, img.shape[:2])
            mm = cv2.remap(m, uv[:, 0].astype(np.float32).reshape(ny, nx), uv[:, 1].astype(np.float32).reshape(ny, nx), cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            w = w * (mm.ravel() == 0)
            if occ.boxes: w = w * (~occ.box_hit(fr.cams[n]['C'], P))
        col = remap(img, uv, (ny, nx)).astype(np.float32)
        wm = w.reshape(ny, nx).astype(np.float32)
        if smooth > 0: wm = cv2.GaussianBlur(wm, (0, 0), smooth)
        layers[n] = (col, wm)
        if verbose: print(tag, n, 'cop', round(float((wm > 0).mean()), 3), flush=True)
    # compensazione dell'esposizione: guadagno per camera e per canale (minimi quadrati sui rapporti delle sovrapposizioni)
    gains = {n: np.ones(3) for n in cams}
    if gain:
        idx = {n: i for i, n in enumerate(cams)}
        rows, rhs, wts = [], [], []
        for a in range(len(cams)):
            for b in range(a + 1, len(cams)):
                ca, wa = layers[cams[a]]; cb, wb = layers[cams[b]]
                m = (wa > 0.02 * wa.max() + 1e-9) & (wb > 0.02 * wb.max() + 1e-9)
                if m.sum() < 400: continue
                ra = np.log(np.maximum(np.median(ca[m], axis=0), 1.0)); rb = np.log(np.maximum(np.median(cb[m], axis=0), 1.0))
                rows.append((a, b)); rhs.append(rb - ra); wts.append(np.sqrt(m.sum()))
        if rows:
            n_c = len(cams); A = np.zeros((len(rows) + 1, n_c)); y = np.zeros((len(rows) + 1, 3))
            for k, ((a, b), r_, w_) in enumerate(zip(rows, rhs, wts)):
                A[k, a] = -w_; A[k, b] = w_; y[k] = r_ * w_      # g_b - g_a = log(Ib/Ia)? vogliamo gain tali che I*g uguali: g_a*Ia = g_b*Ib -> g_a - g_b = log(Ib/Ia)
            # risolvo per log-gain g: g_a - g_b = rhs -> riscrivo
            A = np.zeros((len(rows) + 1, n_c))
            for k, ((a, b), w_) in enumerate(zip(rows, wts)): A[k, a] = w_; A[k, b] = -w_
            A[-1, :] = 0.05                                   # vincolo debole: media dei log-gain ~ 0
            y[-1] = 0
            for k, (r_, w_) in enumerate(zip(rhs, wts)): y[k] = r_ * w_
            sol = np.linalg.lstsq(A, y, rcond=None)[0]
            for n in cams: gains[n] = np.exp(sol[idx[n]])
            if verbose: print(tag, 'guadagni:', {n: np.round(g, 3).tolist() for n, g in gains.items()}, flush=True)
    acc = np.zeros((ny, nx, 3), np.float64); tot = np.zeros((ny, nx), np.float64)
    for n in cams:
        col, wm = layers[n]
        wp = wm.astype(np.float64) ** power
        acc += (col * gains[n][None, None, :]) * wp[..., None]; tot += wp
    out = acc / np.maximum(tot, 1e-20)[..., None]
    return np.clip(out, 0, 255).astype(np.uint8), tot > 1e-9 * max(1.0, tot.max()) * 1e-6, layers
