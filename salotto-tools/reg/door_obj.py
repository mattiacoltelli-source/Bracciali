"""Le due porte della stanza, in rilievo davanti al piano della parete (la texture della parete le aveva solo "dipinte", con doppie immagini e angoli sbavati):
- parete A (x = 0): la porta interna chiusa, in noce, con coprifilo, maniglia a leva e bocchetta della chiave;
- parete F (z = 4,5): il portone blindato d'ingresso, in mogano, con coprifilo largo, controtelaio nero, maniglia con placca, pomolo, serratura e spioncino.
Le texture sono le foto frontali dell'utente (non registrate) rettificate sul rettangolo esterno del coprifilo (door_prep.py): la stessa immagine copre coprifilo e foglia, la parte in rilievo
e' fatta di quattro quadri (due montanti, traverso, foglia rientrata) + i bordi a tinta unita; ferramenta in 3D (leva, placche, cilindri, spioncino). Posizioni e misure: angoli esterni del coprifilo
letti in tre foto registrate (A: 6d89137e; F: 6eac1b0f e 79eb58fc, due foto che concordano a 2 mm) e riportati sul piano della parete. Le texture si riportano alla luce delle texture dei muri
(guadagno per canale = intonaco cotto nel pacchetto / intonaco della foto frontale), cosi' non spiccano."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh, rot_x, rot_z

ASSETS = os.environ.get('DOOR_ASSETS', '/tmp/claude-0/s/st3/assets/doors')
PPM = 600                                  # px/m delle texture rettificate
W_ROOM = 4.5                               # parete F: z = 4,5

# a0 = coordinata del bordo sinistro (guardando la parete da dentro: A -> z, F -> x), w = larghezza esterna, y1 = quota del bordo alto del coprifilo,
# sl, sr, top = larghezza del coprifilo davanti a sinistra, destra e in alto, hc = quanto sporge il coprifilo dal muro, hl = quanto la foglia (rientrata)
DOORS = dict(
    A=dict(wall='A', a0=3.439, w=0.886, y1=2.035, sl=0.058, sr=0.053, top=0.063, hc=0.016, hl=0.002, gain=(0.958, 0.920, 0.873), img='door_A_raw.png', name='doorA'),
    F=dict(wall='F', a0=1.624, w=1.236, y1=2.240, sl=0.071, sr=0.071, top=0.071, hc=0.022, hl=0.004, gain=(0.690, 0.660, 0.625), img='door_F_raw.png', name='doorF'),
)

def tex_rect(d):
    """riquadri (a0, a1) della parete della porta nella texture: la texture copre tutto il rettangolo esterno"""
    return 0.0, d['w']

def _P(d, a, y, h):
    """punto nel sistema stanza: a = distanza dal bordo sinistro (verso destra, guardando da dentro), y = quota, h = sporgenza dal piano della parete verso la stanza"""
    if d['wall'] == 'A': return np.array([h, y, d['a0'] - a])
    return np.array([d['a0'] - a, y, W_ROOM - h])

def _gain(d, rgb):
    return tuple(float(np.clip(c * g, 0, 255)) for c, g in zip(rgb, d['gain']))

def texture(d):
    """JPEG della porta: la foto rettificata con il guadagno di luce dei muri"""
    im = cv2.imread(f'{ASSETS}/{d["img"]}').astype(np.float32)
    g = np.array(d['gain'][::-1], np.float32)[None, None, :]             # BGR
    out = np.clip(im * g, 0, 255).astype(np.uint8)
    ok, b = cv2.imencode('.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 90, cv2.IMWRITE_JPEG_OPTIMIZE, 1]); assert ok
    return b.tobytes(), out

def shell(d):
    """quadri con la texture (coprifilo + foglia) e bordi a tinta unita"""
    W, H = d['w'], d['y1']; sl, sr, top = d['sl'], d['sr'], d['top']; hc, hl = d['hc'], d['hl']
    tx = Mesh(); fl = Mesh()
    def tq(a0, a1, y0, y1, h):
        pts = [_P(d, a0, y0, h), _P(d, a1, y0, h), _P(d, a1, y1, h), _P(d, a0, y1, h)]
        tx._add(pts, [(255, 255, 255)] * 4, [(0, 1, 2), (0, 2, 3)], [(a0 / W, y0 / H), (a1 / W, y0 / H), (a1 / W, y1 / H), (a0 / W, y1 / H)])
    tq(0.0, sl, 0.0, H, hc)                       # montante sinistro del coprifilo
    tq(W - sr, W, 0.0, H, hc)                     # montante destro
    tq(sl, W - sr, H - top, H, hc)                # traverso
    e = 0.02                                      # la foglia continua sotto il coprifilo (nascosta): niente fessure da cui si veda il muro
    tq(sl - e, W - sr + e, 0.0, H - top + e, hl)  # foglia (rientrata)
    # bordi: lati esterni del coprifilo e battute interne (tinta unita: il legno del coprifilo, un po' piu' scuro dentro)
    wood = _gain(d, (58, 36, 28)); dark = _gain(d, (30, 20, 17)) if d['wall'] == 'A' else (14, 14, 15)
    ref = _P(d, W / 2, H / 2, -0.1)
    def sq(pts, col): fl.quad(*pts, col, ref=ref, two=True, k=1.0)
    sq([_P(d, 0, 0, 0), _P(d, 0, H, 0), _P(d, 0, H, hc), _P(d, 0, 0, hc)], wood)                               # lato sinistro esterno
    sq([_P(d, W, 0, 0), _P(d, W, H, 0), _P(d, W, H, hc), _P(d, W, 0, hc)], wood)                               # lato destro esterno
    sq([_P(d, 0, H, 0), _P(d, W, H, 0), _P(d, W, H, hc), _P(d, 0, H, hc)], wood)                               # lato alto esterno
    sq([_P(d, sl, 0, hl), _P(d, sl, H - top, hl), _P(d, sl, H - top, hc), _P(d, sl, 0, hc)], dark)             # battuta sinistra
    sq([_P(d, W - sr, 0, hl), _P(d, W - sr, H - top, hl), _P(d, W - sr, H - top, hc), _P(d, W - sr, 0, hc)], dark)   # battuta destra
    sq([_P(d, sl, H - top, hl), _P(d, W - sr, H - top, hl), _P(d, W - sr, H - top, hc), _P(d, sl, H - top, hc)], dark)   # battuta alta
    return tx, fl

def _disc(m, d, a, y, h0, r, th, col_side, col_top, dome=0.0, seg=22):
    """disco (o cupola) che sporge dalla foglia: centro (a, y), base a quota h0, spessore th"""
    rot = rot_z(-np.pi / 2) if d['wall'] == 'A' else rot_x(-np.pi / 2)        # l'asse locale y (altezza del profilo) va verso la stanza
    prof = [(r, 0.0, col_side), (r, th, col_side)]
    if dome > 0: prof += [(r * 0.8, th + dome * 0.5, col_top), (r * 0.45, th + dome * 0.9, col_top), (0.0, th + dome, col_top)]
    else: prof += [(r * 0.86, th + 0.0006, col_top), (0.0, th + 0.0006, col_top)]
    m.lathe(_P(d, a, y, h0), prof, seg=seg, rot=rot, caps=True)

def hardware_A(d):
    m = Mesh(); hl = d['hl']; ra = 0.752; ry = 2.035 - 573.75 / PPM; ky = 2.035 - 626.25 / PPM
    brass = _gain(d, (112, 90, 58)); brass_hi = _gain(d, (138, 112, 72)); darkb = _gain(d, (36, 28, 22))
    _disc(m, d, ra, ry, hl, 0.0195, 0.010, brass, brass_hi, dome=0.004)                       # rosetta della leva
    _disc(m, d, ra, ry, hl + 0.0025, 0.0125, 0.0112, darkb, darkb)                                # la parte scura al centro della rosetta
    # leva: dalla rosetta verso sinistra (lato cerniere), 9,4 cm, sporge a 2,4 cm dalla foglia
    L = 0.094; t = 0.0115; A0, A1 = ra - L, ra
    def box(a0, a1, y0, y1, h0, h1, col, col_top=None):
        ref = _P(d, (a0 + a1) / 2, (y0 + y1) / 2, (h0 + h1) / 2)
        faces = [([_P(d, a0, y0, h1), _P(d, a1, y0, h1), _P(d, a1, y1, h1), _P(d, a0, y1, h1)], col),
                 ([_P(d, a0, y0, h0), _P(d, a1, y0, h0), _P(d, a1, y0, h1), _P(d, a0, y0, h1)], col),
                 ([_P(d, a0, y1, h0), _P(d, a1, y1, h0), _P(d, a1, y1, h1), _P(d, a0, y1, h1)], col_top or col),
                 ([_P(d, a0, y0, h0), _P(d, a0, y1, h0), _P(d, a0, y1, h1), _P(d, a0, y0, h1)], col),
                 ([_P(d, a1, y0, h0), _P(d, a1, y1, h0), _P(d, a1, y1, h1), _P(d, a1, y0, h1)], col)]
        for pts, c in faces: m.quad(*pts, c, ref=ref, two=False, k=1.0)
    box(A0, A1, ry - t / 2, ry + t / 2, hl + 0.012, hl + 0.012 + t, brass, brass_hi)
    box(A0, A0 + 0.016, ry - t / 2 - 0.0008, ry + t / 2 + 0.0008, hl + 0.011, hl + 0.013 + t, brass_hi)           # punta della leva, un po' piu' grossa
    # bocchetta della chiave
    _disc(m, d, ra, ky, hl, 0.0198, 0.0045, brass, _gain(d, (96, 78, 52)))
    ref = _P(d, ra, ky, hl + 0.01)
    m.quad(_P(d, ra - 0.0018, ky - 0.009, hl + 0.0052), _P(d, ra + 0.0018, ky - 0.009, hl + 0.0052), _P(d, ra + 0.0018, ky + 0.004, hl + 0.0052), _P(d, ra - 0.0018, ky + 0.004, hl + 0.0052), (14, 12, 11), two=True, k=1.0)
    return m

def hardware_F(d):
    m = Mesh(); hl = d['hl']; H = d['y1']
    plate = _gain(d, (168, 146, 98)); plate_hi = _gain(d, (190, 166, 112)); lever = _gain(d, (150, 128, 84)); knob = _gain(d, (150, 120, 76)); knob_hi = _gain(d, (186, 152, 98))
    blk = (18, 17, 17); ring = _gain(d, (150, 133, 92)); cover = _gain(d, (140, 120, 78))
    def box(a0, a1, y0, y1, h0, h1, col, col_top=None):
        ref = _P(d, (a0 + a1) / 2, (y0 + y1) / 2, (h0 + h1) / 2)
        faces = [([_P(d, a0, y0, h1), _P(d, a1, y0, h1), _P(d, a1, y1, h1), _P(d, a0, y1, h1)], col_top or col),
                 ([_P(d, a0, y0, h0), _P(d, a1, y0, h0), _P(d, a1, y0, h1), _P(d, a0, y0, h1)], col),
                 ([_P(d, a0, y1, h0), _P(d, a1, y1, h0), _P(d, a1, y1, h1), _P(d, a0, y1, h1)], col),
                 ([_P(d, a0, y0, h0), _P(d, a0, y1, h0), _P(d, a0, y1, h1), _P(d, a0, y0, h1)], col),
                 ([_P(d, a1, y0, h0), _P(d, a1, y1, h0), _P(d, a1, y1, h1), _P(d, a1, y0, h1)], col)]
        for pts, c in faces: m.quad(*pts, c, ref=ref, two=False, k=1.0)
    # placca della maniglia (7,1 x 17,3 cm, bordi smussati: due piani sovrapposti), con il foro scuro attorno al pomolo
    pa0, pa1 = 105.7 / PPM, 148.3 / PPM; py1, py0 = H - 633 / PPM, H - 737 / PPM
    box(pa0, pa1, py0, py1, hl, hl + 0.0035, plate)
    box(pa0 + 0.006, pa1 - 0.006, py0 + 0.006, py1 - 0.006, hl + 0.0035, hl + 0.0052, plate_hi)
    _disc(m, d, 125 / PPM, H - 707 / PPM, hl + 0.0052, 0.0285, 0.0008, blk, blk)                 # foro scuro
    _disc(m, d, 125 / PPM, H - 707 / PPM, hl + 0.0056, 0.0235, 0.010, knob, knob_hi, dome=0.011)   # pomolo (cupola)
    # leva: 13 cm verso destra, dal perno in alto sulla placca
    ly = H - 656 / PPM; la0, la1 = 122 / PPM, 200 / PPM; t = 0.0135
    box(la0 - 0.008, la0 + 0.012, ly - 0.012, ly + 0.012, hl + 0.0052, hl + 0.0052 + 0.016, plate_hi)      # attacco
    box(la0, la1, ly - t / 2, ly + t / 2, hl + 0.014, hl + 0.014 + t, lever, plate_hi)
    # cilindro della serratura in alto (copertura a disco con la fessura)
    _disc(m, d, 120 / PPM, H - 586 / PPM, hl, 0.0235, 0.0075, cover, plate)
    m.quad(_P(d, 120 / PPM - 0.0022, H - 586 / PPM - 0.012, hl + 0.0082), _P(d, 120 / PPM + 0.0022, H - 586 / PPM - 0.012, hl + 0.0082), _P(d, 120 / PPM + 0.0022, H - 586 / PPM + 0.006, hl + 0.0082), _P(d, 120 / PPM - 0.0022, H - 586 / PPM + 0.006, hl + 0.0082), (22, 18, 15), two=True, k=1.0)
    # spioncino: corona d'ottone con la lente nera e, sotto, il copri-foro
    px, py = 371 / PPM, H - 502 / PPM
    _disc(m, d, px, py, hl, 0.0172, 0.0058, ring, plate)
    _disc(m, d, px, py, hl + 0.0059, 0.0078, 0.0006, blk, blk)
    _disc(m, d, px, H - 515 / PPM, hl, 0.0132, 0.0052, cover, plate)
    return m

def build():
    """parti delle porte: lista di dict(name, mesh, map, wall) e immagini jpeg (wall = la parete a cui restano attaccate: spariscono con lei quando la si guarda da fuori)"""
    parts = []; imgs = {}
    for key in ('A', 'F'):
        d = DOORS[key]
        jb, _ = texture(d); imgs[f'{d["name"]}_t'] = jb
        tx, fl = shell(d)
        hw = hardware_A(d) if key == 'A' else hardware_F(d)
        fl.extend(hw)
        parts.append(dict(name=f'{d["name"]}_tex', mesh=tx, map=f'{d["name"]}_t', wall=key))
        parts.append(dict(name=f'{d["name"]}_flat', mesh=fl, map=None, wall=key))
    return parts, imgs

def wall_rects(wall, wall_len, margin=0.05):
    """fascia (u0, u1, y0, y1, morbido) della parete da rifare per diffusione dove c'era dipinta la porta (u = lunghezza - coordinata lungo la parete): coprifilo piu' margine, da 10 cm da terra (sotto resta lo zoccolo di marmo)"""
    d = DOORS[wall]
    c0, c1 = (d['a0'] - d['w'], d['a0'])                 # intervallo della coordinata (z per A, x per F)
    return [(wall_len - (c1 + margin), wall_len - (c0 - margin), 0.10, d['y1'] + margin, True)]

if __name__ == '__main__':
    p, im = build(); print([(q['name'], len(q['mesh'].P)) for q in p], {k: len(v) for k, v in im.items()})
