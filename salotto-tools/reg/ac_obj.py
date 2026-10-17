"""Split Daikin (Siesta) sulla parete A, sopra la porta interna: prima era cotto nella texture del muro (decalcomania sfocata, con le strisce di luce delle foto e l'alone d'ombra),
ora e' un corpo 3D che sporge dal muro:
- cappuccio (pannello frontale, leggermente inclinato in avanti in alto) e fronte della bocca d'aria (feritoia e schermo) come due facce con la texture della foto frontale dell'utente (81d8e52c, non registrata):
  `console/ac_prep.py` raddrizza sui due rettangoli del modello i quadrilateri letti sulla foto (cappuccio: rette adattate ai bordi; bocca d'aria: angoli letti sulla foto ingrandita);
- fianchi, sopra e sotto in colore pieno col bianco della plastica (media della texture);
- misure: larghezza 75 cm (dagli angoli sul piano frontale: 74-76 cm con le foto registrate, 73-75 con la frontale), bordo alto a 2,727 m (la sovrapposizione del modello sulla 6d89137e, che sul coprifilo della porta torna a 1 mm, dice +2,1 cm rispetto a 2,705; frontale + 6d89137e
  triangolati: 2,70; 4bd3d963 ha ~4,7 cm di errore in verticale gia' sul coprifilo, corretto torna a +1 cm), cappuccio alto 20,8 cm in verticale (21-22 dalla 6d89137e, 20 triangolando con la frontale) e leggermente
  inclinato (sporge 22,5 cm in alto, 20 in basso), bocca d'aria fino a 28,5 cm sotto il bordo alto, centrato 1,5 cm a sinistra della porta (z = 2,975: le foto danno 2,95-2,98).
  Non tornano fra loro (+-3 cm) la profondita' (22,5 nominale, 18-32 cm dalle foto) e l'altezza del cappuccio (21-24 cm): la forma e' una media delle misure, verificata a occhio sulle due foto registrate.
Il muro sotto resta pulito: `wall_rects()` rifa' per diffusione la zona dove c'era l'ombra cotta e le strisce di luce delle foto, `shadow()` aggiunge l'ombra morbida dell'apparecchio."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh, hex2rgb, shade

ASSETS = os.environ.get('AC_ASSETS', '/tmp/claude-0/s/st3/assets/ac')
GAIN = (0.958, 0.920, 0.873)               # stessa foto e stessa luce della porta interna (door_obj A): foto -> intonaco cotto nel pacchetto
W = 0.75                                   # larghezza
Y_TOP = 2.727                              # bordo alto
U_C = 1.525                                # centro (u = 4,5 - z; z = 2,975)
D_TOP = 0.225                              # sporgenza del bordo alto del cappuccio
HOOD = (0.208, 0.200)                      # cappuccio: (altezza in verticale, sporgenza del bordo basso)
CHIN_TOP = (0.208, 0.188)                  # bocca d'aria: spigolo alto (Y sotto il bordo alto, sporgenza dal muro), 1,2 cm piu' in dentro del cappuccio
CHIN_BOT = (0.285, 0.112)                  # spigolo basso
CHIN_INSET = (0.006, 0.045)                # restringimento di ciascun lato in alto e in basso (angoli smussati)
PPM = 1350                                 # px/m della texture
SEG = (10, 3)                              # suddivisione del fronte della bocca d'aria (la texture e' bilineare sul trapezio)
PLASTIC = (206, 205, 197)                  # bianco della plastica nella foto (prima del guadagno): solo per fianchi, sopra e sotto

def corner_room(X, Y, d):
    """punto del fronte: X verso destra guardando dalla stanza (dal bordo sinistro), Y in basso dal bordo alto, d = sporgenza dal muro -> sistema stanza"""
    return np.array([d, Y_TOP - Y, 4.5 - (U_C - W / 2 + X)])

def hood_quad():
    """angoli del cappuccio (X, Y, d): alto-sx, alto-dx, basso-dx, basso-sx"""
    return [(0.0, 0.0, D_TOP), (W, 0.0, D_TOP), (W, HOOD[0], HOOD[1]), (0.0, HOOD[0], HOOD[1])]

def chin_quad():
    """angoli del fronte della bocca d'aria (X, Y, d): alto-sx, alto-dx, basso-dx, basso-sx"""
    it, ib = CHIN_INSET
    return [(it, CHIN_TOP[0], CHIN_TOP[1]), (W - it, CHIN_TOP[0], CHIN_TOP[1]), (W - ib, CHIN_BOT[0], CHIN_BOT[1]), (ib, CHIN_BOT[0], CHIN_BOT[1])]

def tex_size():
    """larghezza, altezza del cappuccio e altezza del fronte della bocca d'aria nella texture (px)"""
    q = hood_quad(); hh = int(round(np.linalg.norm(np.array(q[3]) - np.array(q[0])) * PPM))
    q = chin_quad(); ch = int(round(np.linalg.norm((np.array(q[3]) - np.array(q[0]))) * PPM))
    return int(round(W * PPM)), hh, ch

def wall_rects():
    """fascia (u0, u1, y0, y1, morbido) della parete A da rifare: lo split cotto con la sua ombra e le strisce di luce attorno (la cornice resta)"""
    return [(U_C - W / 2 - 0.16, U_C + W / 2 + 0.16, Y_TOP - CHIN_BOT[0] - 0.14, 2.88, True)]

