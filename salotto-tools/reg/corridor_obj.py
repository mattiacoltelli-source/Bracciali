"""Corridoio dietro l'arco della parete TV (z < 0 nel sistema stanza): un piccolo disimpegno lungo 2,8 m (x da 0,02 a 2,80), profondo 1,40 m dal piano della parete TV, con
a sinistra la porta chiusa di mogano e a destra la seconda porta (anch'essa chiusa), in mezzo le due stampe manga in bianco e nero; zoccolo di marmo bruno, pavimento di marmo.
Misure dalla foto del corridoio (posa ricavata dagli angoli dell'arco e da tre punti della parete TV letti in una foto registrata); il muro di fondo sta a z = -1,40 (pavimento letto in
due foto indipendenti). Texture: stampe e foglia della porta rettificate dalle foto, pavimento rettificato e completato a specchio; l'intonaco e' a colori per vertice con il gradiente di luce visto nella foto
(la luce calda arriva dall'alto). Tutte le parti sono 'deep': l'app le mostra solo da dentro la stanza."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh

ASSETS = os.environ.get('CORR_ASSETS', '/tmp/claude-0/s/st3/corr')
Z_N, Z_F = -0.40, -1.40            # faccia interna della parete TV (l'imbotte dell'arco e' profondo 40 cm, misurato nella foto) e muro di fondo
X_L, X_R, H = 0.02, 2.80, 2.70      # lati del disimpegno e altezza del soffitto
ARCH = (0.46, 1.53)                  # apertura dell'arco nella parete TV (come in room.js)
DOOR = dict(x0=0.385, x1=0.953, y1=1.867, arch_w=0.065)            # foglia della porta chiusa (la sinistra e' nascosta dietro lo stipite dell'arco: l'attacco della maniglia dice 0,385)
DOORWAY = dict(x_out=1.870, x0=1.940, x1=2.720, y1=1.890, arch_w=0.070)  # secondo vano: cornice marrone e interno buio (a destra la cornice simmetrica)
PRINTS = [dict(x0=1.194, x1=1.672, y0=1.399, y1=2.065, tile=0), dict(x0=1.198, x1=1.686, y0=0.632, y1=1.302, tile=1)]   # le due stampe (circa 48 x 67 cm)
BASE_H = 0.07
ARCH_H = 1.989                       # altezza dell'architrave dell'arco (come nell'imbotte)
# per l'app: il disimpegno (da dove si cammina) e il passaggio dell'arco
ZONE = dict(x0=X_L, x1=X_R, zn=Z_N, zf=Z_F, h=H, arch=[ARCH[0], ARCH[1], ARCH_H])

# gradiente di luce sul muro di fondo (colori letti nella foto, dal basso verso l'alto): la luce calda arriva dall'alto
GRAD = [(0.00, (140, 122, 95)), (0.25, (155, 136, 111)), (0.70, (173, 155, 125)), (1.20, (197, 182, 148)), (1.70, (236, 213, 181)), (1.95, (253, 231, 195)), (2.20, (255, 236, 200)), (2.70, (255, 236, 202))]

def plaster(y, k=1.0):
    ys = np.array([g[0] for g in GRAD]); out = np.zeros(np.shape(y) + (3,))
    for c in range(3): out[..., c] = np.interp(y, ys, [g[1][c] for g in GRAD])
    return out * k

def _band_quad(mesh, P0, P1, y0, y1, k, ref, n=10, two=True):
    """parete verticale da P0 a P1 (punti sul pavimento) fra le quote y0 e y1: bande orizzontali con il colore (per vertice) del gradiente di luce, cosi' le sfumature sono continue"""
    ys = np.linspace(y0, y1, n + 1); P0 = np.asarray(P0, float); P1 = np.asarray(P1, float)
    for i in range(n):
        a, b = ys[i], ys[i + 1]; ca = plaster(a, k); cb = plaster(b, k)
        mesh.quad_grad([P0 + np.array([0, a, 0]), P1 + np.array([0, a, 0]), P1 + np.array([0, b, 0]), P0 + np.array([0, b, 0])], [ca, ca, cb, cb], ref=ref, two=two, k=1.0)

