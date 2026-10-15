"""Oggetti sopra la credenza: vaso smaltato grande, portabottiglie con le bottiglie, ciotola di rame.
Forme da sagome misurate nelle foto registrate; i colori (smalto, etichette, capsule) sono cotti dalle foto registrate proiettando la superficie con la loro posa (phototex.py).
Coordinate del sistema stanza (nuovo): la credenza sta lungo la parete A (x = 0), il piano e' a y = 0,801."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh
import phototex as PT

Y_TOP = 0.801
VASE_AXIS = (0.155, 1.945)          # asse del vaso: triangolato da due foto registrate e affinato sulle silhouette (IoU)
# profilo del vaso: (quota sul piano in m, raggio in m) dal contorno nella foto registrata a 2 m (scala da asse e bocca triangolati: bocca a 1,20 m, piede a 0,80 m)
VASE_PROFILE = [(0.000, 0.060), (0.004, 0.075), (0.012, 0.092), (0.020, 0.104), (0.030, 0.113), (0.040, 0.122), (0.050, 0.129), (0.060, 0.133), (0.070, 0.136), (0.080, 0.139), (0.090, 0.1405),
                (0.100, 0.141), (0.110, 0.1395), (0.120, 0.138), (0.130, 0.1352), (0.140, 0.1308), (0.150, 0.1252), (0.160, 0.1178), (0.170, 0.1091), (0.180, 0.092), (0.190, 0.0811),
                (0.200, 0.0699), (0.210, 0.0578), (0.220, 0.0513), (0.230, 0.0475), (0.240, 0.0451), (0.250, 0.0395), (0.260, 0.0364), (0.270, 0.0323), (0.280, 0.0277), (0.290, 0.0258),
                (0.300, 0.0267), (0.310, 0.0283), (0.320, 0.0314), (0.330, 0.0348), (0.340, 0.0395), (0.350, 0.0466), (0.360, 0.0566), (0.370, 0.0709), (0.380, 0.0914), (0.390, 0.1047),
                (0.397, 0.1100), (0.400, 0.1100)]

RSCALE = 0.93        # i raggi del profilo sono stati letti con 1609 px/m (scala verticale): in orizzontale, fuori asse, la prospettiva da' 1750 px/m (verificato sulle silhouette di due foto)

def _radius(y):
    ys = np.array([p[0] for p in VASE_PROFILE]); rs = np.array([p[1] for p in VASE_PROFILE])
    return np.interp(y, ys, rs) * RSCALE

def vase_surface(nphi, ny):
    """punti e normali (ny, nphi, 3) del vaso (colonne = angolo attorno all'asse da 0 a 2 pi, righe = quota dall'alto in basso); y in [0, 0.40]"""
    H = VASE_PROFILE[-1][0]
    ys = (1 - (np.arange(ny) + 0.5) / ny) * H                      # riga 0 = bocca
    ph = (np.arange(nphi) + 0.5) / nphi * 2 * np.pi
    Y, PH = np.meshgrid(ys, ph, indexing='ij')
    r = _radius(Y); dr = (_radius(Y + 0.002) - _radius(Y - 0.002)) / 0.004
    P = np.stack([VASE_AXIS[0] + r * np.cos(PH), Y_TOP + Y, VASE_AXIS[1] + r * np.sin(PH)], -1)
    N = np.stack([np.cos(PH), -dr, np.sin(PH)], -1); N /= np.linalg.norm(N, axis=-1, keepdims=True)
    return P, N, Y, PH

def _mask_valid(maskfile, origin, shape, erode=7, ignore_boxes=()):
    """funzione di validita' per phototex.bake: un punto vale solo se cade ben dentro la maschera dell'oggetto nella foto (niente sfondo ai bordi)"""
    full = np.zeros(shape, np.uint8); mk = cv2.imread(maskfile, 0); x0, y0 = origin
    cnt, _ = cv2.findContours((mk > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)      # solo il contorno esterno: i riflessi non bucano la maschera
    solid = np.zeros(mk.shape, np.uint8); cv2.drawContours(solid, cnt, -1, 1, -1)
    full[y0:y0 + mk.shape[0], x0:x0 + mk.shape[1]] = solid
    full = cv2.erode(full, np.ones((erode, erode), np.uint8))
    for (xa, ya, xb, yb) in ignore_boxes: full[ya:yb, xa:xb] = 0
    def f(u, v, P):
        ui = np.clip(np.round(u).astype(int), 0, shape[1] - 1); vi = np.clip(np.round(v).astype(int), 0, shape[0] - 1)
        return full[vi, ui].astype(np.float32)
    return f

MASKS = os.environ.get('VASE_MASKS', os.environ.get('CONSOLE_ASSETS', '/tmp/claude-0/s/st3/assets'))

def vase_texture(size=(576, 576)):
    nphi, ny = size
    P, N, Y, PH = vase_surface(nphi, ny)
    cs = [PT.Cam('3039c671'), PT.Cam('8ebbe415')]
    valid = {'3039c671': _mask_valid(f'{MASKS}/vase3039_mask.png', (600, 230), (2304, 4096), ignore_boxes=((600, 900, 1300, 960),)),
             '8ebbe415': _mask_valid(f'{MASKS}/vase8eb_mask.png', (1250, 700), (2304, 4096), ignore_boxes=((1250 + 100, 700 + 215, 1250 + 175, 700 + 300),))}
    img, wt = PT.bake(P, N, cs, valid=valid, power=2.0, min_cos=0.04)
    img = PT.fill_holes(img, wt)
    return np.clip(img, 0, 255).astype(np.uint8), wt

def vase_mesh(mesh, nphi=72, rows=None):
    """mesh del vaso con UV sulla texture (colonna = angolo, riga = quota dall'alto); coordinate stanza"""
    H = VASE_PROFILE[-1][0]
    ys = np.array([p[0] for p in VASE_PROFILE])[::-1] if rows is None else rows        # dall'alto
    ys = np.concatenate([[H], np.linspace(H - 0.005, 0.0, 100)])
    ys = np.unique(np.round(ys, 5))[::-1]
    nv = len(ys)
    ph = np.linspace(0, 2 * np.pi, nphi + 1)
    Y, PH = np.meshgrid(ys, ph, indexing='ij')
    r = _radius(Y)
    P = np.stack([VASE_AXIS[0] + r * np.cos(PH), Y_TOP + Y, VASE_AXIS[1] + r * np.sin(PH)], -1)
    UV = np.stack([PH / (2 * np.pi), (Y / H)], -1)                   # v = 1 in alto (le texture hanno la riga 0 in cima: UV con origine in basso)
    # ombra fissa per faccia: il colore e' gia' quello della foto; solo un velo leggero per dare volume
    cols = np.full(P.shape, 255.0)
    idx = np.arange(nv * (nphi + 1)).reshape(nv, nphi + 1)
    T = []
    for j in range(nv - 1):
        for i in range(nphi):
            a, b, c, d = idx[j, i], idx[j, i + 1], idx[j + 1, i + 1], idx[j + 1, i]
            T += [(a, b, c), (a, c, d)]
    mesh._add(P.reshape(-1, 3), cols.reshape(-1, 3), T, UV.reshape(-1, 2))


def vase_inner(mesh):
    """interno del collo (visto dall'alto): superficie scura e il bordo piatto della bocca; colori a vertice"""
    H = VASE_PROFILE[-1][0]; cx, cz = VASE_AXIS
    ph = np.linspace(0, 2 * np.pi, 49)
    # bordo: anello piatto fra il raggio esterno e quello interno della bocca
    ro = float(_radius(H)); ri = ro - 0.008; y = Y_TOP + H
    for i in range(48):
        a, b = ph[i], ph[i + 1]
        P = [(cx + ro * np.cos(a), y, cz + ro * np.sin(a)), (cx + ro * np.cos(b), y, cz + ro * np.sin(b)), (cx + ri * np.cos(b), y - 0.001, cz + ri * np.sin(b)), (cx + ri * np.cos(a), y - 0.001, cz + ri * np.sin(a))]
        mesh.quad(*P, (214, 208, 196), two=True, k=1.0)
    # interno: dalla bocca in giu' per 12 cm, brunendo
    ys = np.linspace(H - 0.001, H - 0.14, 14)
    for j in range(len(ys) - 1):
        r0 = float(_radius(ys[j])) - 0.008 * (1 - (H - ys[j]) / 0.14); r1 = float(_radius(ys[j + 1])) - 0.008
        c0 = np.array([150, 130, 100]) * (1 - 0.75 * (H - ys[j]) / 0.14); c1 = np.array([150, 130, 100]) * (1 - 0.75 * (H - ys[j + 1]) / 0.14)
        for i in range(48):
            a, b = ph[i], ph[i + 1]
            P = [(cx + r0 * np.cos(a), Y_TOP + ys[j], cz + r0 * np.sin(a)), (cx + r0 * np.cos(b), Y_TOP + ys[j], cz + r0 * np.sin(b)),
                 (cx + r1 * np.cos(b), Y_TOP + ys[j + 1], cz + r1 * np.sin(b)), (cx + r1 * np.cos(a), Y_TOP + ys[j + 1], cz + r1 * np.sin(a))]
            mesh._add(P, [c0, c0, c1, c1], [(0, 1, 2), (0, 2, 3)])

# ---------------------------------------------------------------- portabottiglie nero con sei bottiglie
RACK = dict(cx=0.1581, cz=0.5575, yaw=-0.4819, W=0.2148, D=0.1934, y0=0.801, y1=1.1061, bar=0.0095)      # telaio ruotato di ~27,6 gradi: il lato lungo (con le etichette) guarda verso la stanza e l'ingresso; adattato agli angoli visti in tre foto registrate (scarto 3,5 px)

def rack_axes():
    c, s = np.cos(RACK['yaw']), np.sin(RACK['yaw'])
    ed = np.array([c, 0.0, -s]); ew = np.array([s, 0.0, c]); return ed, ew        # ed: profondita' (verso la stanza), ew: larghezza (lungo le bottiglie)

def rack_world(lx, y, lz):
    ed, ew = rack_axes(); o = np.array([RACK['cx'], 0.0, RACK['cz']])
    lx = np.asarray(lx, float)[..., None]; lz = np.asarray(lz, float)[..., None]; y = np.asarray(y, float)[..., None]
    return o + lx * ed + lz * ew + y * np.array([0.0, 1.0, 0.0])

def rack_bars():
    """sbarre del telaio come scatole locali (lx0, lx1, y0, y1, lz0, lz1)"""
    W2, D2, b = RACK['W'] / 2, RACK['D'] / 2, RACK['bar']; y0, y1 = RACK['y0'], RACK['y1']
    B = []
    for ly in (y0, y1 - b):                                                   # rettangoli in basso e in alto
        B += [(-D2, D2, ly, ly + b, -W2, -W2 + b), (-D2, D2, ly, ly + b, W2 - b, W2), (-D2, -D2 + b, ly, ly + b, -W2, W2), (D2 - b, D2, ly, ly + b, -W2, W2)]
    for sx in (-1, 1):
        for sz in (-1, 1):                                                    # montanti agli angoli
            lx0 = (D2 - b) if sx > 0 else -D2; lz0 = (W2 - b) if sz > 0 else -W2
            B.append((lx0, lx0 + b, y0, y1, lz0, lz0 + b))
    bm = 0.005
    for ym in (0.9, 0.995):                                                   # traversi sotto le file di bottiglie, davanti e dietro
        for sx in (-1, 1):
            lx0 = (D2 - bm) if sx > 0 else -D2
            B.append((lx0, lx0 + bm, ym, ym + bm, -W2, W2))
    return B

BOTTLE_L0 = 0.285          # lunghezza di riferimento del profilo; ogni bottiglia lo scala alla sua lunghezza
BOTTLE_PROFILE = [(0.000, 0.0), (0.002, 0.026), (0.006, 0.033), (0.012, 0.0362), (0.020, 0.0370), (0.165, 0.0370), (0.178, 0.0362), (0.190, 0.0335), (0.200, 0.0290), (0.210, 0.0230),
                  (0.220, 0.0170), (0.230, 0.0143), (0.240, 0.0138), (0.2395, 0.0150), (0.270, 0.0150), (0.283, 0.0152), (0.285, 0.0145), (0.285, 0.0)]
CAPS = {('f', 0): (96, 22, 42), ('r', 0): (236, 236, 232), ('f', 1): (196, 156, 60), ('r', 1): (24, 24, 26), ('f', 2): (150, 18, 24), ('r', 2): (24, 24, 26)}     # colori delle capsule (davanti, dietro) per fila dall'alto

def bottles():
    """elenco delle sei bottiglie: dict(nome, quota dell'asse, lx, direzione (+1/-1 lungo lz), lz della base, lunghezza, capsula). Estremi misurati in tre foto registrate (3039c671, 6d89137e, 4bd3d963)."""
    return [dict(name='f0', y=1.0428, lx=+0.045, d=-1, lzb=+0.1333, L=0.2962, cap=CAPS[('f', 0)]),
            dict(name='f1', y=0.9457, lx=+0.045, d=-1, lzb=+0.0850, L=0.2504, cap=CAPS[('f', 1)]),       # la bottiglia di mezzo e' piu' corta e arretrata
            dict(name='f2', y=0.8497, lx=+0.045, d=-1, lzb=+0.1285, L=0.2924, cap=CAPS[('f', 2)]),
            dict(name='r0', y=1.0320, lx=-0.045, d=+1, lzb=-0.1275, L=0.3000, cap=CAPS[('r', 0)]),       # dietro: il collo sporge a sinistra (verso +lz)
            dict(name='r1', y=0.9517, lx=-0.045, d=+1, lzb=-0.1100, L=0.3003, cap=CAPS[('r', 1)]),
            dict(name='r2', y=0.8497, lx=-0.045, d=+1, lzb=-0.1400, L=0.3000, cap=CAPS[('r', 2)])]

def _bottle_r(sl, L=BOTTLE_L0):
    k = L / BOTTLE_L0
    ss = np.array([p[0] for p in BOTTLE_PROFILE]) * k; rr = np.array([p[1] for p in BOTTLE_PROFILE])
    return np.interp(sl, ss, rr)

LABELS = {'f0': (0.038, 0.168), 'f1': (0.093, 0.2036), 'f2': (0.093, 0.164)}            # tratto della bottiglia (m dalla base, con la lunghezza di riferimento 0,285) coperto dall'etichetta, dalla foto frontale
LABEL_A = np.radians(68.0)                                                                  # mezzo arco visibile dell'etichetta

def _bar_box(mesh, x0, x1, y0, y1, z0, z1, col=(24, 24, 26)):
    C = lambda lx, y, lz: rack_world(lx, y, lz)
    P = {(i, j, k): C((x0, x1)[i], (y0, y1)[j], (z0, z1)[k]) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    ctr = C((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    faces = [((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)), ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)),
             ((1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)), ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))]
    for f in faces: mesh.quad(*[P[k] for k in f], col, ref=ctr, k=1.0)

