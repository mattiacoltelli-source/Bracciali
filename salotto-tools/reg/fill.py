"""Riempimento di buchi nelle texture: quilting (patch dal contorno) per superfici con grana, diffusione per superfici lisce."""
import numpy as np, cv2

def diffuse_fill(img, valid, down=4, feather=4):
    """Riempie con una versione sfocata del contorno (adatto a pareti lisce): inpaint a bassa risoluzione, poi composizione sfumata."""
    if valid.all(): return img
    h, w = valid.shape
    sm = cv2.resize(img, (w // down, h // down), interpolation=cv2.INTER_AREA)
    vm = cv2.resize(valid.astype(np.uint8), (w // down, h // down), interpolation=cv2.INTER_NEAREST)
    hole = ((1 - vm) * 255).astype(np.uint8)
    hole = cv2.dilate(hole, np.ones((3, 3), np.uint8))
    filled = cv2.inpaint(sm, hole, 5, cv2.INPAINT_TELEA)
    filled = cv2.GaussianBlur(filled, (0, 0), 2.0)
    up = cv2.resize(filled, (w, h), interpolation=cv2.INTER_CUBIC)
    a = valid.astype(np.float32)
    if feather: a = cv2.GaussianBlur(cv2.erode(valid.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (0, 0), feather)
    a = np.where(valid, np.maximum(a, 0.0), 0.0)[..., None]
    a = np.clip(a * 1.0, 0, 1)
    return (img.astype(np.float32) * a + up.astype(np.float32) * (1 - a)).clip(0, 255).astype(np.uint8)

def quilt_fill(img, valid, patch=48, overlap=14, seed=1, ncand=700, topk=6, ring=260, verbose=False):
    """Riempie i buchi con patch prese dalle zone vicine (image quilting semplificato, fusione a rampa)."""
    rng = np.random.default_rng(seed)
    H, W = valid.shape
    out = img.astype(np.float32).copy()
    known = valid.copy()
    hole = ~valid
    if not hole.any(): return img
    # candidati: posizioni (y,x) la cui patch e' interamente valida
    integ = cv2.integral(valid.astype(np.uint8))
    def full(y, x): return integ[y + patch, x + patch] - integ[y, x + patch] - integ[y + patch, x] + integ[y, x] == patch * patch
    ys, xs = np.nonzero(hole)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    step = patch - overlap
    # bordo della finestra di lavoro: allarga di mezzo patch
    ys_ = list(range(max(0, y0 - overlap), min(H - patch, y1) + 1, step)) or [max(0, min(y0, H - patch))]
    xs_ = list(range(max(0, x0 - overlap), min(W - patch, x1) + 1, step)) or [max(0, min(x0, W - patch))]
    if ys_[-1] + patch < y1: ys_.append(min(H - patch, y1 - patch))
    if xs_[-1] + patch < x1: xs_.append(min(W - patch, x1 - patch))
    # candidati vicini al buco
    near = cv2.dilate(hole.astype(np.uint8), np.ones((2 * ring + 1, 2 * ring + 1), np.uint8)).astype(bool) & valid
    cy, cx = np.nonzero(near[:H - patch, :W - patch])
    cand = [(y, x) for y, x in zip(cy[::7], cx[::7]) if full(y, x)]
    cand = np.array(cand)
    if len(cand) < 50: return diffuse_fill(img, valid)
    for y in ys_:
        for x in xs_:
            kwin = known[y:y + patch, x:x + patch]
            if kwin.all(): continue
            hwin = ~kwin
            tgt = out[y:y + patch, x:x + patch]
            sel = cand[rng.choice(len(cand), size=min(ncand, len(cand)), replace=False)]
            if kwin.any():
                kk = kwin.astype(np.float32)[..., None]
                best = []
                for (cy_, cx_) in sel:
                    src = out[cy_:cy_ + patch, cx_:cx_ + patch]
                    best.append((((src - tgt) ** 2) * kk).sum())
                order = np.argsort(best)[:topk]
                pick = sel[order[rng.integers(0, len(order))]]
            else:
                pick = sel[rng.integers(0, len(sel))]
            src = out[pick[0]:pick[0] + patch, pick[1]:pick[1] + patch]
            unk = (~kwin).astype(np.float32)
            al = cv2.GaussianBlur(unk, (0, 0), overlap / 3.0)
            al = np.where(kwin, np.minimum(al, 0.5), 1.0).astype(np.float32)[..., None]
            tgt[:] = tgt * (1 - al) + src * al
            known[y:y + patch, x:x + patch] = True
    return out.clip(0, 255).astype(np.uint8)

def scene_complete(img, valid, hole, pad=36, stride=1, verbose=True):
    """Riempie `hole` copiando da un'altra zona del pavimento il blocco il cui contorno somiglia di piu' (poi fusione di Poisson)."""
    H, W = valid.shape
    ys, xs = np.nonzero(hole)
    y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + 1 + pad)
    x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + 1 + pad)
    h, w = y1 - y0, x1 - x0
    T = img[y0:y1, x0:x1].astype(np.float32)
    ring = (valid[y0:y1, x0:x1] & ~hole[y0:y1, x0:x1]).astype(np.uint8)
    # finestre interamente valide
    integ = cv2.integral(valid.astype(np.uint8))
    ok = np.zeros((H - h + 1, W - w + 1), bool)
    for yy in range(0, H - h + 1):
        row = integ[yy + h, w:] - integ[yy, w:] - integ[yy + h, :W - w + 1] + integ[yy, :W - w + 1]
        ok[yy] = row == h * w
    if not ok.any(): return None
    M = np.dstack([ring] * 3).astype(np.float32)
    res = cv2.matchTemplate(img.astype(np.float32), T, cv2.TM_SQDIFF, mask=M)
    res = res / max(1.0, M.sum())
    res[~ok] = np.inf
    # non copiare da posti troppo vicini al buco stesso
    iy, ix = np.unravel_index(np.argmin(res), res.shape)
    if verbose: print('miglior sorgente a', (ix, iy), 'costo', float(res[iy, ix]))
    src = img[iy:iy + h, ix:ix + w]
    dst = img.copy()
    m = (cv2.dilate(hole[y0:y1, x0:x1].astype(np.uint8), np.ones((5, 5), np.uint8)) * 255).astype(np.uint8)
    m[:2] = 0; m[-2:] = 0; m[:, :2] = 0; m[:, -2:] = 0
    center = (x0 + w // 2, y0 + h // 2)
    try:
        out = cv2.seamlessClone(src, dst, m, center, cv2.NORMAL_CLONE)
    except Exception as e:
        print('seamlessClone fallito', e); a = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 5)[..., None]
        out = dst.copy(); out[y0:y1, x0:x1] = (dst[y0:y1, x0:x1] * (1 - a) + src * a).astype(np.uint8)
    return out

def push_pull(img, w, levels=8):
    """Interpolazione liscia a piramide (push-pull): i pixel con peso w valgono come dati, il resto si ricava dai livelli piu' grossolani."""
    h, wd = w.shape
    I = [img.astype(np.float32) * w[..., None]]; Wt = [w.astype(np.float32)]
    for _ in range(levels):
        I.append(cv2.pyrDown(I[-1])); Wt.append(cv2.pyrDown(Wt[-1]))
    out = I[-1] / (Wt[-1][..., None] + 1e-6)
    if Wt[-1].max() < 1e-6: return img
    for l in range(levels - 1, -1, -1):
        up = cv2.pyrUp(out, dstsize=(I[l].shape[1], I[l].shape[0]))
        fine = I[l] / (Wt[l][..., None] + 1e-6)
        a = np.clip(Wt[l] * 4.0, 0, 1)[..., None]
        out = fine * a + up * (1 - a)
    return out

def wall_fill(img, valid, ppm=300, floor_cut=0.14, top=3.0, soft=False):
    """Riempie i buchi di una parete usando solo pixel di intonaco chiaro e poco saturo (niente ombre, oggetti, battiscopa)."""
    H, W = valid.shape
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    ref = float(np.median(lum[valid & (lum > 140)]))
    wl = np.clip((lum - 0.80 * ref) / (0.10 * ref), 0, 1) * np.clip((55.0 - hsv[..., 1]) / 25.0, 0, 1)
    if soft:      # tiene anche le zone di intonaco piu' scure (gradiente della luce): serve a ricostruire fasce vicine ai mobili senza schiarirle
        wl = np.clip((lum - 0.45 * ref) / (0.08 * ref), 0, 1) * np.clip((60.0 - hsv[..., 1]) / 25.0, 0, 1)
    rows = (top - (np.arange(H) + 0.5) / ppm)[:, None]           # quota y di ogni riga
    wl = wl * (rows > floor_cut)
    # solo pixel "interni" (lontani dai bordi dei buchi: li' c'e' contaminazione)
    inner = cv2.erode(valid.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
    wl = (wl * inner).astype(np.float32)
    # pre-sfocatura leggera dei pesi: i pixel isolati contano poco
    wl = cv2.GaussianBlur(wl, (0, 0), 1.0) * (wl > 0)
    fill = push_pull(img, wl, levels=9).clip(0, 255)
    a = cv2.GaussianBlur(valid.astype(np.float32), (0, 0), 2.0)
    a = np.where(valid, np.clip(a * 1.5, 0, 1), 0.0)[..., None]
    out = img.astype(np.float32) * a + fill * (1 - a)
    return out.clip(0, 255).astype(np.uint8)