def _box(mesh, x0, x1, y0, y1, z0, z1, col, faces=None, k=1.0):
    if faces is None: faces = {f: col for f in ('+x', '-x', '+y', '-y', '+z', '-z')}
    mesh.box((x0, y0, z0), (x1, y1, z1), faces, k=k)

def _largest_rect(m):
    """rettangolo (y0, y1, x0, x1) piu' grande tutto vero in una maschera booleana (istogramma e pila)"""
    h, w = m.shape; hist = np.zeros(w, int); best = (0, 0, 0, 0, 0)
    for y in range(h):
        hist = np.where(m[y], hist + 1, 0); st = []
        for x in range(w + 1):
            cur = hist[x] if x < w else 0; start = x
            while st and st[-1][1] >= cur:
                s0, hh = st.pop(); area = hh * (x - s0)
                if area > best[0]: best = (area, y - hh + 1, y + 1, s0, x)
                start = s0
            st.append((start, cur))
    return best[1:]

def _fill_floor(raw, valid, ppm):
    """completa le zone senza foto con copie a specchio del rettangolo valido piu' grande (i bordi sono sfumati); la parte valida originale resta"""
    h, w = raw.shape[:2]
    core = cv2.erode(valid.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    y0, y1, x0, x1 = _largest_rect(core); print('floor: rettangolo valido', (y0, y1, x0, x1), flush=True)
    patch = raw[y0:y1, x0:x1].astype(np.float32); ph, pw = patch.shape[:2]
    big = np.zeros((h, w, 3), np.float32)
    for ty in range(-4, 5):
        for tx in range(-6, 7):
            p = patch
            if ty % 2: p = p[::-1]
            if tx % 2: p = p[:, ::-1]
            oy = y0 + ty * ph; ox = x0 + tx * pw
            ya, yb = max(oy, 0), min(oy + ph, h); xa, xb = max(ox, 0), min(ox + pw, w)
            if ya >= yb or xa >= xb: continue
            big[ya:yb, xa:xb] = p[ya - oy:yb - oy, xa - ox:xb - ox]
    keep = cv2.GaussianBlur(cv2.erode(valid.astype(np.uint8), np.ones((11, 11), np.uint8)).astype(np.float32), (0, 0), 3.0)[..., None]
    fin = raw.astype(np.float32) * keep + big * (1 - keep)
    return np.clip(fin, 0, 255).astype(np.uint8)

def floor_texture(ppm=250):
    """pavimento del corridoio rettificato (x 0..2.8, righe: z da -0.25 a -1.4) e completato dove l'arco non lo lascia vedere"""
    raw = cv2.imread(f'{ASSETS}/floor_raw.png'); h, w = raw.shape[:2]
    cam = np.load(f'{ASSETS}/cam.npy')                                     # centro della camera della foto
    xs = np.arange(0, 2.8, 1 / ppm) + 0.5 / ppm; zs = np.arange(0.0, Z_F, -1 / ppm) - 0.5 / ppm; X, Z = np.meshgrid(xs, zs)
    # validita': il raggio camera -> punto passa dentro l'apertura dell'arco (con 6 cm di margine) e il punto e' nella foto con colore non nero
    t0 = (0 - cam[2]) / (Z - cam[2]); Q0 = cam[None, None, :] + t0[..., None] * (np.stack([X, np.zeros_like(X), Z], -1) - cam[None, None, :])
    ok = (Q0[..., 0] > ARCH[0] + 0.06) & (Q0[..., 0] < ARCH[1] - 0.06) & (Q0[..., 1] > 0.02) & (Q0[..., 1] < 1.9)
    t1 = (Z_N - cam[2]) / (Z - cam[2]); Q1 = cam[None, None, :] + t1[..., None] * (np.stack([X, np.zeros_like(X), Z], -1) - cam[None, None, :])
    ok &= (Q1[..., 0] > ARCH[0] + 0.06) & (Q1[..., 0] < ARCH[1] - 0.06)
    ok &= raw.max(axis=2) > 12
    ok &= (Z < -0.02)
    return _fill_floor(raw, ok, ppm)

def reveal(mesh):
    """imbotte dell'arco (due stipiti e architrave, profondi 40 cm): colori a vertice campionati nella foto del corridoio (sono in ombra: beige spento), con gli orli ripuliti"""
    rv = np.load(f'{ASSETS}/reveal.npz'); x0, x1 = ARCH; h = 1.989; D = -Z_N
    def clean(a):
        a = a.copy(); a[:, 0] = a[:, 1]; a[:, -1] = a[:, -2]; a[0] = a[1]; a[-1] = a[-2]; return a
    L = clean(rv['lintel']); R = clean(rv['right']); Lf = clean(rv['left'])
    zs = np.linspace(0, -D, R.shape[1]); ys = np.linspace(0.05, h - 0.02, R.shape[0]); xs = np.linspace(x0, x1, L.shape[0])
    ref = ((x0 + x1) / 2, 1.0, -D / 2)
    # architrave: sotto, visto da sotto
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            P = [(xs[i], h, zs[j]), (xs[i + 1], h, zs[j]), (xs[i + 1], h, zs[j + 1]), (xs[i], h, zs[j + 1])]
            mesh.quad_grad(P, [L[i, j], L[i + 1, j], L[i + 1, j + 1], L[i, j + 1]], ref=ref, two=True, k=1.0)
    # stipite destro (faccia verso -x): colori dalla foto; stipite sinistro: quasi di taglio nella foto, quindi colori chiari e freddi vicino alla stanza, caldi verso il corridoio
    for i in range(len(ys) - 1):
        for j in range(len(zs) - 1):
            P = [(x1, ys[i], zs[j]), (x1, ys[i], zs[j + 1]), (x1, ys[i + 1], zs[j + 1]), (x1, ys[i + 1], zs[j])]
            mesh.quad_grad(P, [R[i, j], R[i, j + 1], R[i + 1, j + 1], R[i + 1, j]], ref=ref, two=True, k=1.0)
    def left_col(y, z):
        t = min(1.0, max(0.0, -z / D)); cool = np.array([196, 199, 196.0]); warm = np.array([170, 158, 136.0]); g = 0.82 + 0.18 * min(1.0, y / 1.2)
        return (cool * (1 - t) + warm * t) * g
    for i in range(len(ys) - 1):
        for j in range(len(zs) - 1):
            P = [(x0, ys[i], zs[j]), (x0, ys[i], zs[j + 1]), (x0, ys[i + 1], zs[j + 1]), (x0, ys[i + 1], zs[j])]
            mesh.quad_grad(P, [left_col(ys[i], zs[j]), left_col(ys[i], zs[j + 1]), left_col(ys[i + 1], zs[j + 1]), left_col(ys[i + 1], zs[j])], ref=ref, two=True, k=1.0)
    # zoccolo di marmo sugli stipiti
    base = (104, 78, 56)
    for x, sgn in ((x0, 1), (x1, -1)):
        _box(mesh, x if sgn > 0 else x - 0.012, x + 0.012 if sgn > 0 else x, 0.0, BASE_H, -D, 0.0, base)

def jpg(img, q=88):
    ok, b = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q, cv2.IMWRITE_JPEG_OPTIMIZE, 1]); assert ok; return b.tobytes()