def rack_meshes(label_dir):
    """telaio, bottiglie (vetro + capsule a colori per vertice) e etichette (texture): ritorna (parti, immagini)"""
    from meshlib import hex2rgb
    solid = Mesh(); dec = Mesh(); imgs = {}
    for b in rack_bars(): _bar_box(solid, *b)
    up = np.array([0.0, 1.0, 0.0]); ed, ew = rack_axes()
    for b in bottles():
        def f(U, V, b=b):
            th = 2 * np.pi * U; sl = V * b['L']; r = _bottle_r(sl, b['L'])
            lz = b['lzb'] + b['d'] * sl; lx = b['lx'] + r * np.cos(th); y = b['y'] + r * np.sin(th)
            return rack_world(lx, y, lz)
        def col(U, V, P, N, b=b):
            th = 2 * np.pi * U; sl = V * BOTTLE_L0       # quota nel profilo di riferimento (la capsula inizia a 0,2385 su 0,285)
            dth = (th - np.radians(48) + np.pi) % (2 * np.pi) - np.pi
            hl = np.exp(-(dth / np.radians(11)) ** 2) * (0.55 + 0.45 * np.clip((sl - 0.05) / 0.12, 0, 1) * np.clip((0.235 - sl) / 0.06, 0, 1))       # riflesso lungo la bottiglia
            glass = np.stack([13 + 58 * hl, 13 + 60 * hl, 15 + 62 * hl], -1)
            dth2 = (th + np.radians(40) + np.pi) % (2 * np.pi) - np.pi
            foil = (0.62 + 0.55 * np.exp(-(dth / np.radians(16)) ** 2) - 0.25 * np.exp(-(dth2 / np.radians(30)) ** 2))[..., None]               # stagnola: fascia chiara e fascia scura
            capc = np.array(b['cap'], float) * foil
            m = (sl > 0.2385)[..., None]
            return np.where(m, capc, glass)
        from console_obj import param
        param(solid, f, 28, 40, col, ref=rack_world(b['lx'], b['y'], b['lzb'] + b['d'] * b['L'] / 2), k=1.0)
        # anello nero attorno al collo, saldato al montante dal lato del collo
        lz_ring = (-RACK['W'] / 2 + RACK['bar'] / 2) if b['d'] < 0 else (RACK['W'] / 2 - RACK['bar'] / 2)
        def ring(U, V, b=b, lz_ring=lz_ring, R_=0.0215, r_=0.0042):
            t_ = 2 * np.pi * U; p_ = 2 * np.pi * V
            return rack_world(b['lx'] + (R_ + r_ * np.cos(p_)) * np.cos(t_), b['y'] + (R_ + r_ * np.cos(p_)) * np.sin(t_), lz_ring + r_ * np.sin(p_))
        param(solid, ring, 20, 8, lambda U, V, P, N: np.broadcast_to(np.array([26.0, 26.0, 29.0]), P.shape).copy(), two=True, k=1.0)
    # etichette: strisce curve sulle tre bottiglie davanti, con UV sull'atlante verticale
    names = ['f0', 'f1', 'f2']; tw = 384; tiles = []
    for n in names:
        im = cv2.imread(f'{label_dir}/label_{n}.png'); hh = int(tw * im.shape[0] / im.shape[1]); tiles.append(cv2.resize(im, (tw, hh), interpolation=cv2.INTER_AREA))
    TH = sum(t.shape[0] for t in tiles); atlas = np.zeros((TH, tw, 3), np.uint8); y0 = 0; offs = []
    for t in tiles: atlas[y0:y0 + t.shape[0]] = t; offs.append((y0, y0 + t.shape[0])); y0 += t.shape[0]
    imgs['cobj_labels'] = jpg_(atlas, 88)
    bmap = {b['name']: b for b in bottles()}
    for n, (ya, yb_) in zip(names, offs):
        b = bmap[n]; kL = b['L'] / BOTTLE_L0; s0, s1 = LABELS[n][0] * kL, LABELS[n][1] * kL; nA, nT = 22, 18
        sl = np.linspace(s0, s1, nA + 1); th = np.linspace(LABEL_A, -LABEL_A, nT + 1)          # theta misurato dal davanti (+ed) verso l'alto
        r = _bottle_r(sl, b['L']) + 0.0004
        P = np.zeros((nT + 1, nA + 1, 3)); UV = np.zeros((nT + 1, nA + 1, 2))
        for i, t in enumerate(th):
            for j, s_ in enumerate(sl):
                lz = b['lzb'] + b['d'] * s_
                P[i, j] = rack_world(b['lx'] + r[j] * np.cos(t), b['y'] + r[j] * np.sin(t), lz)
                # texture: orizzontale lungo l'asse (dalla base verso il collo e' da sinistra a destra nella foto), verticale = sin(theta) come visto di fronte
                u = (s_ - s0) / (s1 - s0); v = 0.5 - 0.5 * np.sin(t) / np.sin(LABEL_A)
                UV[i, j] = (u, 1 - (ya + v * (yb_ - ya)) / TH)
        idx = np.arange((nT + 1) * (nA + 1)).reshape(nT + 1, nA + 1); T = []
        for i in range(nT):
            for j in range(nA):
                a, b2, c, d = idx[i, j], idx[i, j + 1], idx[i + 1, j + 1], idx[i + 1, j]; T += [(a, b2, c), (a, c, d)]
        dec._add(P.reshape(-1, 3), np.full((P.shape[0] * P.shape[1], 3), 255.0), T, UV.reshape(-1, 2))
    parts = [dict(name='rack', mesh=solid, map=None), dict(name='rack_labels', mesh=dec, map='cobj_labels')]
    return parts, imgs

