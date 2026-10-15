"""Misura i 5 quadri sulle pareti: bake ad alta risoluzione sul piano della tela, ricerca della posizione del rettangolo (misura nota)
col massimo di bordo lungo il contorno, estrazione della foto del quadro. Uso: python3 paintings.py"""
import sys, json, time
sys.path.insert(0, '/tmp/claude-0/s/reg')
from bake4 import *
from bake2 import wall_def

PAINT = {  # misure del catalogo; u,y = stima di partenza dai muri a 300 ppm
    'taj': dict(wall='T', u=2.87, y=1.835, w=0.50, h=0.75),
    'petra': dict(wall='W', u=3.02, y=1.787, w=0.50, h=0.75),
    'barca': dict(wall='W', u=3.80, y=1.655, w=0.75, h=0.50),
    'islanda': dict(wall='F', u=4.015, y=1.885, w=0.75, h=0.50),
    'sneaker': dict(wall='A', u=3.34, y=1.03, w=0.75, h=0.50),
}
PPM = 800
ONLY = {'sneaker': ['6d89137e']}   # il quadro e' appoggiato inclinato: con una sola camera frontale niente doppie immagini
OFF = {'sneaker': 0.03}
DEPTH = 0.03    # la tela sporge di 3 cm: la facciata sta a 3 cm dalla parete

def region(fr, wid, uc, yc, hw, hh, ppm, off):
    O, U, N, length = wall_def(fr, wid)
    nx, ny = int(round(2 * hw * ppm)), int(round(2 * hh * ppm))
    us = uc - hw + (np.arange(nx) + 0.5) / ppm; ys = yc + hh - (np.arange(ny) + 0.5) / ppm
    UU, YY = np.meshgrid(us, ys)
    P = O[None, :] + UU.reshape(-1, 1) * U[None, :] + np.stack([np.zeros(UU.size), YY.ravel(), np.zeros(UU.size)], 1) + N[None, :] * off
    return P, N, (ny, nx)

def locate(img, w, h, ppm, search=0.07):
    """Posizione (dx, dy in metri rispetto al centro della regione) del rettangolo w x h col massimo di bordo sul contorno."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 1.6)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    G = np.abs(gx) + np.abs(gy)
    ny, nx = g.shape
    pw, ph = int(round(w * ppm)), int(round(h * ppm))
    cx, cy = nx // 2, ny // 2
    r = int(search * ppm)
    t = 3
    # somme cumulate per righe/colonne per valutare in fretta i quattro lati
    Ir = np.cumsum(G, axis=1); Ic = np.cumsum(G, axis=0)
    def row_sum(y, x0, x1): return Ir[y, x1] - Ir[y, x0 - 1]
    def col_sum(x, y0, y1): return Ic[y1, x] - Ic[y0 - 1, x]
    best = (-1, 0, 0)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            x0 = cx - pw // 2 + dx; y0 = cy - ph // 2 + dy; x1 = x0 + pw; y1 = y0 + ph
            if x0 - t < 1 or y0 - t < 1 or x1 + t >= nx or y1 + t >= ny: continue
            s = 0.0
            for k in range(-t, t + 1):
                s += row_sum(y0 + k, x0, x1) + row_sum(y1 + k, x0, x1) + col_sum(x0 + k, y0, y1) + col_sum(x1 + k, y0, y1)
            if s > best[0]: best = (s, dx, dy)
    return best[1] / ppm, -best[2] / ppm, best[0] / (2 * (pw + ph) * (2 * t + 1))

if __name__ == '__main__':
    fr = FR(); names = sorted(fr.cams)
    out = {}
    for pid, p in PAINT.items():
        t0 = time.time()
        hw, hh = p['w'] / 2 + 0.10, p['h'] / 2 + 0.10
        P, N, shape = region(fr, p['wall'], p['u'], p['y'], hw, hh, PPM, OFF.get(pid, DEPTH))
        img, valid, tot = bake(fr, P, N, shape, ONLY.get(pid, names), None, scale=1.0, power=4.0, smooth=0, gain=False, tag=pid, verbose=False, cos_pow=2.0, min_cos=0.2)
        cv2.imwrite(f'/tmp/claude-0/s/reg/out/pt_{pid}_raw.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        dx, dy, sc = locate(img, p['w'], p['h'], PPM)
        uc, yc = p['u'] + dx, p['y'] + dy
        # estrazione: stessa regione ricentrata sul rettangolo, bordo interno di 1 mm per non prendere il filo della tela
        pw, ph = int(round(p['w'] * PPM)), int(round(p['h'] * PPM))
        cx, cy = img.shape[1] // 2 + int(round(dx * PPM)), img.shape[0] // 2 - int(round(dy * PPM))
        x0, y0 = cx - pw // 2, cy - ph // 2
        art = img[y0 + 2:y0 + ph - 2, x0 + 2:x0 + pw - 2].copy()
        if pid == 'sneaker':   # la ciotola davanti al bordo basso: si cancella
            ah, aw = art.shape[:2]
            m = np.zeros((ah, aw), np.uint8); m[int(ah * 0.885):, int(aw * 0.17):int(aw * 0.45)] = 255
            art = cv2.inpaint(art, m, 7, cv2.INPAINT_TELEA)
        cv2.imwrite(f'/tmp/claude-0/s/reg/out/art_{pid}.png', art)
        out[pid] = dict(wall=p['wall'], u=round(uc, 4), y=round(yc, 4), w=p['w'], h=p['h'], score=round(float(sc), 2))
        print(pid, out[pid], 'da', (p['u'], p['y']), round(time.time() - t0), 's', flush=True)
    json.dump(out, open('/tmp/claude-0/s/reg/out/paintings.json', 'w'), indent=1)