def build():
    """parti del corridoio: lista di dict(name, mesh, map) e immagini jpeg"""
    parts = []; imgs = {}
    refc = (1.4, 1.2, -0.8)                     # punto interno al disimpegno, per orientare le facce
    # --- muri e soffitto (colori per vertice con il gradiente di luce) ---
    walls = Mesh()
    _band_quad(walls, (X_L, 0, Z_F), (X_R, 0, Z_F), 0, H, 1.0, refc)                      # muro di fondo
    _band_quad(walls, (X_L, 0, Z_N), (X_L, 0, Z_F), 0, H, 0.80, refc)                     # muro sinistro
    _band_quad(walls, (X_R, 0, Z_F), (X_R, 0, Z_N), 0, H, 0.80, refc)                     # muro destro
    walls.quad((X_L, H, Z_N), (X_R, H, Z_N), (X_R, H, Z_F), (X_L, H, Z_F), tuple(plaster(2.4, 0.80)), ref=refc, two=True)       # soffitto
    # retro della parete TV (z = Z_N) visto da dentro il disimpegno, con il buco dell'arco: stesso intonaco e stesso gradiente di luce
    _band_quad(walls, (X_L, 0, Z_N), (ARCH[0], 0, Z_N), 0, H, 0.84, refc)
    _band_quad(walls, (ARCH[1], 0, Z_N), (X_R, 0, Z_N), 0, H, 0.84, refc)
    _band_quad(walls, (ARCH[0], 0, Z_N), (ARCH[1], 0, Z_N), ARCH_H, H, 0.84, refc)
    parts.append(dict(name='corr_walls', mesh=walls, map=None))
    # --- zoccolo di marmo bruno e cornici ---
    trim = Mesh()
    base = (104, 78, 56); base_top = (138, 110, 84)
    for (a, b) in (((X_L, Z_F), (X_R, Z_F)),):
        pass
    _box(trim, X_L, X_R, 0, BASE_H, Z_F, Z_F + 0.012, base, faces=dict([('+z', base), ('+y', base_top), ('+x', base), ('-x', base)]))              # fondo
    _box(trim, X_L, X_L + 0.012, 0, BASE_H, Z_F, Z_N, base, faces=dict([('+x', base), ('+y', base_top), ('+z', base), ('-z', base)]))               # sinistro
    _box(trim, X_R - 0.012, X_R, 0, BASE_H, Z_F, Z_N, base, faces=dict([('-x', base), ('+y', base_top), ('+z', base), ('-z', base)]))              # destro
    _box(trim, X_L, ARCH[0], 0, BASE_H, Z_N - 0.012, Z_N, base, faces=dict([('-z', base), ('+y', base_top), ('+x', base), ('-x', base)]))          # retro della parete TV, a sinistra dell'arco
    _box(trim, ARCH[1], X_R, 0, BASE_H, Z_N - 0.012, Z_N, base, faces=dict([('-z', base), ('+y', base_top), ('+x', base), ('-x', base)]))          # e a destra
    d = DOOR; aw = d['arch_w']; fz = Z_F
    frame = (66, 32, 19); frame_hi = (88, 45, 28)
    def casing(x0, x1, y1, w, zc=0.0, deep=0.011):
        # cornice a due gradini (coprifilo esterno largo e bordo interno piu' sporgente) attorno all'apertura x0..x1 fino a y1
        _box(trim, x0 - w, x0, 0.0, y1 + w, fz, fz + deep, frame_hi, faces=dict([('+z', frame_hi), ('+x', frame), ('-x', frame), ('+y', frame)]))        # montante sinistro
        _box(trim, x1, x1 + w, 0.0, y1 + w, fz, fz + deep, frame_hi, faces=dict([('+z', frame_hi), ('+x', frame), ('-x', frame), ('+y', frame)]))        # montante destro
        _box(trim, x0 - w, x1 + w, y1, y1 + w, fz, fz + deep, frame_hi, faces=dict([('+z', frame_hi), ('+y', frame), ('-y', frame), ('+x', frame), ('-x', frame)]))   # traverso
        iw = w * 0.45                                                                          # bordo interno, un po' piu' sporgente
        _box(trim, x0 - iw, x0, 0.0, y1 + iw, fz, fz + deep + 0.012, frame, faces=dict([('+z', frame), ('+x', frame_hi)]))
        _box(trim, x1, x1 + iw, 0.0, y1 + iw, fz, fz + deep + 0.012, frame, faces=dict([('+z', frame), ('-x', frame_hi)]))
        _box(trim, x0 - iw, x1 + iw, y1, y1 + iw, fz, fz + deep + 0.012, frame, faces=dict([('+z', frame), ('-y', frame_hi)]))
    casing(d['x0'], d['x1'], d['y1'], aw)
    w2 = DOORWAY
    # secondo vano: cornice solo sul lato sinistro e in alto (il resto sta dietro lo stipite destro dell'arco), interno nero
    casing(w2['x0'], w2['x1'], w2['y1'], w2['arch_w'])
    # secondo vano: anche questa porta e' chiusa (nelle foto era aperta, con l'interno buio). Foglia uguale a quella di sinistra (stessa texture, riflessa: la maniglia sta sul lato lontano
    # dall'arco, che da dentro la stanza resta nascosto dallo stipite destro), alla stessa profondita'; la cornice e' quella di prima
    fz2 = fz + 0.014
    reveal(trim)
    parts.append(dict(name='corr_trim', mesh=trim, map=None))
    # --- foglia della porta (texture rettificata dalla foto) ---
    door = cv2.imread(f'{ASSETS}/door_raw.png'); ppm = 600
    c0 = int(round((d['x0'] - 0.34) * ppm)); c1 = int(round((d['x1'] - 0.34) * ppm)); r0 = int(round((1.95 - d['y1']) * ppm)); r1 = int(round((1.95 - 0.02) * ppm))
    leaf = door[r0:r1, c0:c1]
    imgs['corr_door'] = jpg(leaf, 90)
    dm = Mesh(); dz = fz + 0.014
    dm._add([(d['x0'], 0.02, dz), (d['x1'], 0.02, dz), (d['x1'], d['y1'], dz), (d['x0'], d['y1'], dz)], [(255, 255, 255)] * 4, [(0, 1, 2), (0, 2, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)])
    parts.append(dict(name='corr_leaf', mesh=dm, map='corr_door'))
    d2 = Mesh()
    d2._add([(w2['x0'], 0.02, fz2), (w2['x1'], 0.02, fz2), (w2['x1'], w2['y1'], fz2), (w2['x0'], w2['y1'], fz2)], [(255, 255, 255)] * 4, [(0, 1, 2), (0, 2, 3)], [(1, 0), (0, 0), (0, 1), (1, 1)])
    parts.append(dict(name='corr_leaf2', mesh=d2, map='corr_door'))
    # --- stampe ---
    p1 = cv2.imread(f'{ASSETS}/print1.png'); p2 = cv2.imread(f'{ASSETS}/print2.png')
    tw, th = 512, 716
    atlas = np.concatenate([cv2.resize(p1, (tw, th), interpolation=cv2.INTER_AREA), cv2.resize(p2, (tw, th), interpolation=cv2.INTER_AREA)], 1)
    imgs['corr_prints'] = jpg(atlas, 84)
    pm = Mesh(); pz = fz + 0.006
    for p in PRINTS:
        u0, u1 = p['tile'] * 0.5, p['tile'] * 0.5 + 0.5
        pm._add([(p['x0'], p['y0'], pz), (p['x1'], p['y0'], pz), (p['x1'], p['y1'], pz), (p['x0'], p['y1'], pz)], [(255, 255, 255)] * 4, [(0, 1, 2), (0, 2, 3)], [(u0, 0), (u1, 0), (u1, 1), (u0, 1)])
    parts.append(dict(name='corr_prints', mesh=pm, map='corr_prints'))
    # --- pavimento ---
    fl = floor_texture(); imgs['corr_floor'] = jpg(fl, 86)
    fm = Mesh()
    # righe della texture: z da 0 (riga 0, in alto) a -1.4: v = 1 in alto
    fm._add([(0.0, 0.0, 0.0), (2.8, 0.0, 0.0), (2.8, 0.0, Z_F), (0.0, 0.0, Z_F)], [(255, 255, 255)] * 4, [(0, 1, 2), (0, 2, 3)], [(0, 1), (1, 1), (1, 0), (0, 0)])
    parts.append(dict(name='corr_floor', mesh=fm, map='corr_floor'))
    return parts, imgs
