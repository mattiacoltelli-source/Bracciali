"""Texture di una superficie parametrica a partire da foto registrate: per ogni punto della superficie si guarda in quali foto e' visibile (normale verso la camera),
si campiona il colore proiettando il punto con la posa della foto (sul fotogramma senza distorsione) e si mescolano le foto con peso = coseno dell'angolo di vista.
Le pose sono nel sistema stanza (poses_room.json: matrice V stanza -> camera OpenCV, f, cx, cy, k)."""
import os, json
import numpy as np, cv2

POSES = os.environ.get('POSES_ROOM', '/tmp/claude-0/s/shelf/poses_room.json')
FOTO = os.environ.get('FOTO_DIR', '')
CACHE = os.environ.get('UND_CACHE', '/tmp/claude-0/s/st3/und_cache')

class Cam:
    def __init__(s, pid, photo_dir=None):
        d = json.load(open(POSES))[pid]; s.pid = pid
        s.V = np.array(d['V']).reshape(4, 4); s.f, s.cx, s.cy, s.k = d['f'], d['cx'], d['cy'], d['k']; s.W, s.H = d['W'], d['H']
        s.C = -np.linalg.solve(s.V[:3, :3], s.V[:3, 3])         # centro della camera nel sistema stanza (V non e' ortonormale: la trasformazione SfM->stanza ha una piccola anisotropia)
        s._img = None; s.photo_dir = photo_dir or FOTO
    @property
    def img(s):
        if s._img is None:
            p = f'{CACHE}/{s.pid}.png'
            if os.path.exists(p): s._img = cv2.imread(p)
            else:
                im = cv2.imread(f'{s.photo_dir}/{s.pid}-image.jpg'); K = np.array([[s.f, 0, s.cx], [0, s.f, s.cy], [0, 0, 1.0]])
                s._img = cv2.undistort(im, K, np.array([s.k, 0, 0, 0], float), None, K); os.makedirs(CACHE, exist_ok=True); cv2.imwrite(p, s._img)
        return s._img
    def project(s, P):
        P = np.asarray(P, float); X = P @ s.V[:3, :3].T + s.V[:3, 3]
        z = X[..., 2]; zz = np.where(z > 1e-6, z, 1e-6)
        return s.f * X[..., 0] / zz + s.cx, s.f * X[..., 1] / zz + s.cy, z
    def sample(s, u, v):
        im = s.img; H, W = im.shape[:2]
        uu = np.clip(u, 0, W - 1.001).astype(np.float32); vv = np.clip(v, 0, H - 1.001).astype(np.float32)
        return cv2.remap(im, uu, vv, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)

def bake(P, N, cams, valid=None, power=3.0, min_cos=0.12, kill_highlights=True, blur_src=0.0):
    """P, N: (h, w, 3) punti e normali (verso l'esterno) della superficie; cams: lista di Cam; valid: dict pid -> f(u, v, P) -> bool (occlusioni note).
    Ritorna (rgb float32 BGR, peso totale): le zone senza foto hanno peso 0."""
    h, w = P.shape[:2]; acc = np.zeros((h, w, 3), np.float32); wt = np.zeros((h, w), np.float32)
    for cam in cams:
        u, v, z = cam.project(P)
        view = cam.C[None, None, :] - P; ln = np.linalg.norm(view, axis=-1); view = view / np.maximum(ln[..., None], 1e-9)
        cosa = np.sum(N * view, axis=-1)
        W_ = np.clip((cosa - min_cos) / (1 - min_cos), 0, 1) ** power * (z > 0)
        inside = (u > 2) & (u < cam.W - 3) & (v > 2) & (v < cam.H - 3); W_ = W_ * inside
        if valid and cam.pid in valid: W_ = W_ * valid[cam.pid](u, v, P)
        col = cam.sample(u, v)
        if kill_highlights:      # riflessi puntiformi (bianchi, poco saturi): in questa foto non contano
            hsv = cv2.cvtColor(np.clip(col, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
            hl = (hsv[..., 2] > 238) & (hsv[..., 1] < 40); hl = cv2.dilate(hl.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            W_ = W_ * np.where(hl, 0.02, 1.0)
        acc += col * W_[..., None]; wt += W_
    out = acc / np.maximum(wt[..., None], 1e-6)
    return out, wt

def fill_holes(img, wt, thr=0.02):
    """riempie le zone senza foto con una diffusione liscia (push-pull) dei colori vicini"""
    m = (wt > thr).astype(np.float32)
    if m.mean() < 0.01: return img
    pyr_i = [img * m[..., None]]; pyr_w = [m]
    for _ in range(8):
        pyr_i.append(cv2.pyrDown(pyr_i[-1])); pyr_w.append(cv2.pyrDown(pyr_w[-1]))
    out = pyr_i[-1] / (pyr_w[-1][..., None] + 1e-6)
    for l in range(7, -1, -1):
        up = cv2.pyrUp(out, dstsize=(pyr_i[l].shape[1], pyr_i[l].shape[0]))
        fine = pyr_i[l] / (pyr_w[l][..., None] + 1e-6); a = np.clip(pyr_w[l] * 4.0, 0, 1)[..., None]
        out = fine * a + up * (1 - a)
    a = np.clip(m * 1.0, 0, 1)[..., None]
    return img * a + out * (1 - a)

def raster_rings(cam, ring_fn, ys, nphi=72, offset=(0.0, 0.0), shape=None):
    """silhouette (immagine binaria piena) di un solido di rotazione: unione dei dischi dei suoi anelli proiettati. ring_fn(y) -> (n, 3) punti dell'anello a quota y."""
    H, W = shape if shape else (cam.H, cam.W)
    out = np.zeros((H, W), np.uint8)
    for y in ys:
        P = ring_fn(y); u, v, z = cam.project(P)
        pts = np.stack([u + offset[0], v + offset[1]], -1).astype(np.int32)
        cv2.fillPoly(out, [pts.reshape(-1, 1, 2)], 255)
    return out

def best_shift(pred_full, mask_crop, origin, rng=24, ignore=None):
    """cerca lo spostamento (du, dv) in pixel che massimizza l'IoU fra la silhouette prevista (immagine intera) e la maschera (ritaglio con origine `origin`)"""
    x0, y0 = origin; h, w = mask_crop.shape
    best = (-1, 0, 0); mk = (mask_crop > 127)
    ig = None if ignore is None else ignore
    for dv in range(-rng, rng + 1, 2):
        for du in range(-rng, rng + 1, 2):
            sub = pred_full[max(0, y0 - dv):y0 - dv + h, max(0, x0 - du):x0 - du + w] if False else None
    # versione rapida: sposta la maschera invece della previsione
    M = np.float32([[1, 0, 0], [0, 1, 0]])
    pred = (pred_full[y0:y0 + h, x0:x0 + w] > 127)
    for dv in range(-rng, rng + 1, 2):
        for du in range(-rng, rng + 1, 2):
            M[0, 2] = du; M[1, 2] = dv
            m2 = cv2.warpAffine(mk.astype(np.uint8), M, (w, h), flags=cv2.INTER_NEAREST) > 0
            a = pred & m2; b = pred | m2
            if ig is not None: a = a & ~ig; b = b & ~ig
            iou = a.sum() / max(1, b.sum())
            if iou > best[0]: best = (iou, du, dv)
    return best
