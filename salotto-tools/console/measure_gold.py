"""Misura la larghezza dei contorni d'oro di una finestra in una foto o in un render: segmenta il bronzo, prende il quadrilatero esterno, lo raddrizza e misura lo spessore su ogni lato in percentuale della larghezza."""
import sys, cv2, numpy as np
def measure(img, name, dbg=None):
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    gold = ((H >= 8) & (H <= 34) & (S >= 45) & (V >= 55)).astype(np.uint8) * 255
    gold = cv2.morphologyEx(gold, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(gold, connectivity=8)
    k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = (lab == k).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cnts, key=cv2.contourArea)
    hull = cv2.convexHull(c); peri = cv2.arcLength(hull, True)
    quad = None
    for eps in np.linspace(0.01, 0.08, 15):
        a = cv2.approxPolyDP(hull, eps * peri, True)
        if len(a) == 4: quad = a[:, 0, :].astype(np.float32); break
    if quad is None: print(name, 'quadrilatero non trovato'); return None
    # ordina: TL, TR, BR, BL
    s = quad.sum(1); d = (quad[:, 0] - quad[:, 1]); tl = quad[np.argmin(s)]; br = quad[np.argmax(s)]; tr = quad[np.argmax(d)]; bl = quad[np.argmin(d)]
    q = np.array([tl, tr, br, bl], np.float32)
    Wq = int(round((np.linalg.norm(tr - tl) + np.linalg.norm(br - bl)) / 2)); Hq = int(round((np.linalg.norm(bl - tl) + np.linalg.norm(br - tr)) / 2))
    M = cv2.getPerspectiveTransform(q, np.array([[0, 0], [Wq, 0], [Wq, Hq], [0, Hq]], np.float32))
    rect = cv2.warpPerspective(img, M, (Wq, Hq)); gm = cv2.warpPerspective(gold, M, (Wq, Hq)) > 0
    # spessore: da ogni bordo verso l'interno, quanti pixel consecutivi (con tolleranza) sono oro, mediando sul 60% centrale del lato
    def thick(line_iter):
        vals = []
        for ln in line_iter:
            n = 0; gaps = 0
            for v in ln:
                if v: n += 1; gaps = 0
                else:
                    gaps += 1
                    if gaps > 3: break
            vals.append(n - 0 if n else 0)
        return float(np.median(vals))
    lo, hi = int(0.2 * Hq), int(0.8 * Hq); lw, hw = int(0.2 * Wq), int(0.8 * Wq)
    bl_ = thick(gm[y, :Wq // 3] for y in range(lo, hi)); br_ = thick(gm[y, ::-1][:Wq // 3] for y in range(lo, hi))
    bt_ = thick(gm[:Hq // 3, x] for x in range(lw, hw)); bb_ = thick(gm[::-1][:Hq // 3, x] for x in range(lw, hw))
    print(f'{name}: riquadro esterno {Wq}x{Hq} (rapporto {Hq / Wq:.3f}); bordo oro / larghezza: sinistro {bl_ / Wq:.3f} destro {br_ / Wq:.3f} alto {bt_ / Wq:.3f} basso {bb_ / Wq:.3f}')
    if dbg: cv2.imwrite(dbg, rect)
    return Wq, Hq, bl_, br_, bt_, bb_
if __name__ == '__main__':
    img = cv2.imread(sys.argv[1]); 
    if len(sys.argv) > 4:
        x0, y0, x1, y1 = map(int, sys.argv[3:7]); img = img[y0:y1, x0:x1]
    measure(img, sys.argv[1].split('/')[-1], sys.argv[2] if len(sys.argv) > 2 else None)