# ---------------------------------------------------------------- ciotola di rame con l'oggetto blu-argento appoggiato dentro
BOWL = dict(cx=0.33, cz=1.31, H=0.0415, rim=0.078)           # posizione dai raggi di tre foto registrate (3039c671, 6d89137e, 4bd3d963); dimensioni dalla silhouette nella frontale a 1,7 m
BOWL_PROFILE = [(0.000, 0.048), (0.002, 0.052), (0.006, 0.058), (0.012, 0.0645), (0.020, 0.0705), (0.030, 0.0755), (0.038, 0.0775), (0.0415, 0.078)]     # (quota, raggio): fondo piatto e fianco svasato

def _bowl_r(y):
    ys = np.array([p[0] for p in BOWL_PROFILE]); rs = np.array([p[1] for p in BOWL_PROFILE]); return np.interp(y, ys, rs)

def bowl(mesh, seed=17):
    """ciotola bassa di rame martellato (esterno arancio-bruno a macchie, interno scuro) con un oggetto cilindrico blu-argento e punta nera appoggiato dentro; colori a vertice"""
    from console_obj import param, noise2, noise2_at
    cx, cz, H = BOWL['cx'], BOWL['cz'], BOWL['H']
    nz = noise2(seed, (96, 192), scales=((5, 1.0), (11, 0.8), (30, 0.5)))
    def fo(U, V):
        y = V * H; r = _bowl_r(y)
        return np.stack([cx + r * np.cos(2 * np.pi * U), Y_TOP + y, cz + r * np.sin(2 * np.pi * U)], -1)
    def co(U, V, P, N):
        n = noise2_at(nz, (U * 3.0) % 1.0, V)
        lo = np.array([66.0, 32.0, 18.0]); hi = np.array([172.0, 94.0, 46.0])
        c = lo + (hi - lo) * (n[..., None] ** 0.9)
        c = c * (0.62 + 0.38 * np.clip(V * 1.4, 0, 1))[..., None]                         # piu' scuro verso il fondo
        gl = np.clip(((N[..., 0] * 0.6 + N[..., 2] * 0.4) - 0.35) / 0.45, 0, 1)[..., None]
        c = c + gl * np.array([60.0, 40.0, 22.0]) * (0.4 + 0.6 * n[..., None])
        return c
    param(mesh, fo, 44, 12, co, ref=(cx, Y_TOP + H * 0.5, cz), k=1.0)
    # interno: scuro, appena piu' chiaro verso il bordo
    def fi(U, V):
        y = V * H; r = _bowl_r(y) - 0.0035
        return np.stack([cx + r * np.cos(2 * np.pi * U), Y_TOP + y + 0.0035 * (1 - V), cz + r * np.sin(2 * np.pi * U)], -1)
    def ci(U, V, P, N):
        n = noise2_at(nz, (U * 3.0 + 0.3) % 1.0, V)
        base = np.array([24.0, 15.0, 11.0]) + (np.array([62.0, 38.0, 25.0]) - np.array([24.0, 15.0, 11.0])) * (V[..., None] ** 2.0)
        return base * (0.8 + 0.4 * n[..., None])
    param(mesh, fi, 44, 10, ci, ref=(cx, Y_TOP + H * 2.0, cz), two=True, k=1.0)
    # bordo: anello sottile che chiude fra esterno e interno
    ro = _bowl_r(H); ri = ro - 0.0038; y = Y_TOP + H
    for i in range(44):
        a, b = 2 * np.pi * i / 44, 2 * np.pi * (i + 1) / 44
        mesh.quad((cx + ro * np.cos(a), y, cz + ro * np.sin(a)), (cx + ro * np.cos(b), y, cz + ro * np.sin(b)),
                  (cx + ri * np.cos(b), y, cz + ri * np.sin(b)), (cx + ri * np.cos(a), y, cz + ri * np.sin(a)), (150, 82, 42), two=True, k=1.0)
    # fondo interno
    rb = float(_bowl_r(0.0)) - 0.004; yb = Y_TOP + 0.0036
    for i in range(28):
        a, b = 2 * np.pi * i / 28, 2 * np.pi * (i + 1) / 28
        mesh._add([(cx, yb, cz), (cx + rb * np.cos(a), yb, cz + rb * np.sin(a)), (cx + rb * np.cos(b), yb, cz + rb * np.sin(b))], [(26, 16, 12)] * 3, [(0, 1, 2)])
    # oggetto cilindrico (blu-argento con punta nera) lungo ~11 cm: dal fondo a sinistra (verso +z) sale verso il bordo a destra (verso -z) e sporge poco sopra il bordo
    A = np.array([cx - 0.004, Y_TOP + 0.011, cz + 0.052]); B = np.array([cx - 0.008, Y_TOP + 0.050, cz - 0.046])
    ax = B - A; Ln = np.linalg.norm(ax); ax /= Ln
    def pt(s): return A + ax * (s * Ln)
    s_cap = 0.80
    up = np.array([0.0, 1.0, 0.0]); v = np.cross(up, ax); c_ = float(up @ ax); sk = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    R = np.eye(3) + sk + sk @ sk / (1 + c_)                                           # rotazione che porta l'asse locale y sull'asse dell'oggetto
    blue = (150, 166, 206); blk = (26, 26, 30)
    prof = [(0.0, 0.0, blue), (0.0050, 0.0, blue), (0.0075, s_cap * Ln, blue), (0.0075, s_cap * Ln, blk), (0.0072, Ln, blk), (0.0, Ln, blk)]
    mesh.lathe(tuple(A), prof, seg=14, rot=R, caps=False, two=True, k=1.0)

def build(label_dir=None):
    """tutte le parti degli oggetti sulla credenza: lista di dict(name, mesh, map) e immagini jpeg per il pacchetto"""
    label_dir = label_dir or MASKS
    parts = []; imgs = {}
    tex, wt = vase_texture()
    imgs['cobj_vase'] = jpg_(tex, 90)
    vm = Mesh(); vase_mesh(vm); parts.append(dict(name='vase', mesh=vm, map='cobj_vase'))
    vi = Mesh(); vase_inner(vi); parts.append(dict(name='vase_in', mesh=vi, map=None))
    rp, ri = rack_meshes(label_dir); parts += rp; imgs.update(ri)
    bm = Mesh(); bowl(bm); parts.append(dict(name='bowl', mesh=bm, map=None))
    return parts, imgs

def jpg_(img, q=88):
    ok, b = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q, cv2.IMWRITE_JPEG_OPTIMIZE, 1]); assert ok; return b.tobytes()
