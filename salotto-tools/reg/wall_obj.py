"""Piccoli oggetti a muro in 3D (parete A, x = 0, sporgono verso +x): placca a tre moduli con interruttore a tre tasti e con presa bipasso.
Posizione e misure dagli angoli letti in due foto registrate (3039c671, 6d89137e) e intersecati col piano della parete: concordano entro 4 mm.
Colori a vertice (come gli altri oggetti): la cornice e' antracite smussata, i tasti e la presa grigio chiaro."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from meshlib import Mesh

PLATE_W, PLATE_H = 0.117, 0.082                 # placca a 3 moduli
SWITCH = dict(zc=2.3675, yc=1.2350)              # centro dell'interruttore sulla parete A (z, y)
OUTLET = dict(zc=2.3855, yc=0.3840)              # centro della presa (stessa colonna, in basso)
H_RIM, H_TOP, H_WIN = 0.0045, 0.0100, 0.0070     # sporgenza: bordo esterno, spigolo interno della cornice, fondo della finestra
WIN_W, WIN_H = 0.0715, 0.0420                    # finestra della cornice
FRAME = (62, 62, 66)

def _plate(mesh, zc, yc, x0=0.0):
    def P(dz, dy, h): return np.array([x0 + h, yc + dy, zc + dz])
    ref = P(0, 0, 0.001)
    hw, hh = PLATE_W / 2, PLATE_H / 2
    out = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    ww, wh = WIN_W / 2, WIN_H / 2
    inn = [(-ww, -wh), (ww, -wh), (ww, wh), (-ww, wh)]
    for i in range(4):
        j = (i + 1) % 4
        mesh.quad(P(*out[i], 0.0), P(*out[j], 0.0), P(*out[j], H_RIM), P(*out[i], H_RIM), FRAME, ref=ref, k=1.0)                  # bordo verticale
        mesh.quad(P(*out[i], H_RIM), P(*out[j], H_RIM), P(*inn[j], H_TOP), P(*inn[i], H_TOP), FRAME, ref=ref, k=1.12)              # smusso verso la finestra
        mesh.quad(P(*inn[i], H_TOP), P(*inn[j], H_TOP), P(*inn[j], H_WIN), P(*inn[i], H_WIN), (30, 30, 33), two=True, k=1.0)       # fianchi della finestra
    return P

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

def build():
    m = Mesh(); switch(m); outlet(m)
    return [dict(name='wallobj', mesh=m, map=None)], {}

def wall_rects(wall_len=4.5, margin=0.045):
    """rettangoli (u0, u1, y0, y1, morbido) sulla parete A (u = lunghezza - z) da rifare per diffusione nella texture della parete, attorno a interruttore e presa"""
    out = []
    for o in (SWITCH, OUTLET):
        z0, z1 = o['zc'] - PLATE_W / 2 - margin, o['zc'] + PLATE_W / 2 + margin
        out.append((wall_len - z1, wall_len - z0, o['yc'] - PLATE_H / 2 - margin, o['yc'] + PLATE_H / 2 + margin, False))
    return out
