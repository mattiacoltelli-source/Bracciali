"""Piccoli oggetti a muro in 3D (parete A, x = 0, sporgono verso +x): placca a tre moduli con interruttore a tre tasti e con presa bipasso.
Posizione e misure dagli angoli letti in due foto registrate (3039c671, 6d89137e) e intersecati col piano della parete: concordano entro 4 mm.
Colori a vertice (come gli altri oggetti): la cornice e' antracite smussata, i tasti e la presa grigio chiaro."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from meshlib import Mesh, rot_x

PLATE_W, PLATE_H = 0.117, 0.082                 # placca a 3 moduli
SWITCH = dict(zc=2.3675, yc=1.2350)              # centro dell'interruttore sulla parete A (z, y)
OUTLET = dict(zc=2.3855, yc=0.3840)              # centro della presa (stessa colonna, in basso)
H_RIM, H_TOP, H_WIN = 0.0045, 0.0100, 0.0070     # sporgenza: bordo esterno, spigolo interno della cornice, fondo della finestra
WIN_W, WIN_H = 0.0715, 0.0420                    # finestra della cornice
FRAME = (62, 62, 66)

def _plate_gen(mesh, P, W, Hh, win_w, win_h, h_rim=H_RIM, h_top=H_TOP, h_win=H_WIN):
    """placca smussata con finestra centrale; P(a, b, h) -> punto del mondo (a: orizzontale, b: verticale, h: sporgenza dalla parete)"""
    ref = P(0, 0, 0.001)
    hw, hh = W / 2, Hh / 2
    out = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    ww, wh = win_w / 2, win_h / 2
    inn = [(-ww, -wh), (ww, -wh), (ww, wh), (-ww, wh)]
    for i in range(4):
        j = (i + 1) % 4
        mesh.quad(P(*out[i], 0.0), P(*out[j], 0.0), P(*out[j], h_rim), P(*out[i], h_rim), FRAME, ref=ref, k=1.0)                  # bordo verticale
        mesh.quad(P(*out[i], h_rim), P(*out[j], h_rim), P(*inn[j], h_top), P(*inn[i], h_top), FRAME, ref=ref, k=1.12)              # smusso verso la finestra
        mesh.quad(P(*inn[i], h_top), P(*inn[j], h_top), P(*inn[j], h_win), P(*inn[i], h_win), (30, 30, 33), two=True, k=1.0)       # fianchi della finestra
    return P

def _plate(mesh, zc, yc, x0=0.0):
    def P(dz, dy, h): return np.array([x0 + h, yc + dy, zc + dz])
    return _plate_gen(mesh, P, PLATE_W, PLATE_H, WIN_W, WIN_H)

def switch(mesh, zc=None, yc=None):
    """placca con tre tasti larghi (interruttore a tre moduli)"""
    zc = SWITCH['zc'] if zc is None else zc; yc = SWITCH['yc'] if yc is None else yc
    P = _plate(mesh, zc, yc)
    ww, wh = WIN_W / 2, WIN_H / 2; gap = 0.0012; kw = (WIN_W - 2 * gap) / 3
    top = H_TOP - 0.0012
    for i in range(3):
        a = -ww + i * (kw + gap); b = a + kw
        mesh.quad(P(a, -wh, top), P(b, -wh, top), P(b, wh, top), P(a, wh, top), (214, 212, 204), two=True, k=1.0)                  # faccia del tasto
        mesh.quad(P(a, -wh, top), P(a, wh, top), P(a, wh, H_WIN), P(a, -wh, H_WIN), (60, 60, 62), two=True, k=1.0)                    # fianco (ombra fra i tasti)
        mesh.quad(P(b, -wh, top), P(b, wh, top), P(b, wh, H_WIN), P(b, -wh, H_WIN), (60, 60, 62), two=True, k=1.0)
    mesh.quad(P(-ww, -wh, H_WIN + 0.0005), P(ww, -wh, H_WIN + 0.0005), P(ww, wh, H_WIN + 0.0005), P(-ww, wh, H_WIN + 0.0005), (44, 44, 46), two=True, k=1.0)      # fondo visibile fra i tasti

def outlet(mesh, zc=None, yc=None):
    """placca con una presa bipasso: blocco chiaro con tre fori in fila verticale"""
    zc = OUTLET['zc'] if zc is None else zc; yc = OUTLET['yc'] if yc is None else yc
    P = _plate(mesh, zc, yc)
    ww, wh = WIN_W / 2, WIN_H / 2; top = H_TOP - 0.0018
    mesh.quad(P(-ww, -wh, top), P(ww, -wh, top), P(ww, wh, top), P(-ww, wh, top), (208, 206, 198), two=True, k=1.0)
    for dz in (-0.0185, 0.0, 0.0185):          # fori: ai lati i due poli, al centro la terra
        for q in range(8):
            a0, a1 = 2 * np.pi * q / 8, 2 * np.pi * (q + 1) / 8; r = 0.0035 if dz == 0.0 else 0.0032
            mesh._add([P(dz, 0, top + 0.0003), P(dz + r * np.cos(a0), r * np.sin(a0), top + 0.0003), P(dz + r * np.cos(a1), r * np.sin(a1), top + 0.0003)], [(36, 36, 38)] * 3, [(0, 1, 2)])

# ---------------------------------------------------------------- parete ingresso (F, z = 4,5): applique, citofono, cornetta e placca nera
Z_FW = 4.5                                       # le cose sporgono verso -z
SCONCES = [dict(x=2.206, y0=1.567, y1=2.226, yc=2.042), dict(x=2.060, y0=1.564, y1=2.230, yc=1.743)]      # asta (da y0 a y1) e posizione del cilindro lungo l'asta; dai raggi di tre foto registrate (79eb58fc, 6eac1b0f, 8a00d20d)
ROD_R, DISC_R, DISC_L = 0.0058, 0.028, 0.050
INTERCOM = dict(x0=1.826, x1=1.919, y0=1.397, y1=1.576)
HANDSET = dict(x0=1.666, x1=1.749, y0=1.372, y1=1.603)
PLATE4 = dict(x0=1.666, x1=1.869, y0=1.159, y1=1.251)

def FP(x, y, h): return np.array([x, y, Z_FW - h])
def _solid(col): return {f: col for f in ('+x', '-x', '+y', '-y', '+z', '-z')}

def sconces(mesh):
    """due applique nere: cilindro (end cap grigio scuro) contro il muro e asta sottile fissata al suo centro, con i piccoli tappi alle estremita'"""
    side = '#1c1c1e'; cap = '#4a4a4f'; rod = '#202022'
    R = rot_x(-np.pi / 2)                                      # l'asse locale y (verso l'alto) diventa -z: il cilindro esce dalla parete
    for sc in SCONCES:
        mesh.lathe((sc['x'], sc['yc'], Z_FW), [(DISC_R, 0.0, side), (DISC_R, DISC_L - 0.003, side), (DISC_R * 0.96, DISC_L, cap)], seg=28, rot=R, caps=True, k=1.0)
        zr = Z_FW - DISC_L - ROD_R                              # asta davanti al cilindro
        L = sc['y1'] - sc['y0']; cr = ROD_R * 1.18
        mesh.lathe((sc['x'], sc['y0'], zr), [(cr, 0.0, rod), (cr, 0.010, rod), (ROD_R, 0.012, rod), (ROD_R, L - 0.012, rod), (cr, L - 0.010, rod), (cr, L, rod)], seg=12, caps=True, k=1.0)

