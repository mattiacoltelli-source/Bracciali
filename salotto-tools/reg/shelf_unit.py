"""Mobile a mensole accanto alla TV (sistema stanza nuovo): mensole in noce, base, pianta, brocca, vasetti, fumetti, vasi rossi.
Il fondo beige, il pilastro e il pannello scuro sono scatole in scene_def.py; qui ci sono le mesh a colori per vertice.
Misure da foto registrate (triangolazioni, sovrapposizioni, silhouette nella foto di fronte): mensole trapezoidali (lato sinistro in diagonale),
spessore 2,2 cm; scala nella foto di fronte (e8ef7d82) circa 836 px/m in orizzontale e 735 px/m in verticale."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from meshlib import Mesh, hex2rgb, rot_y, rot_x, rot_z, shade

U = dict(xL=3.54, zb=0.034, zf=0.24, xFL=3.63, xp=3.855, th=0.022, ys=dict(A=2.027, B=1.815, C=1.598, D=1.16), base=(0.945, 0.975))
WALNUT = dict(top='#7e4c2d', bot='#4b2d1c', front='#94603a', left='#8a5836')

def board_poly(U=U):
    return [(U['xL'], U['zb']), (U['xFL'], U['zf']), (U['xp'], U['zf']), (U['xp'], U['zb'])]

def add_boards(m, U=U):
    poly = board_poly(U)
    for n, yt in U['ys'].items():
        m.prism(poly, yt - U['th'], yt, WALNUT['top'], WALNUT['bot'], [WALNUT['left'], WALNUT['front'], WALNUT['left'], None])
    y0, y1 = U['base']
    m.prism(poly, y0, y1, '#7f796d', '#55504a', ['#8e887c', '#9a9487', '#8e887c', None])

LIGHT_V = np.array([0.35, 0.85, 0.40]); LIGHT_V /= np.linalg.norm(LIGHT_V)
def glossy(n):
    return 0.74 + 0.5 * max(0.0, float(np.asarray(n) @ LIGHT_V))

# ---------- vasetti e piante grasse ----------
def pot_faceted(m, c, r=0.034, h=0.048, k=1.0, seg=8, col='#efede7'):
    prof = [(r * 0.72, 0.0, col), (r * 0.93, h * 0.2, col), (r, h * 0.5, col), (r * 0.92, h * 0.82, col), (r * 0.80, h, col)]
    m.lathe(c, prof, seg=seg, smooth=False, caps=False, k=k, phase=np.pi / seg)
    m.lathe((c[0], c[1] + h * 0.96, c[2]), [(0.0, 0.0, '#2a261e'), (r * 0.76, 0.0, '#2a261e')], seg=seg, caps=False, k=1.0)

def succulent_rosette(m, c, rng, n=14, rl=0.05, rw=0.016, ang=(25, 60), cols=('#8e4256', '#d9808f', '#c5697c'), k=1.0):
    for i in range(n):
        th = 2 * np.pi * (i + rng.uniform(-0.25, 0.25)) / n
        el = np.radians(rng.uniform(*ang))
        d = np.array([np.sin(th) * np.cos(el), np.sin(el), np.cos(th) * np.cos(el)])
        L = rl * rng.uniform(0.8, 1.15)
        m.leaf(c, d, [0, 1, 0] if abs(d[1]) < 0.9 else [1, 0, 0], L, rw * rng.uniform(0.9, 1.15), cols[0], cols[1], cols[2], curl=0.12, k=k)

# ---------- vasi rossi ----------
def vase_round(m, c, k=1.0):
    P = [(0.000, 0.026), (0.012, 0.040), (0.029, 0.0545), (0.046, 0.059), (0.063, 0.0603), (0.080, 0.0585), (0.097, 0.053), (0.114, 0.042), (0.131, 0.024), (0.148, 0.0115), (0.165, 0.009), (0.178, 0.0105), (0.183, 0.0098)]
    prof = [(r, h, np.array(hex2rgb('#8f1119')) * (0.78 + 0.35 * np.sin(np.pi * min(1.0, h / 0.183 * 1.1)))) for h, r in P]
    prof.append((0.0075, 0.183, hex2rgb('#6a0b11')))
    m.lathe(c, prof, seg=28, smooth=True, caps=True, k=k, shade_fn=glossy)

def vase_tulip(m, c, k=1.0, phase=0.0):
    P = [(0.001, 0.031), (0.023, 0.032), (0.047, 0.035), (0.074, 0.036), (0.098, 0.035), (0.115, 0.033), (0.127, 0.032), (0.132, 0.035), (0.149, 0.044), (0.166, 0.051), (0.183, 0.057), (0.207, 0.063), (0.224, 0.0665)]
    prof = [(r, h, np.array(hex2rgb('#8f1119')) * (0.80 + 0.30 * np.sin(np.pi * min(1.0, h / 0.224 * 1.05)))) for h, r in P]
    prof.append((0.0640, 0.224, hex2rgb('#c63a40'))); prof.append((0.0610, 0.221, hex2rgb('#5a0a10'))); prof.append((0.0, 0.180, hex2rgb('#3d070b')))
    # il bordo e' un'ellisse (largo 13,3 cm nel verso x, circa 10,4 cm nell'altro) con un'incavatura davanti: due ali alte ai lati
    ell = lambda y: (1.0, 1.0 - 0.22 * np.clip((y - 0.127) / 0.097, 0, 1))
    dy = lambda th, y: -0.014 * np.cos(2 * th) * np.clip((y - 0.19) / 0.034, 0, 1)
    m.lathe(c, prof, seg=32, smooth=True, caps=True, k=k, phase=phase, shade_fn=glossy, ell=ell, dy_fn=dy)

# ---------- brocca siciliana ----------
def m_lathe_painted(m, c, P, col_fn, seg=40, k=1.0):
    cx, cy, cz = c; n = len(P)
    def pt(h, r, th): return np.array([cx + r * np.sin(th), cy + h, cz + r * np.cos(th)])
    for j in range(n - 1):
        (h0, r0), (h1, r1) = P[j], P[j + 1]
        for i in range(seg):
            a, b = 2 * np.pi * i / seg, 2 * np.pi * (i + 1) / seg
            Pq = [pt(h0, r0, a), pt(h0, r0, b), pt(h1, r1, b), pt(h1, r1, a)]
            cols = []
            for (th, h, r) in ((a, h0, r0), (b, h0, r0), (b, h1, r1), (a, h1, r1)):
                nrm = np.array([np.sin(th) * (h1 - h0), -(r1 - r0), np.cos(th) * (h1 - h0)]); nrm /= (np.linalg.norm(nrm) + 1e-12)
                cols.append(np.clip(col_fn(th, j, h, r) * shade(nrm) * k, 0, 255))
            m._add(Pq, cols, [(0, 1, 2), (0, 2, 3)])

def jar(m, c, k=1.0, sc=0.80):
    """piattino bianco, corpo tondo bianco con grappolo giallo e foglie, collo, tappo verde-acqua, manici a strisce (totale ~11,9 cm x 10 cm)"""
    cx, cy, cz = c
    m.lathe((cx, cy, cz), [(0.0, 0.0, '#e8e5dc'), (0.044, 0.0, '#e8e5dc'), (0.046, 0.005, '#efece3'), (0.0, 0.005, '#efece3')], seg=28, caps=False, k=k)
    P0 = [(0.007, 0.030), (0.016, 0.046), (0.034, 0.060), (0.062, 0.066), (0.085, 0.062), (0.096, 0.050), (0.101, 0.034), (0.108, 0.022), (0.116, 0.018), (0.122, 0.0165), (0.130, 0.020), (0.136, 0.011), (0.140, 0.0)]
    P = [(h * 0.88, r * 0.74) for h, r in P0]
    H = P[-1][0]
    def col_fn(th, j, h, r):
        d = (th + np.radians(35) + np.pi) % (2 * np.pi) - np.pi
        base = np.array(hex2rgb('#ece9df'))
        if h > H - 0.018: return np.array(hex2rgb('#2f8a86'))
        if abs(d) < np.radians(50) and 0.011 < h < 0.080:
            u = d / np.radians(50); v = (h - 0.011) / 0.069
            if abs(u) < 0.55 * (1 - 0.55 * v) and 0.12 < v < 0.95 and ((np.floor(u * 6) + np.floor(v * 7)) % 2 == 0 or abs(u) < 0.2): return np.array(hex2rgb('#e8b830'))
            if abs(u) < 0.95 and 0.15 < v < 0.9 and ((np.floor(u * 4 + 7) + np.floor(v * 5)) % 3 == 0): return np.array(hex2rgb('#3d6a37'))
        if 0.027 < h < 0.033 or 0.074 < h < 0.079: return np.array(hex2rgb('#3a5d6a'))
        return base
    m_lathe_painted(m, (cx, cy + 0.005, cz), P, col_fn, seg=40, k=k)
    for sgn in (-1, 1):
        for q in range(3):
            y = 0.040 + 0.009 * q
            m.box([cx + sgn * 0.058 - 0.010, cy + 0.005 + y, cz - 0.013], [cx + sgn * 0.058 + 0.010, cy + 0.005 + y + 0.0075, cz + 0.013], '#2f8a86' if q % 2 == 0 else '#ece9df', k=k)

# ---------- pianta ----------
def plant(m, pot_c, rng, k=1.0):
    cx, cy, cz = pot_c
    r0, r1, h = 0.038, 0.048, 0.094
    def col_fn(th, j, hh, r):
        d = (th + np.radians(20) + np.pi) % (2 * np.pi) - np.pi; t = hh / h
        base = np.array(hex2rgb('#efece4'))
        if abs(d) < np.radians(55) and 0.12 < t < 0.85:
            u = d / np.radians(55)
            if -0.95 < u < -0.05 and 0.18 < t < 0.78 and abs(u + 0.5) < 0.42 * (1 - 0.3 * abs(t - 0.45)): return np.array(hex2rgb('#1d1d20'))
            if 0.05 < u < 0.9 and 0.10 < t < 0.62: return np.array(hex2rgb('#4a9a4a'))
        if t < 0.12: return np.array(hex2rgb('#d6efe8'))
        return base
    m_lathe_painted(m, (cx, cy, cz), [(0.0, r0 * 0.9), (0.012, r0), (0.050, (r0 + r1) / 2), (h, r1)], col_fn, seg=28, k=k)
    m.lathe((cx, cy + h, cz), [(0.0, 0.0, '#2b2a22'), (r1 * 0.97, 0.0, '#2b2a22')], seg=28, caps=False, k=1.0)
    top = np.array([cx, cy + h, cz])
    cE, cM, cT = '#163220', '#92a98a', '#2f4a2c'
    def lf(base, d, L, W, kk=1.0, curl=0.1, up=(0, 1, 0)):
        m.leaf(base, d, up, L, W, cE, cM, cT, curl=curl, k=k * kk, c_rib='#1f4a28')
    # chioma: steli che salgono dal vaso e ricadono a ventaglio, con foglie alterne lungo lo stelo
    def stem(start, az, el0, length, droop, n_leaves, lw=(0.050, 0.062), wr=0.5, k0=1.0):
        pts = []
        for t in np.linspace(0, 1, 9):
            el = np.radians(el0) - droop * t
            pts.append(start + np.array([np.sin(az) * np.cos(el), np.sin(el), np.cos(az) * np.cos(el)]) * length * t * 0 + 0)
        # integrazione del percorso
        P = [np.array(start, float)]; d_prev = None
        for t in np.linspace(0, 1, 9)[1:]:
            el = np.radians(el0) - droop * t
            d = np.array([np.sin(az) * np.cos(el), np.sin(el), np.cos(az) * np.cos(el)])
            P.append(P[-1] + d * length / 8); d_prev = d
        for i in range(n_leaves):
            t = 0.25 + 0.75 * i / max(1, n_leaves - 1); idx = min(7, int(t * 8)); f = t * 8 - idx
            pos = P[idx] * (1 - f) + P[idx + 1] * f; dd = P[idx + 1] - P[idx]; dd /= np.linalg.norm(dd)
            sd = np.cross(dd, [0, 1, 0]); sd /= (np.linalg.norm(sd) + 1e-9)
            sgn = 1 if i % 2 == 0 else -1
            dleaf = dd * 0.55 + sd * sgn * 0.8 + np.array([0, 0.25, 0]); dleaf /= np.linalg.norm(dleaf)
            L = rng.uniform(*lw)
            lf(pos, dleaf, L, L * wr * rng.uniform(0.9, 1.1), kk=k0 * rng.uniform(0.9, 1.05), curl=rng.uniform(0.05, 0.25), up=(np.sin(az) * 0.8, 0.7, np.cos(az) * 0.8))
        # foglia in cima
        lf(P[-1], d_prev, rng.uniform(*lw), rng.uniform(*lw) * wr, kk=k0, curl=0.1, up=(np.sin(az) * 0.8, 0.7, np.cos(az) * 0.8))
    for si in range(12):
        az = 2 * np.pi * si / 12 + rng.uniform(-0.2, 0.2)
        frontish = np.cos(az) > 0.35
        start = top + np.array([0.012 * np.sin(az), 0.0, 0.012 * np.cos(az)])
        el0 = rng.uniform(72, 88) if frontish else rng.uniform(35, 75)
        stem(start, az, el0, rng.uniform(0.05, 0.08) if frontish else rng.uniform(0.10, 0.17), droop=np.radians(rng.uniform(4, 14)) if frontish else np.radians(rng.uniform(25, 60)), n_leaves=int(rng.randint(2, 4)) if frontish else int(rng.randint(3, 6)))
    # tralci: partono dal bordo sinistro del vaso, corrono sul piano verso sinistra e cadono oltre il bordo sinistro della mensola
    y_end = [1.985, 1.945, 1.905, 1.88, 1.86]
    for q in range(5):
        sx = cx - 0.035 - 0.004 * q; sy = cy + h * 0.55; sz = cz + 0.05 + 0.025 * q
        x_edge = 3.535 - 0.012 * q; zq = 0.19 + 0.012 * q
        pts = []
        for t in np.linspace(0, 1, 16):
            if t < 0.45:
                u = t / 0.45
                x = sx + (x_edge - sx) * u; z = sz + (zq - sz) * u; y = sy + 0.03 * np.sin(np.pi * u) - (sy - (cy + 0.045)) * u
            else:
                u = (t - 0.45) / 0.55
                x = x_edge - 0.010 * u; z = zq + 0.008 * u; y = (cy + 0.045) + (y_end[q] - (cy + 0.045)) * u
            pts.append(np.array([x, y, z]))
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]; dv = b - a; ln = np.linalg.norm(dv)
            if ln < 1e-6: continue
            dn = dv / ln
            for s in (-1, 1):
                side = np.cross(dn, [0, 0, 1]) if abs(dn[2]) < 0.9 else np.cross(dn, [1, 0, 0]); side /= np.linalg.norm(side)
                fwd = np.cross(side, dn)
                phi = rng.uniform(-0.9, 0.9) + (0 if s > 0 else np.pi)
                d = dn * rng.uniform(0.15, 0.6) + (side * np.cos(phi) + fwd * np.sin(phi)) * 0.85; d /= np.linalg.norm(d)
                up = (side * np.cos(phi) + fwd * np.sin(phi)) * 0.3 + np.array([0, 0.2, 1.0])
                lf(a + dv * rng.uniform(0.1, 0.8), d, rng.uniform(0.043, 0.060), rng.uniform(0.022, 0.030), kk=rng.uniform(0.92, 1.05), curl=rng.uniform(0.1, 0.3), up=tuple(up))

# ---------- fumetti ----------
def manga(m, x0, zf, depth=0.115, h=0.178, y0=0.0, k=0.9):
    spines = [
        [(0.07, '#d2cfc4'), (0.36, '#b0391b'), (0.18, '#c98a64'), (0.14, '#8a6b3d'), (0.10, '#54433a'), (0.15, '#c5c1b5')],
        [(0.07, '#d2cfc4'), (0.36, '#b0391b'), (0.18, '#c98a64'), (0.14, '#9a7a3a'), (0.10, '#5a463c'), (0.15, '#c5c1b5')],
        [(0.07, '#d2cfc4'), (0.36, '#b8401c'), (0.18, '#d09870'), (0.14, '#a08040'), (0.10, '#5d493e'), (0.15, '#cac6ba')],
        [(0.07, '#d6d3c8'), (0.36, '#b8401c'), (0.18, '#d6ac80'), (0.14, '#a88a4a'), (0.10, '#62503f'), (0.15, '#cfcbbf')],
        [(0.07, '#d6d3c8'), (0.36, '#bc4420'), (0.18, '#dbb48a'), (0.14, '#b09050'), (0.10, '#665443'), (0.15, '#d3cfc3')],
    ]
    t = 0.0105
    for i, bands in enumerate(spines):
        xa = x0 + i * t
        m.box([xa, y0, zf - depth], [xa + t, y0 + h, zf], {'+z': bands, '-x': '#6e665a', '+x': '#6e665a', '+y': '#a59f91', '-y': '#6a655a', '-z': '#8b857a'}, k=k)

def manga_back(m, x0, z, w=0.113, h=0.178, y0=0.0, k=0.9):
    bands = [(0.10, '#3a4a5a'), (0.16, '#5a82a8'), (0.14, '#8fb0c8'), (0.12, '#cfd8dc'), (0.16, '#b79a74'), (0.16, '#6b5a4a'), (0.16, '#3d3228')]
    m.box([x0, y0, z - 0.012], [x0 + w, y0 + h, z], {'+z': bands, '-x': '#6e665a', '+x': '#6e665a', '+y': '#a59f91', '-y': '#6a655a', '-z': '#8b857a'}, k=k)

# ---------- assemblaggio ----------
def build(seed=3, U=U):
    rng = np.random.RandomState(seed)
    m = Mesh()
    add_boards(m, U)
    yA, yB, yC, yD = (U['ys'][n] for n in 'ABCD')
    plant(m, (3.745, yA, 0.115), rng, k=1.0)
    jar(m, (3.672, yB, 0.125), k=0.95)
    pot_faceted(m, (3.805, yB, 0.125), r=0.033, h=0.039, k=0.92)
    succulent_rosette(m, (3.805, yB + 0.036, 0.125), rng, n=11, rl=0.038, rw=0.014, ang=(30, 60), k=0.92)
    manga(m, 3.684, 0.17, y0=yC, k=0.82)
    manga_back(m, 3.742, 0.050, y0=yC, k=0.82)
    pot_faceted(m, (3.635, yC, 0.150), r=0.034, h=0.048, k=0.9)
    succulent_rosette(m, (3.635, yC + 0.046, 0.150), rng, n=16, rl=0.070, rw=0.012, ang=(20, 55), k=0.9)
    pot_faceted(m, (3.775, yC, 0.150), r=0.034, h=0.048, k=0.9)
    succulent_rosette(m, (3.775, yC + 0.046, 0.150), rng, n=12, rl=0.048, rw=0.019, ang=(30, 65), cols=('#a0503c', '#e0907a', '#c87a5e'), k=0.9)
    vase_tulip(m, (3.683, yD, 0.110), k=1.0)
    vase_round(m, (3.763, yD, 0.150), k=1.0)
    return m

if __name__ == '__main__':
    m = build()
    m.to_json('/tmp/claude-0/s/shelf/unit_mesh.json'); print('vertici', len(m.P), 'triangoli', len(m.I))
