"""Texture della finestra dalla foto vera (non registrata) e non piu' dal solo riquadro del telaio: il quadrilatero esterno dell'oro (segmentato per colore, come in measure_gold.py) si raddrizza sul rettangolo VERO
(0,904 x 1,54 m: l'utente dice che la finestra e' alta 154 cm e sta a 95 cm da terra) con l'omografia dei quattro angoli: le proporzioni e la larghezza dei bordi d'oro sono quelle della foto.
I vetri della foto sono scuri e pieni di riflessi della stanza: si sostituiscono con quelli puliti della vecchia texture (frame_clean.png: vista fuori, riflessi coperti), rimappati con l'omografia fra le due coppie di vetri.
Uso: python3 win_prep2.py FOTO.jpg x0 y0 x1 y1 [OUT_DIR]   (ritaglio in pixel attorno alla finestra)  ->  OUT_DIR/frame_full.png (700 px/m)"""
import sys, os, cv2, numpy as np
W_M, H_M, PPM = 0.904, 1.54, 700
def gold_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    g = ((H >= 8) & (H <= 34) & (S >= 45) & (V >= 55)).astype(np.uint8) * 255
    return cv2.morphologyEx(g, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
def outer_quad(img):
    g = gold_mask(img); n, lab, st, _ = cv2.connectedComponentsWithStats(g, connectivity=8)
    m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8) * 255
    c = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea); hull = cv2.convexHull(c); peri = cv2.arcLength(hull, True)
    for eps in np.linspace(0.01, 0.08, 15):
        a = cv2.approxPolyDP(hull, eps * peri, True)
        if len(a) == 4: break
    q = a[:, 0, :].astype(np.float32); s = q.sum(1); d = q[:, 0] - q[:, 1]
    return np.array([q[np.argmin(s)], q[np.argmax(d)], q[np.argmax(s)], q[np.argmin(d)]], np.float32)       # TL, TR, BR, BL
def panes(rect, margin):
    """i due vetri: componenti grandi non-oro dentro il rettangolo (esclusi `margin` px di bordo); ritorna i quadrilateri (TL,TR,BR,BL) da sinistra a destra"""
    ng = (gold_mask(rect) == 0).astype(np.uint8) * 255; ng[:margin] = 0; ng[-margin:] = 0; ng[:, :margin] = 0; ng[:, -margin:] = 0
    ng = cv2.morphologyEx(ng, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(ng, connectivity=8); idx = sorted(range(1, n), key=lambda i: -st[i, cv2.CC_STAT_AREA])[:2]
    out = []
    for i in sorted(idx, key=lambda i: st[i, cv2.CC_STAT_LEFT]):
        m = (lab == i).astype(np.uint8) * 255; c = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea)
        r = cv2.minAreaRect(c); b = cv2.boxPoints(r).astype(np.float32); s = b.sum(1); d = b[:, 0] - b[:, 1]
        out.append((np.array([b[np.argmin(s)], b[np.argmax(d)], b[np.argmax(s)], b[np.argmin(d)]], np.float32), m))
    return out
if __name__ == '__main__':
    photo = cv2.imread(sys.argv[1]); x0, y0, x1, y1 = map(int, sys.argv[2:6]); out = sys.argv[6] if len(sys.argv) > 6 else '.'
    img = photo[y0:y1, x0:x1]; q = outer_quad(img); w, h = int(round(W_M * PPM)), int(round(H_M * PPM))
    M = cv2.getPerspectiveTransform(q, np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)); R = cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_CUBIC)
    R = cv2.resize(R[3:-3, 3:-3], (w, h), interpolation=cv2.INTER_CUBIC)      # via i 3 px esterni (sfumatura oro/muro)
    old = cv2.imread(os.path.join(os.environ.get('WIN_ASSETS', '/tmp/claude-0/s/st3/assets/win'), 'frame_clean.png'))
    pr, pt = panes(R, int(0.06 * w)), panes(old, int(0.02 * old.shape[1]))
    print('vetri nella foto raddrizzata:', len(pr), 'nella vecchia texture:', len(pt))
    res = R.copy()
    for (qr, mr), (qt, mt) in zip(pr, pt):
        Hm = cv2.getPerspectiveTransform(qt, qr); warped = cv2.warpPerspective(old, Hm, (w, h), flags=cv2.INTER_CUBIC)
        mk = cv2.erode(mr, np.ones((5, 5), np.uint8)).astype(np.float32) / 255; mk = cv2.GaussianBlur(mk, (0, 0), 2.0)[..., None]
        res = (res.astype(np.float32) * (1 - mk) + warped.astype(np.float32) * mk).clip(0, 255).astype(np.uint8)
    os.makedirs(out, exist_ok=True); cv2.imwrite(os.path.join(out, 'frame_full_raw.png'), R); cv2.imwrite(os.path.join(out, 'frame_full.png'), res); print('salvato', res.shape)