def intercom(mesh):
    """pannello bianco del citofono (parte alta in tessuto grigio, quattro simboli, tasto in basso) e cornetta bianca col cavo a spirale"""
    c = INTERCOM; d = 0.026; white = (234, 232, 224); side = (206, 204, 196)
    mesh.box((c['x0'], c['y0'], Z_FW - d), (c['x1'], c['y1'], Z_FW), dict([('-z', white), ('+x', side), ('-x', side), ('+y', side), ('-y', side)]), k=1.4)
    ys = c['y1'] - 0.042
    mesh.quad(FP(c['x0'] + 0.004, ys, d + 0.0008), FP(c['x1'] - 0.004, ys, d + 0.0008), FP(c['x1'] - 0.004, c['y1'] - 0.004, d + 0.0008), FP(c['x0'] + 0.004, c['y1'] - 0.004, d + 0.0008), (150, 138, 126), two=True, k=1.0)     # altoparlante in tessuto
    xm = (c['x0'] + c['x1']) / 2
    for i in range(4):                                                                              # i quattro simboli
        xi = c['x1'] - 0.014 - i * 0.021; mesh.quad(FP(xi - 0.004, ys - 0.020, d + 0.0008), FP(xi + 0.004, ys - 0.020, d + 0.0008), FP(xi + 0.004, ys - 0.012, d + 0.0008), FP(xi - 0.004, ys - 0.012, d + 0.0008), (60, 60, 66), two=True, k=1.0)
    mesh.quad(FP(xm - 0.009, c['y0'] + 0.038, d + 0.0008), FP(xm + 0.009, c['y0'] + 0.038, d + 0.0008), FP(xm + 0.009, c['y0'] + 0.034, d + 0.0008), FP(xm - 0.009, c['y0'] + 0.034, d + 0.0008), (70, 70, 78), two=True, k=1.0)           # tasto/spia
    h = HANDSET; xc = (h['x0'] + h['x1']) / 2; cream = (230, 228, 218)
    mesh.box((h['x0'] - 0.004, h['y0'] - 0.004, Z_FW - 0.012), (h['x1'] + 0.004, h['y1'] + 0.004, Z_FW), dict([('-z', (222, 220, 210)), ('+x', side), ('-x', side), ('+y', side), ('-y', side)]), k=1.4)      # base
    gw = 0.020; ty = 0.075
    mesh.box((h['x0'] + 0.003, h['y1'] - ty, Z_FW - 0.040), (h['x1'] - 0.003, h['y1'] - 0.004, Z_FW - 0.012), _solid(cream), k=1.4)                    # padiglione dell'auricolare
    mesh.box((h['x0'] + 0.003, h['y0'] + 0.004, Z_FW - 0.040), (h['x1'] - 0.003, h['y0'] + ty, Z_FW - 0.012), _solid(cream), k=1.4)                    # microfono
    mesh.box((xc - gw, h['y0'] + ty, Z_FW - 0.034), (xc + gw, h['y1'] - ty, Z_FW - 0.012), _solid(cream), k=1.4)                                       # impugnatura
    # cavo a spirale che pende dal fondo della cornetta, con l'asola finale
    pts = []; N = 150; y_top = h['y0'] + 0.004
    for i in range(N + 1):
        t = i / N; a = t * 2 * np.pi * 9.5; pts.append((xc + 0.0075 * np.sin(a) - 0.004 * t, y_top - 0.16 * t, Z_FW - 0.026 - 0.0075 * np.cos(a)))
    from console_obj import tube
    tube(mesh, pts, 0.0022, (232, 228, 214), seg=6, k=1.0)