def shadow(img, ppm, H=3.0, strength=0.085):
    """ombra morbida sul muro (luce dall'alto a destra: cade in basso a sinistra): scurisce il muro attorno all'apparecchio; img = texture della parete A (BGR uint8), u verso destra, riga 0 = alto"""
    h, w = img.shape[:2]; m = np.zeros((h, w), np.float32)
    u0, u1 = U_C - W / 2, U_C + W / 2; y0, y1 = Y_TOP - CHIN_BOT[0], Y_TOP
    m[int((H - y1 - 0.01) * ppm):int((H - y0 + 0.02) * ppm), int((u0 - 0.04) * ppm):int((u1 + 0.02) * ppm)] = 1.0
    m = cv2.GaussianBlur(m, (0, 0), 0.045 * ppm)
    return np.clip(img.astype(np.float32) * (1.0 - strength * m)[..., None], 0, 255).astype(np.uint8)

def jpg(img, q=90):
    ok, b = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q]); assert ok; return b.tobytes()

def plastic(atlas_bgr, hh):
    """bianco medio del cappuccio nella texture (RGB, dopo il guadagno): serve ai lati, sopra e sotto"""
    c = atlas_bgr[int(hh * 0.1):int(hh * 0.6), int(atlas_bgr.shape[1] * 0.1):int(atlas_bgr.shape[1] * 0.9)].reshape(-1, 3).mean(0)
    return c[::-1]

def build():
    """parti: lista di dict(name, mesh, map, wall) e immagini jpeg"""
    wpx, hh, ch = tex_size(); gap = 4; H_ATLAS = hh + gap + ch
    atlas = cv2.imread(f'{ASSETS}/ac_t.png')
    assert atlas is not None and atlas.shape[:2] == (H_ATLAS, wpx), (None if atlas is None else atlas.shape, (H_ATLAS, wpx))
    g = np.array(GAIN[::-1], np.float32)[None, None, :]
    atlas = np.clip(atlas.astype(np.float32) * g, 0, 255).astype(np.uint8)
    imgs = {'ac_t': jpg(atlas, 90)}
    white = (255, 255, 255); mt = Mesh()
    # cappuccio: una faccia sola (in alto nella texture)
    top_v, bot_v = 1.0, 1.0 - hh / H_ATLAS
    mt._add([corner_room(*p) for p in hood_quad()], [white] * 4, [(0, 1, 2), (0, 2, 3)], [(0, top_v), (1, top_v), (1, bot_v), (0, bot_v)])
    # fronte della bocca d'aria: griglia (SEG) con la stessa parametrizzazione bilineare della texture
    cq = chin_quad(); nx, ny = SEG; v_top, v_bot = ch / H_ATLAS, 0.0; base = len(mt.P)
    for j in range(ny + 1):
        t = j / ny
        for i in range(nx + 1):
            s_ = i / nx
            a_ = np.array(cq[0]) * (1 - s_) + np.array(cq[1]) * s_; b_ = np.array(cq[3]) * (1 - s_) + np.array(cq[2]) * s_
            mt._add([corner_room(*(a_ * (1 - t) + b_ * t))], [white], [], [(s_, v_top - t * (v_top - v_bot))])
    for j in range(ny):
        for i in range(nx):
            a_ = base + j * (nx + 1) + i; b_ = a_ + 1; c_ = a_ + (nx + 1) + 1; d_ = a_ + (nx + 1)
            mt.I += [(a_, b_, c_), (a_, c_, d_)]
    # corpo in colore pieno: sopra, fianchi (poligono del profilo), sotto, bordino sotto il cappuccio
    P = plastic(atlas, hh) * 1.0; mb = Mesh(); ref = (D_TOP * 0.5, Y_TOP - 0.15, 4.5 - U_C)
    y_h = Y_TOP - HOOD[0]; y_c = Y_TOP - CHIN_TOP[0]; y_b = Y_TOP - CHIN_BOT[0]
    zl, zr = 4.5 - (U_C - W / 2), 4.5 - (U_C + W / 2)                      # z del lato sinistro (visto da dentro) e del destro
    mb.quad(*[(0.0, Y_TOP, zl), (D_TOP, Y_TOP, zl), (D_TOP, Y_TOP, zr), (0.0, Y_TOP, zr)], P * 0.98, ref=ref)                                # sopra
    prof = [(0.0, Y_TOP), (D_TOP, Y_TOP), (HOOD[1], y_h), (CHIN_TOP[1], y_c), (CHIN_BOT[1], y_b), (0.0, y_b + 0.025)]
    cen = np.mean(prof, 0)
    for z in (zl, zr):
        zin = np.sign(0.5 * (zl + zr) - z)                                  # verso l'interno
        for k in range(len(prof)):
            a_, b_ = prof[k], prof[(k + 1) % len(prof)]
            mb.tri((a_[0], a_[1], z), (b_[0], b_[1], z), (cen[0], cen[1], z), np.minimum(P * 1.14, 252), ref=(cen[0], cen[1], z + zin * 0.1))
    mb.quad(*[(0.0, y_b + 0.025, zl), (CHIN_BOT[1], y_b, zl), (CHIN_BOT[1], y_b, zr), (0.0, y_b + 0.025, zr)], P * 0.92, ref=ref, two=True)   # sotto
    mb.quad(*[(CHIN_TOP[1], y_h, zl), (HOOD[1], y_h, zl), (HOOD[1], y_h, zr), (CHIN_TOP[1], y_h, zr)], P * 0.80, ref=ref, two=True)           # bordino sotto il cappuccio
    return [dict(name='ac_front', mesh=mt, map='ac_t', wall='A'), dict(name='ac_body', mesh=mb, map=None, wall='A')], imgs

if __name__ == '__main__':
    print(tex_size(), wall_rects())
    parts, imgs = build(); print([(p['name'], len(p['mesh'].P)) for p in parts], {k: len(v) for k, v in imgs.items()})
