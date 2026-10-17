"""Nicchia del termosifone sotto la finestra (parete W), termosifone in ghisa a 13 elementi, base e robot aspirapolvere: tutto in 3D.
Prima stavano cotti nelle texture: il termosifone nel muro (sfocato e sdoppiato, 5-7 m e pose diverse) e il robot con la base nel pavimento e nel muro (macchia scura). Ora:
- la nicchia e' un buco nel muro (manifesto `holes`, stessa larghezza dell'apertura della finestra: z 0,726-1,630, dal pavimento a y = 0,86: fra la nicchia e la finestra restano 6 cm d'intonaco, il davanzale) con fondo e fianchi d'intonaco profondi 10 cm;
- il termosifone sta dentro la nicchia, a filo del muro: 13 elementi (passo 6,1 cm, z 0,80-1,58, y 0,10-0,78; misure dal muro cotto, dove sbava ma in metri veri, e dal rapporto con la nicchia nella foto frontale),
  ciascuno con la nervatura centrale in rilievo, testata e piede piu' larghi; dietro la lamiera forata grigia e l'ombra; la valvola a sinistra e la testa termostatica bianca a destra;
- la base del robot (nera, 20 x 28 x 36 cm, logo arancione e spia) e il robot (disco di 34 cm, torretta del laser, vetro) sono sul pavimento, contro il muro, davanti all'estremita' destra del termosifone;
  il pacchetto ne fa un ostacolo per la camminata (`scene_def`: `ostacolo_robot`), e le zone cotte nel pavimento e nel muro (`floor_excl`, `wall_rects`) si rifanno per diffusione.
Le misure si leggono dalle tre foto dell'utente (frontale e due oblique, non registrate): non hanno una posa, quindi le quote sono stime a +-3 cm."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from meshlib import Mesh

X_WALL = 7.10
NICHE = dict(z0=0.726, z1=1.630, y0=0.0, y1=0.90, d=0.10)
RAD = dict(z0=0.788, z1=1.568, y0=0.09, y1=0.75, n=13, el_w=0.054, depth=0.085, gap_x=0.012)       # centrato nella nicchia (foto frontale)
DOCK = dict(zc=1.41, w=0.17, d=0.25, h=0.30, x_back=X_WALL - 0.02)
ROBOT = dict(zc=1.45, xc=6.69, r=0.16, h=0.092)
PLASTER = (205, 204, 200)

def holes():
    """per il manifesto: buco della nicchia nella parete W (u0, u1, y0, y1; u = z)"""
    return {'W': [[NICHE['z0'], NICHE['z1'], NICHE['y0'], NICHE['y1']]]}

def wall_rects():
    """fasce della parete W da rifare per diffusione: attorno alla nicchia (il termosifone sbavava di qualche cm oltre i bordi) e la macchia della base del robot (sale fino a ~0,45 m)"""
    n = NICHE
    return [(n['z0'] - 0.17, n['z1'] + 0.30, 0.0, n['y1'] + 0.13, True)]

def floor_excl():
    """rettangoli (x0, x1, z0, z1) del pavimento da rifare: base e robot, con 3 cm di margine"""
    d, r = DOCK, ROBOT
    return [(d['x_back'] - d['d'] - 0.03, X_WALL, d['zc'] - d['w'] / 2 - 0.03, d['zc'] + d['w'] / 2 + 0.03),
            (r['xc'] - r['r'] - 0.03, r['xc'] + r['r'] + 0.03, r['zc'] - r['r'] - 0.03, r['zc'] + r['r'] + 0.03)]

def _niche(m):
    n = NICHE; xw = X_WALL; xb = X_WALL + n['d']; z0, z1, y0, y1 = n['z0'], n['z1'], n['y0'], n['y1']
    P = np.array(PLASTER, float); ref = (xw - 0.5, 0.45, (z0 + z1) / 2)
    m.quad_grad([(xb, y0, z0), (xb, y0, z1), (xb, y1, z1), (xb, y1, z0)], [P * 0.74] * 4, ref=ref, two=True)                        # fondo (in ombra dietro il termosifone)
    m.quad_grad([(xw, y0, z0), (xb, y0, z0), (xb, y1, z0), (xw, y1, z0)], [P * 0.96, P * 0.80, P * 0.80, P * 0.96], ref=ref, two=True)   # fianco sinistro
    m.quad_grad([(xw, y0, z1), (xb, y0, z1), (xb, y1, z1), (xw, y1, z1)], [P * 0.96, P * 0.80, P * 0.80, P * 0.96], ref=ref, two=True)   # fianco destro
    m.quad_grad([(xw, y1, z0), (xb, y1, z0), (xb, y1, z1), (xw, y1, z1)], [P * 0.86, P * 0.66, P * 0.66, P * 0.86], ref=ref, two=True)   # sotto il davanzale
    m.quad_grad([(xw, y0 + 0.002, z0), (xb, y0 + 0.002, z0), (xb, y0 + 0.002, z1), (xw, y0 + 0.002, z1)], [(122, 114, 106)] * 4, ref=ref, two=True)  # pavimento della nicchia
    m.box((xb - 0.006, 0.0, z0), (xb, 0.07, z1), {'-x': (104, 78, 56), '+y': (138, 110, 84)})                                    # zoccolo in fondo

def _radiator(m):
    r = RAD; xf = X_WALL + r['gap_x']; xb = xf + r['depth']
    cream = (236, 232, 222); cream_d = (214, 209, 198); gray = (156, 156, 158); dark = (84, 80, 74)
    z0, z1, y0, y1, n, w = r['z0'], r['z1'], r['y0'], r['y1'], r['n'], r['el_w']; pitch = (z1 - z0 - w) / (n - 1)
    m.box((xb - 0.012, y0 - 0.005, z0 - 0.004), (xb - 0.006, y1 + 0.005, z1 + 0.004), {'-x': dark})                              # ombra dietro gli elementi
    m.box((xb - 0.030, y0, z0 - 0.002), (xb - 0.022, 0.36, z1 + 0.002), {'-x': gray, '+y': (176, 176, 178)})                      # lamiera forata dietro il piede
    yb0, yb1 = y0 + 0.06, y1 - 0.08                                                                                              # colonna fra piede e testata
    for i in range(n):
        zc = z0 + w / 2 + i * pitch
        # colonna: nervatura centrale in rilievo e due fianchi smussati piu' dietro
        m.box((xf, yb0, zc - 0.012), (xb, yb1, zc + 0.012), {'-x': cream, '+z': cream_d, '-z': cream_d})
        m.box((xf + 0.009, yb0, zc - w / 2), (xb, yb1, zc - 0.012), {'-x': cream_d, '-z': cream_d, '+z': cream_d})
        m.box((xf + 0.009, yb0, zc + 0.012), (xb, yb1, zc + w / 2), {'-x': cream_d, '-z': cream_d, '+z': cream_d})
        # testata (sopra) e piede (sotto): piu' larghi della colonna
        m.box((xf, y1 - 0.08, zc - 0.029), (xb, y1 - 0.04, zc + 0.029), {'-x': cream, '+y': cream, '+z': cream_d, '-z': cream_d})
        m.box((xf + 0.008, y1 - 0.04, zc - 0.024), (xb - 0.008, y1, zc + 0.024), {'-x': cream, '+y': (246, 243, 236), '+z': cream_d, '-z': cream_d})
        m.box((xf - 0.0012, y1 - 0.073, zc - 0.009), (xf, y1 - 0.047, zc + 0.009), {'-x': (58, 54, 50)})                                                      # apertura scura sulla testata (si vede nella foto)
        m.box((xf, y0, zc - 0.029), (xb, y0 + 0.06, zc + 0.029), {'-x': cream, '+y': cream_d, '+z': cream_d, '-z': cream_d})
    # valvola a sinistra (in basso) e testa termostatica bianca a destra
    m.box((xf + 0.01, y0 + 0.02, z0 - 0.045), (xf + 0.05, y0 + 0.07, z0 - 0.004), {'-x': (232, 230, 224), '+y': (244, 242, 238), '-z': (190, 188, 182), '+z': (200, 198, 192)})
    m.box((xf + 0.01, y0 + 0.02, z1 + 0.004), (xf + 0.05, y0 + 0.10, z1 + 0.05), {'-x': (246, 246, 243), '+y': (252, 252, 250), '+z': (210, 210, 206), '-z': (210, 210, 206)})

def _dock(m):
    d = DOCK; xb = d['x_back']; xf = xb - d['d']; zc = d['zc']; hw = d['w'] / 2; h = d['h']
    body = (26, 26, 29); side = (18, 18, 20); top = (46, 46, 50); front = (34, 34, 38)
    m.box((xf, 0.0, zc - hw), (xb, h - 0.03, zc + hw), {'-x': front, '+x': side, '+z': side, '-z': side, '+y': top})
    m.box((xf + 0.012, h - 0.03, zc - hw + 0.012), (xb - 0.004, h, zc + hw - 0.012), {'-x': body, '+z': side, '-z': side, '+y': top})      # parte alta, appena rientrata (spigoli smussati)
    m.box((xf + 0.02, h - 0.0005, zc - hw + 0.02), (xf + 0.05, h + 0.0015, zc - hw + 0.055), {'+y': (226, 142, 64)})                            # logo arancione, in alto a sinistra
    m.box((xf - 0.0015, 0.17, zc - 0.004), (xf, 0.176, zc + 0.004), {'-x': (240, 244, 255)})                                                    # spia bianca
    m.box((xf - 0.002, 0.02, zc - hw + 0.025), (xf, 0.15, zc + hw - 0.025), {'-x': (22, 22, 25)})                                              # pannello frontale (griglia scura)

def _robot(m):
    r = ROBOT; c = (r['xc'], 0.0, r['zc']); R = r['r']; H = r['h']
    body = (22, 22, 24); topc = (32, 32, 35); rim = (40, 40, 44)
    m.lathe(c, [(0.0, 0.004, body), (R - 0.004, 0.004, body), (R, 0.012, body), (R, H - 0.020, body), (R - 0.010, H - 0.006, topc), (R - 0.016, H, topc), (0.0, H, topc)], seg=40, caps=False)
    m.lathe(c, [(R - 0.004, 0.030, rim), (R, 0.034, rim), (R, 0.046, rim), (R - 0.004, 0.050, rim)], seg=40, caps=False)                           # fascia chiara del paraurti
    t = (r['xc'] + 0.012, H, r['zc'] + 0.012)                                                                                                  # torretta del laser, vicino al centro
    m.lathe(t, [(0.0, 0.0, (28, 28, 31)), (0.034, 0.0, (28, 28, 31)), (0.034, 0.026, (30, 30, 34)), (0.026, 0.032, (50, 50, 55)), (0.0, 0.032, (50, 50, 55))], seg=26, caps=False)
    m.box((r['xc'] - 0.095, H - 0.0005, r['zc'] - 0.085), (r['xc'] - 0.040, H + 0.0015, r['zc'] - 0.010), {'+y': (16, 16, 20)})                  # vetro scuro, in alto a sinistra
    m.box((r['xc'] - R - 0.002, 0.030, r['zc'] - 0.040), (r['xc'] - R + 0.006, 0.058, r['zc'] + 0.040), {'-x': (48, 50, 58)})               # sensore frontale

def build():
    """parti: lista di dict(name, mesh, map, wall); wall = parete a cui restano legate (nicchia e termosifone)"""
    mn, mr, md, mb = Mesh(), Mesh(), Mesh(), Mesh()
    _niche(mn); _radiator(mr); _dock(md); _robot(mb)
    return [dict(name='niche', mesh=mn, map=None, wall='W'), dict(name='radiator', mesh=mr, map=None, wall='W'), dict(name='robot_dock', mesh=md, map=None), dict(name='robot', mesh=mb, map=None)]

if __name__ == '__main__':
    print([(p['name'], len(p['mesh'].P)) for p in build()], holes(), wall_rects(), floor_excl())
