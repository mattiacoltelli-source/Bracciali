"""Piccole mesh a colori per vertice (ombreggiatura piatta calcolata qui), per gli oggetti che non sono scatole: mensole, piante, vasi, fumetti.
Coordinate del sistema stanza (x lungo la parete TV, y su, z verso l'ingresso). Colori sRGB; l'app li legge come colori per vertice."""
import numpy as np

def hex2rgb(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)

LIGHT = np.array([0.35, 0.85, 0.40]); LIGHT /= np.linalg.norm(LIGHT)   # luce dall'alto a destra, verso chi guarda (come nelle foto: le ombre cadono in basso a sinistra)

def shade(n, two_sided=False):
    n = np.asarray(n, float); n = n / (np.linalg.norm(n) + 1e-12)
    d = float(n @ LIGHT)
    if two_sided: return 0.80 + 0.26 * abs(d)
    return 0.70 + 0.42 * max(0.0, d) - 0.10 * max(0.0, -float(n[1]))

def rot_y(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rot_x(a):
    c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def rot_z(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

class Mesh:
    def __init__(s):
        s.P = []; s.C = []; s.I = []; s.UV = []; s.has_uv = False
    def _add(s, pts, cols, tris, uvs=None):
        i0 = len(s.P); s.P += [tuple(float(v) for v in p) for p in pts]; s.C += [tuple(float(v) for v in c) for c in cols]
        if uvs is not None: s.has_uv = True
        s.UV += [tuple(float(v) for v in u) for u in uvs] if uvs is not None else [(0.0, 0.0)] * len(pts)
        s.I += [(i0 + a, i0 + b, i0 + c) for a, b, c in tris]; return i0
    def tri(s, a, b, c, col, ref=None, two=False, k=1.0):
        a, b, c = (np.asarray(v, float) for v in (a, b, c))
        n = np.cross(b - a, c - a); ln = np.linalg.norm(n)
        if ln < 1e-12: return
        if ref is not None and float(n @ ((a + b + c) / 3 - np.asarray(ref, float))) < 0: n = -n
        f = shade(n, two or ref is None) * k
        col = np.clip(hex2rgb(col) * f if isinstance(col, str) else np.asarray(col, float) * f, 0, 255)
        s._add([a, b, c], [col] * 3, [(0, 1, 2)])
    def quad(s, a, b, c, d, col, ref=None, two=False, k=1.0):
        s.tri(a, b, c, col, ref, two, k); s.tri(a, c, d, col, ref, two, k)
    def quad_grad(s, pts, cols, ref=None, two=False, k=1.0):
        """quadrilatero con colore per vertice (gia' in sRGB, si moltiplica per l'ombra della faccia)"""
        P = [np.asarray(p, float) for p in pts]
        n = np.cross(P[1] - P[0], P[2] - P[0])
        if ref is not None and float(n @ (sum(P) / 4 - np.asarray(ref, float))) < 0: n = -n
        f = shade(n, two or ref is None) * k
        C = [np.clip((hex2rgb(c) if isinstance(c, str) else np.asarray(c, float)) * f, 0, 255) for c in cols]
        s._add(P, C, [(0, 1, 2), (0, 2, 3)])
    # --- solidi ---
    def box(s, mn, mx, cols, rot=None, pivot=None, k=1.0):
        """cols: dict faccia->colore ('+x','-x','+y','-y','+z','-z'), oppure un colore unico. rot: matrice 3x3 attorno a pivot (default centro)"""
        mn = np.asarray(mn, float); mx = np.asarray(mx, float); ctr = (mn + mx) / 2
        pv = ctr if pivot is None else np.asarray(pivot, float)
        T = (lambda p: p) if rot is None else (lambda p: pv + rot @ (np.asarray(p, float) - pv))
        x0, y0, z0 = mn; x1, y1, z1 = mx
        F = {'+x': [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], '-x': [(x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (x0, y0, z0)],
             '+y': [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], '-y': [(x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1)],
             '+z': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], '-z': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)]}
        for f, q in F.items():
            c = cols if isinstance(cols, str) else cols.get(f)
            if c is None: continue
            q = [T(p) for p in q]
            if isinstance(c, (list, tuple)) and c and isinstance(c[0], (list, tuple)):   # bande: [(frazione_altezza, colore), ...] dall'alto in basso, solo facce verticali
                s.banded(q, c, ref=T(ctr), k=k)
            else:
                s.quad(*q, c, ref=T(ctr), k=k)
    def banded(s, q, bands, ref=None, k=1.0):
        """faccia verticale q = [in basso a sx, in basso a dx, in alto a dx, in alto a sx] divisa in bande orizzontali (dall'alto: frazione, colore)"""
        q = [np.asarray(p, float) for p in q]; tot = sum(b[0] for b in bands); t = 0.0
        for fr, col in bands:
            t0, t1 = t / tot, (t + fr) / tot; t += fr
            def at(u, v): return (q[0] * (1 - u) + q[1] * u) * (1 - v) + (q[3] * (1 - u) + q[2] * u) * v
            # v = 1 in alto: la banda i va da v = 1 - t1 a v = 1 - t0
            s.quad(at(0, 1 - t1), at(1, 1 - t1), at(1, 1 - t0), at(0, 1 - t0), col, ref=ref, k=k)
    def prism(s, poly, y0, y1, col_top, col_bot, cols_side, k=1.0):
        """poligono convesso in pianta (x,z) estruso fra y0 e y1; cols_side: lista di colori, uno per spigolo (dal vertice i al i+1) o un colore"""
        poly = [tuple(p) for p in poly]; n = len(poly); ctr = np.array([sum(p[0] for p in poly) / n, (y0 + y1) / 2, sum(p[1] for p in poly) / n])
        top = [np.array([x, y1, z]) for x, z in poly]; bot = [np.array([x, y0, z]) for x, z in poly]
        for i in range(1, n - 1):
            s.tri(top[0], top[i], top[i + 1], col_top, ref=ctr, k=k); s.tri(bot[0], bot[i], bot[i + 1], col_bot, ref=ctr, k=k)
        for i in range(n):
            j = (i + 1) % n; c = cols_side if isinstance(cols_side, str) else cols_side[i]
            if c is None: continue
            s.quad(bot[i], bot[j], top[j], top[i], c, ref=ctr, k=k)
    def lathe(s, center, prof, seg=24, rot=None, smooth=True, caps=True, phase=0.0, k=1.0, shade_fn=None, two=False, ell=None, dy_fn=None):
        """solido di rotazione attorno all'asse verticale per `center`: prof = [(raggio, quota, colore), ...] dal basso; rot: matrice per inclinarlo"""
        cx, cy, cz = center; n = len(prof); R = np.eye(3) if rot is None else rot
        cols = [hex2rgb(p[2]) if isinstance(p[2], str) else np.asarray(p[2], float) for p in prof]
        def pt(r, y, th, j=0):
            sx, sz = ell(y) if ell else (1.0, 1.0)
            dy = dy_fn(th, y) if dy_fn else 0.0
            return np.array([cx, cy, cz]) + R @ np.array([r * sx * np.sin(th), y + dy, r * sz * np.cos(th)])
        ths = [phase + 2 * np.pi * i / seg for i in range(seg + 1)]
        # normali alle quote (inclinazione del profilo)
        def prof_n(j, th):
            j0, j1 = max(j - 1, 0), min(j + 1, n - 1); dr = prof[j1][0] - prof[j0][0]; dy = prof[j1][1] - prof[j0][1]
            m = np.array([dy * np.sin(th), -dr, dy * np.cos(th)]); return R @ (m / (np.linalg.norm(m) + 1e-12))
        for j in range(n - 1):
            for i in range(seg):
                a, b = ths[i], ths[i + 1]
                P = [pt(prof[j][0], prof[j][1], a), pt(prof[j][0], prof[j][1], b), pt(prof[j + 1][0], prof[j + 1][1], b), pt(prof[j + 1][0], prof[j + 1][1], a)]
                if smooth:
                    Ns = [prof_n(j, a), prof_n(j, b), prof_n(j + 1, b), prof_n(j + 1, a)]
                    Cs = [np.clip(cols[[j, j, j + 1, j + 1][q]] * (shade_fn(Ns[q]) if shade_fn else shade(Ns[q], two)) * k, 0, 255) for q in range(4)]
                    s._add(P, Cs, [(0, 1, 2), (0, 2, 3)])
                else:
                    nn = np.cross(P[1] - P[0], P[2] - P[0]) if j < n - 1 else np.zeros(3)
                    mid = (prof_n(j, (a + b) / 2) + prof_n(j + 1, (a + b) / 2)) / 2
                    f = (shade_fn(mid) if shade_fn else shade(mid, two)) * k
                    Cs = [np.clip(cols[[j, j, j + 1, j + 1][q]] * f, 0, 255) for q in range(4)]
                    s._add(P, Cs, [(0, 1, 2), (0, 2, 3)])
        if caps:
            for end, up in ((0, -1.0), (n - 1, 1.0)):
                r, y, col = prof[end]
                if r < 1e-6: continue
                c0 = pt(0, y, 0); nrm = R @ np.array([0, up, 0]); cc = np.clip(cols[end] * shade(nrm, two) * k, 0, 255)
                for i in range(seg):
                    s._add([c0, pt(r, y, ths[i]), pt(r, y, ths[i + 1])], [cc] * 3, [(0, 1, 2)])
    def leaf(s, base, along, up, length, width, c_edge, c_mid, c_end=None, curl=0.0, k=1.0, rows=(0.0, 0.35, 0.7, 1.0), c_rib=None):
        """foglia: foglio piegato a V leggero, lungo `along` dalla base, largo `width` (perpendicolare a along e up); curl = abbassamento della punta (frazione della lunghezza).
        Colori: bordo, bande chiare ai lati della nervatura, nervatura (c_rib). Vertici condivisi, ombra per vertice con la normale a V."""
        base = np.asarray(base, float); a = np.asarray(along, float); a = a / np.linalg.norm(a)
        u = np.asarray(up, float); side = np.cross(a, u); side /= (np.linalg.norm(side) + 1e-12); nrm = np.cross(side, a)
        ce, cm = hex2rgb(c_edge), hex2rgb(c_mid); cend = hex2rgb(c_end) if c_end else cm * 0.7
        cr = hex2rgb(c_rib) if c_rib else (ce * 0.5 + cm * 0.5) * 0.9
        ts = (-1.0, -0.78, -0.62, -0.46, 0.0, 0.46, 0.62, 0.78, 1.0); tc = (ce, ce, cm, ce, cr, ce, cm, ce, ce)
        nl = nrm - 0.45 * side; nl /= np.linalg.norm(nl); nr = nrm + 0.45 * side; nr /= np.linalg.norm(nr)
        shd = [shade(nl, True)] * 4 + [shade(nrm, True)] + [shade(nr, True)] * 4
        V = []; Cc = []
        for si, sf in enumerate(rows):
            w = width / 2 * (np.sin(np.pi * min(1.0, sf ** 0.8)) ** 0.7 if 0 < sf < 1 else 0.0)
            ctr = base + a * length * sf - nrm * (curl * length * sf * sf)
            fold = 0.18 * w
            for q, (t, ct) in enumerate(zip(ts, tc)):
                V.append(ctr + side * w * t + nrm * (fold * abs(t)))
                Cc.append(np.clip((ct if si not in (0, len(rows) - 1) else cend) * shd[q] * k, 0, 255))
        nc = len(ts); T = []
        for si in range(len(rows) - 1):
            for t in range(nc - 1):
                i00 = si * nc + t; i01 = i00 + 1; i10 = (si + 1) * nc + t; i11 = i10 + 1
                T += [(i00, i01, i11), (i00, i11, i10)]
        s._add(V, Cc, T)
    def extend(s, other, fn=None):
        """accoda un'altra mesh, con una trasformazione dei punti fn(P: (n,3)) -> (n,3) (rotazione, scala)"""
        if not other.P: return
        P = np.array(other.P, float)
        if fn is not None: P = fn(P)
        uv = other.UV if other.has_uv else None
        s._add(P, other.C, other.I, uv)
    # --- salvataggio ---
    def arrays(s):
        P = np.array(s.P, np.float32); C = np.clip(np.round(np.array(s.C)), 0, 255).astype(np.uint8); I = np.array(s.I, np.uint32)
        return P, C, I
    def pack(s):
        """blob per il pacchetto: posizioni float32 (nv*3), colori uint8 (nv*3, riempiti a 4 byte), [uv float32 (nv*2) se ci sono], indici uint16 (ni)"""
        P, C, I = s.arrays(); nv = len(P)
        assert nv < 65536, nv
        cb = C.tobytes(); cb += b'\0' * ((-len(cb)) % 4)
        uvb = np.array(s.UV, np.float32).tobytes() if s.has_uv else b''
        meta = dict(nv=nv, ni=int(I.size))
        if s.has_uv: meta['uv'] = 1
        return meta, P.tobytes() + cb + uvb + I.astype(np.uint16).tobytes()
    def to_json(s, path, **extra):
        import json
        P, C, I = s.arrays(); d = dict(pos=np.round(P, 5).ravel().tolist(), col=C.ravel().tolist(), idx=I.ravel().tolist())
        if s.has_uv: d['uv'] = np.round(np.array(s.UV, np.float32), 5).ravel().tolist()
        d.update(extra); json.dump(d, open(path, 'w')); return d