def plate4(mesh):
    """placca nera con quattro tasti chiari sotto il citofono"""
    p = PLATE4; xc = (p['x0'] + p['x1']) / 2; yc = (p['y0'] + p['y1']) / 2; W = p['x1'] - p['x0']; Hh = p['y1'] - p['y0']
    def P(a, b, h): return np.array([xc - a, yc + b, Z_FW - h])           # a cresce verso destra guardando la parete dalla stanza
    ww, wh = 0.150, 0.056
    _plate_gen(mesh, P, W, Hh, ww, wh)
    gap = 0.0012; kw = (ww - 3 * gap) / 4; top = H_TOP - 0.0012
    for i in range(4):
        a0 = -ww / 2 + i * (kw + gap); a1 = a0 + kw
        mesh.quad(P(a0, -wh / 2, top), P(a1, -wh / 2, top), P(a1, wh / 2, top), P(a0, wh / 2, top), (214, 212, 204), two=True, k=1.0)
        mesh.quad(P(a0, -wh / 2, top), P(a0, wh / 2, top), P(a0, wh / 2, H_WIN), P(a0, -wh / 2, H_WIN), (60, 60, 62), two=True, k=1.0)
        mesh.quad(P(a1, -wh / 2, top), P(a1, wh / 2, top), P(a1, wh / 2, H_WIN), P(a1, -wh / 2, H_WIN), (60, 60, 62), two=True, k=1.0)
    mesh.quad(P(-ww / 2, -wh / 2, H_WIN + 0.0005), P(ww / 2, -wh / 2, H_WIN + 0.0005), P(ww / 2, wh / 2, H_WIN + 0.0005), P(-ww / 2, wh / 2, H_WIN + 0.0005), (44, 44, 46), two=True, k=1.0)

def wall_rects_F(wall_len=7.1, margin=0.04):
    """fasce (u0, u1, y0, y1, morbido) della parete F (u = lunghezza - x) da rifare per diffusione: applique con il loro alone, citofono, cornetta e placca; il portone comincia a x = 1,63"""
    out = []
    for (x0, x1, y0, y1) in ((1.645, 2.50, 1.30, 2.40), (1.645, 1.96, 1.02, 1.70)):          # il primo arriva fino al portone: a destra delle applique restava un blocco d'alone caldo con il bordo netto
        out.append((wall_len - x1, wall_len - x0, y0, y1, True))
    return out

def build():
    m = Mesh(); switch(m); outlet(m); sconces(m); intercom(m); plate4(m)
    return [dict(name='wallobj', mesh=m, map=None)], {}

def wall_rects(wall_len=4.5, margin=0.045):
    """rettangoli (u0, u1, y0, y1, morbido) sulla parete A (u = lunghezza - z) da rifare per diffusione nella texture della parete, attorno a interruttore e presa"""
    out = []
    for o in (SWITCH, OUTLET):
        z0, z1 = o['zc'] - PLATE_W / 2 - margin, o['zc'] + PLATE_W / 2 + margin
        out.append((wall_len - z1, wall_len - z0, o['yc'] - PLATE_H / 2 - margin, o['yc'] + PLATE_H / 2 + margin, False))
    return out
