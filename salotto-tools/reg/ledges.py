"""Le due mensole portaquadri nere sulla parete TV e i sei quadretti incorniciati (poster horror) appoggiati sopra.
Mensole: asse nera con un bordo anteriore rialzato; quadretti: cornice nera, passepartout e stampa in un'unica texture rettificata dalla foto (atlante 3x2), inclinati all'indietro contro il muro.
Coordinate del sistema stanza: x lungo la parete TV (u), y su, z verso la stanza (la parete TV e' z = 0)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh

ASSETS = os.environ.get('CONSOLE_ASSETS', '')
Y_TOP = 1.967                       # piano delle mensole
LEDGES = [(4.75, 5.73), (6.03, 7.09)]
DEPTH = 0.115
POSTERS = [('shining', 4.925), ('exorcist', 5.24), ('clockwork', 5.57), ('thing', 6.17), ('jaws', 6.495), ('evildead', 6.83)]
MAT_W, MAT_H, BORDER, FDEPTH = 0.216, 0.294, 0.012, 0.020
LEAN = np.radians(8.0)

def jpg(img, q=88):
    ok, b = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q, cv2.IMWRITE_JPEG_OPTIMIZE, 1]); assert ok; return b.tobytes()

def build(y_top=Y_TOP, lean=LEAN):
    """ritorna (parti, immagini): mensole+cornici a colori per vertice e quadretti con texture (atlante)"""
    parts = []; imgs = {}
    solid = Mesh(); tex = Mesh()
    # mensole: asse (spessore 2,2 cm) + bordo anteriore rialzato
    top = (40, 40, 44); side = (26, 26, 29); lip = (48, 48, 53)
    for (u0, u1) in LEDGES:
        solid.box((u0, y_top - 0.022, 0.0), (u1, y_top, DEPTH), {'+y': top, '-y': (14, 14, 16), '+z': side, '-x': side, '+x': side, '-z': side})
        solid.box((u0, y_top, DEPTH - 0.012), (u1, y_top + 0.014, DEPTH), {'+y': lip, '+z': (34, 34, 38), '-x': side, '+x': side, '-z': (20, 20, 22)})
    # quadretti
    tw, th = 270, 368
    atlas = np.zeros((th * 2, tw * 3, 3), np.uint8)
    Wt, Ht = MAT_W + 2 * BORDER, MAT_H + 2 * BORDER
    d = FDEPTH; ca, sa = np.cos(lean), np.sin(lean)
    for i, (name, u) in enumerate(POSTERS):
        im = cv2.imread(f'{ASSETS}/poster_{name}.png'); im = cv2.resize(im, (tw, th), interpolation=cv2.INTER_AREA)
        r, c = divmod(i, 3); atlas[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = im
        # il bordo posteriore basso del quadretto poggia sulla mensola, un po' dietro al bordo rialzato
        z_b = 0.042
        def W3(lx, ly, lz):          # locale (x, su, avanti) -> stanza; il quadretto e' inclinato all'indietro attorno al bordo posteriore basso
            return np.array([u + lx, y_top + ly * ca + (lz + d) * sa, z_b + (lz + d) * ca - ly * sa])
        # cornice nera: facce (davanti con il passepartout al centro)
        black = (22, 22, 24); inner = (30, 30, 33)
        x0, x1 = -Wt / 2, Wt / 2
        # lato superiore, inferiore, sinistro, destro (spessore d)
        for (a, b, cc, dd, col) in [((x0, Ht, -d), (x1, Ht, -d), (x1, Ht, 0), (x0, Ht, 0), black),          # superiore
                                    ((x0, 0, -d), (x1, 0, -d), (x1, 0, 0), (x0, 0, 0), black),               # inferiore
                                    ((x0, 0, -d), (x0, Ht, -d), (x0, Ht, 0), (x0, 0, 0), black),             # sinistro
                                    ((x1, 0, -d), (x1, Ht, -d), (x1, Ht, 0), (x1, 0, 0), black)]:            # destro
            solid.quad(W3(*a), W3(*b), W3(*cc), W3(*dd), col, two=True, k=1.0)
        # retro
        solid.quad(W3(x0, 0, -d), W3(x1, 0, -d), W3(x1, Ht, -d), W3(x0, Ht, -d), (18, 18, 20), two=True)
        # davanti: cornice (4 strisce) e stampa
        m0, m1 = -MAT_W / 2, MAT_W / 2; y0_, y1_ = BORDER, BORDER + MAT_H
        for (a, b, cc, dd) in [((x0, 0, 0), (x1, 0, 0), (x1, BORDER, 0), (x0, BORDER, 0)), ((x0, y1_, 0), (x1, y1_, 0), (x1, Ht, 0), (x0, Ht, 0)),
                               ((x0, BORDER, 0), (m0, BORDER, 0), (m0, y1_, 0), (x0, y1_, 0)), ((m1, BORDER, 0), (x1, BORDER, 0), (x1, y1_, 0), (m1, y1_, 0))]:
            solid.quad(W3(*a), W3(*b), W3(*cc), W3(*dd), (26, 26, 29), two=True)
        uv0 = (c * tw / (tw * 3), 1 - (r + 1) * th / (th * 2)); uv1 = ((c + 1) * tw / (tw * 3), 1 - r * th / (th * 2))
        P = [W3(m0, y0_, 0.0005), W3(m1, y0_, 0.0005), W3(m1, y1_, 0.0005), W3(m0, y1_, 0.0005)]
        tex._add(P, [(255, 255, 255)] * 4, [(0, 1, 2), (0, 2, 3)], [(uv0[0], uv0[1]), (uv1[0], uv0[1]), (uv1[0], uv1[1]), (uv0[0], uv1[1])])
    imgs['cobj_posters'] = jpg(atlas, 88)
    parts.append(dict(name='ledges', mesh=solid, map=None)); parts.append(dict(name='posters', mesh=tex, map='cobj_posters'))
    return parts, imgs
