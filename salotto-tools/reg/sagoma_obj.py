"""La statua a rilievo da una foto: la figura intera (ritaglio con maschera) diventa una scultura a bassorilievo che si vede da tutti i lati.
La forma viene dalla maschera: lo spessore di ogni punto cresce con la distanza dal bordo (profilo tondeggiante, come le figure Funko di console_obj.py). La mesh segue il contorno della
figura (anelli di punti a distanze crescenti dal bordo + una griglia larga all'interno, triangolati con Delaunay): davanti e dietro si incontrano sul contorno (z = 0), quindi e' un solido chiuso
e non servono maschere alfa. Davanti c'e' la foto; dietro la stessa figura con i colori dei capelli e del vestito (niente volto sul retro); le coordinate texture sono le stesse (il retro
visto da dietro e' specchiato da se'). Coordinate locali dell'oggetto: origine a terra al centro, x a destra, y su, z davanti (+z); altezza di riferimento `height_m`.
Nel pacchetto cifrato le parti sono `asset` (non si disegnano nella stanza): le usa l'oggetto "sagoma" dell'app (objects.js), che si puo' mettere, spostare ed eliminare."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import Delaunay
from meshlib import Mesh
from console_obj import fill_outside, jpg

ASSETS = os.environ.get('SAGOMA_ASSETS', '/tmp/claude-0/s/st3/assets/sagoma')

def ring_points(binary, spacing, smooth=1.6):
    """punti del contorno (uno per anello) ricampionati ogni `spacing` pixel, con il contorno lisciato"""
    cnts, _ = cv2.findContours(binary.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cnts:
        c = c[:, 0, :].astype(float)
        if len(c) < 24: continue
        c = gaussian_filter1d(c, smooth, axis=0, mode='wrap')
        cc = np.vstack([c, c[:1]]); d = np.r_[0, np.cumsum(np.hypot(*np.diff(cc, axis=0).T))]
        n = max(8, int(d[-1] / spacing)); t = np.linspace(0, d[-1], n, endpoint=False)
        out.append(np.stack([np.interp(t, d, cc[:, 0]), np.interp(t, d, cc[:, 1])], 1))
    return np.vstack(out) if out else np.zeros((0, 2))

def triangulate(mask, ppm, R=0.10):
    """punti (u, v) in pixel del ritaglio e triangoli, con la profondita' di ogni punto"""
    m = (mask > 127).astype(np.uint8)
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 5) / ppm
    levels = [(0.0, 3.2), (0.004, 3.8), (0.010, 5.0), (0.020, 7.0), (0.035, 9.0), (0.055, 12.0), (0.080, 15.0)]
    pts = []
    for lv, sp in levels:
        pts.append(ring_points(m if lv == 0 else (dt >= lv), sp))
    H, W = m.shape; gpx = 18.0
    gy, gx = np.mgrid[gpx / 2:H:gpx, gpx / 2:W:gpx]
    g = np.stack([gx.ravel(), gy.ravel()], 1)
    ok = dt[np.clip(g[:, 1].astype(int), 0, H - 1), np.clip(g[:, 0].astype(int), 0, W - 1)] >= 0.10
    pts.append(g[ok])
    P = np.vstack(pts)
    P = np.unique(np.round(P * 4) / 4, axis=0)                                  # niente punti doppi
    tri = Delaunay(P)
    S = tri.simplices
    cen = P[S].mean(axis=1)
    inside = m[np.clip(cen[:, 1].astype(int), 0, H - 1), np.clip(cen[:, 0].astype(int), 0, W - 1)] > 0
    e = np.maximum.reduce([np.hypot(*(P[S[:, i]] - P[S[:, (i + 1) % 3]]).T) for i in range(3)])
    S = S[inside & (e < 70)]
    return P, S, dt

def build(R=0.10, flat=0.85, shade_min=0.78):
    """parti: lista di dict(name, mesh, map, asset, h) e immagini jpeg"""
    prm = json.load(open(f'{ASSETS}/params.json'))
    rgb = cv2.imread(f'{ASSETS}/sagoma_rgb.png'); mask = cv2.imread(f'{ASSETS}/sagoma_mask.png', 0); back = cv2.imread(f'{ASSETS}/sagoma_back.png')
    ppm = (prm['bottom_row'] - prm['top_row']) / prm['height_m']; u0 = prm['cx']; v_base = prm['bottom_row']
    P, S, dt = triangulate(mask, ppm, R)
    H, W = mask.shape
    def bil(a, u, v):
        ui = np.clip(u, 0, W - 1.001); vi = np.clip(v, 0, H - 1.001); i0 = ui.astype(int); j0 = vi.astype(int); fu = ui - i0; fv = vi - j0
        return a[j0, i0] * (1 - fu) * (1 - fv) + a[j0, i0 + 1] * fu * (1 - fv) + a[j0 + 1, i0] * (1 - fu) * fv + a[j0 + 1, i0 + 1] * fu * fv
    dts = cv2.GaussianBlur(dt, (0, 0), 0.0008 * ppm)
    dd = np.minimum(dts, R); hmap = flat * np.sqrt(dd * (2 * R - dd))
    hh = bil(hmap, P[:, 0], P[:, 1]); edge = bil(dt, P[:, 0], P[:, 1]) < 2.4 / ppm      # sul contorno (entro 2 pixel) la profondita' e' 0: davanti e dietro si toccano, il solido e' chiuso
    hh[edge] = 0.0
    hu = np.gradient(hmap, axis=1) * ppm; hv = np.gradient(hmap, axis=0) * ppm
    cosang = 1.0 / np.sqrt(1.0 + bil(hu, P[:, 0], P[:, 1]) ** 2 + bil(hv, P[:, 0], P[:, 1]) ** 2)
    f = 255.0 * (shade_min + (1 - shade_min) * np.clip(cosang, 0, 1) ** 0.8)
    X = (P[:, 0] - u0) / ppm; Y = (v_base - P[:, 1]) / ppm; UV = np.stack([P[:, 0] / W, 1.0 - P[:, 1] / H], 1)
    C = np.stack([f, f, f], 1)
    fm = Mesh(); fm._add(np.stack([X, Y, hh], 1), C, [tuple(t) for t in S], UV)
    bm = Mesh(); bm._add(np.stack([X, Y, -hh], 1), C, [(int(a), int(c), int(b)) for a, b, c in S], UV)
    tex = fill_outside(rgb, mask); texb = fill_outside(back, mask)
    imgs = {'sagoma_t': jpg(tex, 88), 'sagoma_tb': jpg(cv2.GaussianBlur(texb, (0, 0), 1.0), 80)}
    parts = [dict(name='sagoma_f', mesh=fm, map='sagoma_t', asset='sagoma', h=prm['height_m']),
             dict(name='sagoma_b', mesh=bm, map='sagoma_tb', asset='sagoma', h=prm['height_m'])]
    return parts, imgs

if __name__ == '__main__':
    p, im = build(); print([(q['name'], len(q['mesh'].P), len(q['mesh'].I)) for q in p], {k: len(v) for k, v in im.items()})
    P = np.array(p[0]['mesh'].P); print('limiti x', P[:, 0].min().round(3), P[:, 0].max().round(3), 'y', P[:, 1].min().round(3), P[:, 1].max().round(3), 'z', P[:, 2].min().round(3), P[:, 2].max().round(3))
