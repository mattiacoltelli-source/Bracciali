"""Oggetti sopra la console, in 3D: figure Funko come rilievi (la foto frontale e la sua silhouette 'gonfiata' a profondita'), custodia del fumetto, lampada, telecamera, ciotola.
Le figure: da una foto ravvicinata si ricava la maschera della sagoma; la profondita' di ogni punto vien dalla distanza dal bordo (profilo tondeggiante), cosi' la sagoma e' esatta e
il colore e' la foto stessa (texture con maschera alfa). Coordinate del sistema stanza (x lungo la parete TV, y su, z verso l'ingresso); la console corre lungo z con il fronte verso -x."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh, hex2rgb, shade

def fill_outside(rgb, mask, erode=2):
    """riempie fuori dalla maschera con il colore del pixel interno piu' vicino (niente alone di parete ai bordi)"""
    m = (mask > 127).astype(np.uint8)
    core = cv2.erode(m, np.ones((3, 3), np.uint8), iterations=erode)
    if core.sum() < 50: core = m
    src = (core == 0).astype(np.uint8)
    dist, lab = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(core)
    lut = np.zeros((lab.max() + 1, 3), np.uint8); lut[lab[ys, xs]] = rgb[ys, xs]
    out = lut[lab]; out[core > 0] = rgb[core > 0]
    return out

def relief(mesh, rgb, mask, ppm, base_px, pos, step=0.0022, R=0.025, flat=0.85, shade_min=0.5, depth_fn=None, front=-1.0, pad_cells=2):
    """Aggiunge a `mesh` la superficie in rilievo di una figura. rgb/mask: ritaglio (BGR / 0-255) con `ppm` pixel per metro; base_px = (u, v) del centro della base nel ritaglio;
    pos = (x, y, z) stanza di quel punto. L'immagine ha la destra verso +z, il davanti verso -x. UV normalizzate sul ritaglio."""
    H, W = mask.shape
    m = (mask > 127).astype(np.uint8)
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 5) / ppm
    dt = cv2.GaussianBlur(dt, (0, 0), 0.0006 * ppm)
    dd = np.minimum(dt, R)
    hmap = flat * np.sqrt(dd * (2 * R - dd))
    if depth_fn is not None: hmap = depth_fn(hmap, dt, W, H)
    gpx = step * ppm
    u0, v0 = base_px
    ys, xs = np.nonzero(m)
    ua, ub, va, vb = xs.min(), xs.max(), ys.min(), ys.max()
    us = np.arange(ua - pad_cells * gpx, ub + pad_cells * gpx + gpx, gpx); vs = np.arange(va - pad_cells * gpx, vb + pad_cells * gpx + gpx, gpx)
    nu, nv = len(us), len(vs)
    big = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * pad_cells * gpx) | 1, int(2 * pad_cells * gpx) | 1)))
    def sample(a, u, v):
        ui = np.clip(u, 0, W - 1.001); vi = np.clip(v, 0, H - 1.001); i0 = ui.astype(int); j0 = vi.astype(int); fu = ui - i0; fv = vi - j0
        return (a[j0, i0] * (1 - fu) * (1 - fv) + a[j0, i0 + 1] * fu * (1 - fv) + a[j0 + 1, i0] * (1 - fu) * fv + a[j0 + 1, i0 + 1] * fu * fv)
    U, V = np.meshgrid(us, vs)
    hh = sample(hmap, U, V)
    used = sample(big.astype(np.float32), U, V) > 0.5
    # normali per l'ombra: gradiente della profondita'
    hu = np.gradient(hh, axis=1) / (gpx / ppm); hv = np.gradient(hh, axis=0) / (gpx / ppm)       # m/m
    nx = 1.0; ny = hv; nz = -hu
    cosang = nx / np.sqrt(nx * nx + ny * ny + nz * nz)
    f = shade_min + (1 - shade_min) * np.clip(cosang, 0, 1) ** 0.8
    idx = -np.ones((nv, nu), int)
    P = []; C = []; UV = []
    for j in range(nv):
        for i in range(nu):
            if not used[j, i]: continue
            idx[j, i] = len(P)
            P.append((pos[0] + front * hh[j, i], pos[1] + (v0 - V[j, i]) / ppm, pos[2] + (U[j, i] - u0) / ppm))
            c = 255.0 * f[j, i]; C.append((c, c, c)); UV.append((U[j, i] / W, 1.0 - V[j, i] / H))
    T = []
    for j in range(nv - 1):
        for i in range(nu - 1):
            a, b, c, d = idx[j, i], idx[j, i + 1], idx[j + 1, i + 1], idx[j + 1, i]
            if min(a, b, c, d) < 0: continue
            T += [(a, b, c), (a, c, d)]
    mesh._add(P, C, T, UV)
    return len(P)


# ---------------------------------------------------------------- superfici parametriche
def param(mesh, f, nu, nv, color_fn, ref=None, closed_u=False, k=1.0, two=False, uv_fn=None):
    """Superficie parametrica: f(U, V) -> (..., 3) vettorializzata, u e v in [0, 1]; color_fn(U, V, P, N) -> (..., 3) colore sRGB 0-255 (poi per l'ombra della faccia).
    Le normali vengono dalle differenze finite e puntano via da `ref` (un punto dentro al solido)."""
    us = np.linspace(0, 1, nu + 1); vs = np.linspace(0, 1, nv + 1)
    U, V = np.meshgrid(us, vs)
    P = np.asarray(f(U, V), float)
    du = np.gradient(P, axis=1); dv = np.gradient(P, axis=0)
    N = np.cross(du, dv); ln = np.linalg.norm(N, axis=-1, keepdims=True); N = N / np.maximum(ln, 1e-12)
    if ref is not None:
        sgn = np.sign(np.sum(N * (P - np.asarray(ref, float)), axis=-1, keepdims=True)); sgn[sgn == 0] = 1; N = N * sgn
    C = np.asarray(color_fn(U, V, P, N), float)
    sh = np.vectorize(lambda a, b, c: shade((a, b, c), two))(N[..., 0], N[..., 1], N[..., 2])
    C = np.clip(C * sh[..., None] * k, 0, 255)
    nv1, nu1 = U.shape
    idx = np.arange(nv1 * nu1).reshape(nv1, nu1)
    T = []
    for j in range(nv):
        for i in range(nu):
            a, b, c, d = idx[j, i], idx[j, i + 1], idx[j + 1, i + 1], idx[j + 1, i]
            T += [(a, b, c), (a, c, d)]
    uvs = None
    if uv_fn is not None: uvs = np.asarray(uv_fn(U, V), float).reshape(-1, 2)
    return mesh._add(P.reshape(-1, 3), C.reshape(-1, 3), T, uvs)

def sphere(mesh, c, r, color_fn, seg=14, rings=10, squash=(1.0, 1.0, 1.0), k=1.0):
    c = np.asarray(c, float); sq = np.asarray(squash, float)
    def f(U, V):
        th = 2 * np.pi * U; ph = np.pi * V
        return c + np.stack([r * sq[0] * np.sin(ph) * np.sin(th), r * sq[1] * np.cos(ph) * np.ones_like(th), r * sq[2] * np.sin(ph) * np.cos(th)], -1)
    return param(mesh, f, seg, rings, color_fn, ref=c, k=k)

def tube(mesh, pts, radius, color, seg=8, k=1.0):
    """tubo lungo una spezzata (cavo, asta): sezione circolare, senza tappi"""
    pts = [np.asarray(p, float) for p in pts]; n = len(pts)
    tang = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]) for i in range(n)]
    tang = [t / np.linalg.norm(t) for t in tang]
    ring = []
    ref = np.array([0.0, 1.0, 0.0])
    for p, t in zip(pts, tang):
        a = np.cross(t, ref)
        if np.linalg.norm(a) < 1e-6: a = np.cross(t, np.array([1.0, 0, 0]))
        a /= np.linalg.norm(a); b = np.cross(t, a)
        ring.append([p + radius * (np.cos(2 * np.pi * i / seg) * a + np.sin(2 * np.pi * i / seg) * b) for i in range(seg + 1)])
    col = hex2rgb(color) if isinstance(color, str) else np.asarray(color, float)
    for j in range(n - 1):
        for i in range(seg):
            q = [ring[j][i], ring[j][i + 1], ring[j + 1][i + 1], ring[j + 1][i]]
            nn = np.cross(q[1] - q[0], q[3] - q[0]); mid = (q[0] + q[2]) / 2; cen = (pts[j] + pts[j + 1]) / 2
            mesh.tri(q[0], q[1], q[2], col, ref=cen, k=k); mesh.tri(q[0], q[2], q[3], col, ref=cen, k=k)

def noise2(seed, shape, scales=((8, 1.0), (16, 0.5), (32, 0.25))):
    """rumore liscio in [0,1] a piu' scale (per le stagnole e le venature); deterministico"""
    rng = np.random.RandomState(seed); out = np.zeros(shape)
    for sc, w in scales:
        g = rng.rand(max(2, shape[0] // sc + 2), max(2, shape[1] // sc + 2))
        out += w * cv2.resize(g, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    out -= out.min(); out /= max(out.max(), 1e-9); return out

# ---------------------------------------------------------------- lampada nera con paralume plissettato
def lamp(mesh, c=(7.00, 0.776, 4.405), r_top=0.056, r_hem=0.048, h_shade=0.10, h_rod=0.27, pleats=26):
    """base piatta nera, asta sottile con colletto svasato, paralume a pieghe (esterno nero, interno chiaro). c = centro della base sul piano della console"""
    cx, y0, cz = c
    mesh.box((cx - 0.046, y0, cz - 0.046), (cx + 0.046, y0 + 0.005, cz + 0.046), {'+y': '#2a2a2d', '-y': '#151517', '+x': '#1d1d20', '-x': '#212124', '+z': '#1d1d20', '-z': '#212124'})
    rod = [(0.0050, 0.0, '#242427'), (0.0044, 0.10, '#202023'), (0.0042, 0.20, '#202023'), (0.0048, h_rod - 0.02, '#232326'), (0.0095, h_rod - 0.006, '#26262a'), (0.0140, h_rod + 0.012, '#26262a')]
    mesh.lathe((cx, y0 + 0.005, cz), rod, seg=14, caps=False, k=1.25)
    yh = y0 + h_rod                     # quota dell'orlo inferiore del paralume
    def pl(U):                           # onda a triangolo: pieghe nette
        t = (U * pleats) % 1.0; return np.abs(2 * t - 1)
    Lh2 = np.array([-0.45, 0.30, -0.85]); Lh2 /= np.linalg.norm(Lh2)     # le pieghe che guardano la stanza (verso -x) prendono la luce
    def outer(U, V):
        r = r_hem + (r_top - r_hem) * V + 0.0030 * pl(U) * (1 - 0.3 * V)
        y = yh + h_shade * V - 0.0030 * pl(U) * (1 - V) ** 3 * 1.0     # orlo a festone
        th = 2 * np.pi * U
        return np.stack([cx + r * np.sin(th), y, cz + r * np.cos(th)], -1)
    def col_out(U, V, P, N):
        lit = np.clip(N @ Lh2, 0, 1)
        g = 15 + 62 * lit ** 1.6
        return np.stack([g, g, g * 1.06], -1)
    param(mesh, outer, pleats * 4, 3, col_out, ref=(cx, yh + h_shade / 2, cz), k=1.0)
    def inner(U, V):
        r = (r_hem - 0.0012) + (r_top - r_hem) * V + 0.0030 * pl(U) * (1 - 0.3 * V)
        y = yh + h_shade * V - 0.0030 * pl(U) * (1 - V) ** 3
        th = 2 * np.pi * U
        return np.stack([cx + r * np.sin(th), y, cz + r * np.cos(th)], -1)
    param(mesh, inner, pleats * 3, 2, lambda U, V, P, N: np.stack([236 - 22 * V, 231 - 24 * V, 216 - 28 * V], -1), ref=(cx, yh + h_shade / 2, cz) , k=1.0, two=True)
    # disco chiaro sotto il bordo superiore (diffusore)
    mesh.lathe((cx, yh + h_shade - 0.012, cz), [(0.0, 0, '#ece7d8'), (r_top - 0.006, 0, '#ece7d8')], seg=28, caps=False, two=True, k=1.0)

# ---------------------------------------------------------------- telecamera bianca (Arlo) sul suo piedino
def camera(mesh, c=(7.015, 0.776, 2.868), scale=0.90, yaw=np.radians(40.0)):
    """c = centro del piedino sul piano. Costruita con il fronte verso -z, poi scalata e ruotata di `yaw` attorno alla verticale (nelle foto il fronte guarda a meta' fra la stanza e l'arco)."""
    R_ = _roty(yaw); c0 = np.array(c, float)
    tmp = Mesh(); _camera_raw(tmp, c)
    mesh.extend(tmp, lambda P: c0 + (P - c0) @ (scale * R_).T)

def _camera_raw(mesh, c):
    cx, y0, cz = c
    white = np.array([238.0, 236.0, 230.0])
    # piedino: disco basso con la cima che sale al collo
    base = [(0.0, 0.0, white), (0.0270, 0.0, white), (0.0272, 0.0016, white), (0.0262, 0.0036, white), (0.0200, 0.0056, white), (0.0120, 0.0078, white), (0.0098, 0.0100, white), (0.0095, 0.0180, white)]
    mesh.lathe((cx, y0, cz), [(r, y, tuple(col)) for r, y, col in base], seg=32, caps=False, k=0.98)
    yb, H, p = y0 + 0.0185, 0.066, 3.0
    rx, rz = 0.0232, 0.0208
    def sx(v):
        t = 2 * v - 1; return (1 - np.abs(t) ** p) ** (1 / p)
    def body(U, V):
        th = 2 * np.pi * U; Vr = (1 - np.cos(np.pi * V)) / 2; s = sx(Vr)
        return np.stack([cx + rx * s * np.sin(th), yb + H * Vr, cz + rz * s * np.cos(th)], -1)
    param(mesh, body, 40, 30, lambda U, V, P, N: np.broadcast_to(white, P.shape).copy(), ref=(cx, yb + H / 2, cz), k=1.0)
    # pannello frontale (verso -z): ovale scuro con cornice nera sottile e led, che segue la superficie del corpo
    def front_pt(xl, yl, off):
        t = 2 * ((yl - yb) / H) - 1; s = (1 - abs(t) ** p) ** (1 / p)
        zz = -rz * s * np.sqrt(max(0.0, 1 - (xl / (rx * s + 1e-9)) ** 2))
        return np.array([cx + xl, yl, cz + zz - off])
    ym = yb + H * 0.50; a, b = 0.0192, 0.0290
    def panel_f(a_, b_, yc, off, e=2.6):
        def f(U, V):
            th = 2 * np.pi * U
            c, s_ = np.cos(th), np.sin(th)
            r = 1.0 / (np.abs(c) ** e + np.abs(s_) ** e) ** (1.0 / e)          # superellisse: ovale squadrato per la cornice
            xl = a_ * V * r * c; yl = yc + b_ * V * r * s_
            return np.array([front_pt(x, y, off) for x, y in zip(xl.ravel(), yl.ravel())]).reshape(U.shape + (3,))
        return f
    param(mesh, panel_f(a, b, ym, 0.0004), 28, 6, lambda U, V, P, N: np.broadcast_to(np.array([14.0, 14.0, 16.0]), P.shape).copy(), ref=(cx, ym, cz), two=True, k=1.0)
    def col_lens(U, V, P, N):
        t = np.clip((P[..., 1] - (ym + 0.004 - 0.016)) / 0.032, 0, 1)
        g = 118 + 62 * t
        return np.stack([g, g * 1.01, g * 1.04], -1)
    param(mesh, panel_f(0.0128, 0.0185, ym + 0.0075, 0.0007, e=2.0), 24, 5, col_lens, ref=(cx, ym, cz), two=True, k=1.0)
    led = front_pt(-0.0030, ym - 0.0225, 0.0009)
    sphere(mesh, led, 0.0011, lambda U, V, P, N: np.broadcast_to(np.array([70.0, 130.0, 255.0]), P.shape).copy(), seg=8, rings=5, k=1.2)
    # cavo bianco sottile: dal retro della testa, in un arco che scende sul piano e continua verso il muro
    pts = [(cx + 0.002, yb + 0.030, cz + rz * 0.95), (cx + 0.004, yb + 0.032, cz + rz + 0.010), (cx + 0.008, yb + 0.024, cz + rz + 0.022), (cx + 0.014, yb + 0.010, cz + rz + 0.032),
           (cx + 0.022, y0 + 0.0025, cz + rz + 0.040), (cx + 0.040, y0 + 0.0020, cz + rz + 0.050), (cx + 0.058, y0 + 0.0020, cz + rz + 0.058)]
    tube(mesh, pts, 0.0015, (214, 212, 206), seg=6, k=1.0)

# ---------------------------------------------------------------- ciotola nera a barca con cioccolatini
def foil_color(seed, base, hi, lo, shape):
    """colore a stagnola: base + chiazze chiare/scure da rumore (per sfere e scatole di carta stagnola)"""
    n = noise2(seed, shape, ((4, 1.0), (8, 0.6), (16, 0.3)))
    def f(U, V, P, N):
        g = noise2_at(n, U, V)
        t = np.clip((g - 0.5) * 2.2, -1, 1)[..., None]
        out = np.where(t >= 0, np.asarray(base) * (1 - t) + np.asarray(hi) * t, np.asarray(base) * (1 + t) + np.asarray(lo) * (-t))
        return out
    return f

def noise2_at(n, U, V):
    H, W = n.shape; x = np.clip(U * (W - 1), 0, W - 1.001); y = np.clip(V * (H - 1), 0, H - 1.001)
    i = x.astype(int); j = y.astype(int); fx = x - i; fy = y - j
    return n[j, i] * (1 - fx) * (1 - fy) + n[j, i + 1] * fx * (1 - fy) + n[j + 1, i] * (1 - fx) * fy + n[j + 1, i + 1] * fx * fy

def dish(mesh, c=(6.99, 0.776, 3.675), L=0.235, W=0.115, hr=0.040, up=0.012, D=0.040, seed=5):
    """barca nera sul suo piedino, bordi che si alzano ai due estremi; dentro, cioccolatini (palline dorate, carte rosa e rosse). c = centro sul piano, asse lungo z."""
    cx, y0, cz = c
    foot_h = 0.005
    def w_of(s, t=0.0): return np.maximum(W / 2 * (1 - np.abs(s) ** 2.2) ** 0.62 - t, 1e-4)
    def rim_of(s): return y0 + foot_h + hr + up * np.abs(s) ** 2.4
    def bottom_of(s, t=0.0): return rim_of(s) - np.maximum(D * (1 - np.abs(s) ** 1.8) ** 0.8 - t, 0.0)
    def make(t, outward):
        def f(U, V):
            s = 2 * U - 1; ph = np.pi * V
            w = w_of(s, t); yb = bottom_of(s, t); yr = rim_of(s)
            return np.stack([cx + w * np.cos(ph), yr - (yr - yb) * np.sin(ph), cz + s * L / 2], -1)
        return f
    black = np.array([26.0, 26.0, 29.0])
    param(mesh, make(0.0, True), 44, 16, lambda U, V, P, N: np.broadcast_to(black, P.shape).copy(), ref=(cx, y0 + foot_h + hr * 0.5, cz), k=1.18)
    param(mesh, make(0.003, False), 44, 12, lambda U, V, P, N: np.broadcast_to(np.array([19.0, 19.0, 21.0]), P.shape).copy(), ref=(cx, y0 + foot_h + hr * 2.0, cz), two=True, k=1.0)
    # bordo: striscia sottile
    for i in range(44):
        s0, s1 = 2 * i / 44 - 1, 2 * (i + 1) / 44 - 1
        for ph in (0.0, np.pi):
            a0 = np.array([cx + w_of(s0) * np.cos(ph), rim_of(s0), cz + s0 * L / 2]); a1 = np.array([cx + w_of(s1) * np.cos(ph), rim_of(s1), cz + s1 * L / 2])
            b0 = np.array([cx + w_of(s0, 0.003) * np.cos(ph), rim_of(s0), cz + s0 * L / 2]); b1 = np.array([cx + w_of(s1, 0.003) * np.cos(ph), rim_of(s1), cz + s1 * L / 2])
            mesh.quad(a0, a1, b1, b0, (40, 40, 44), two=True)
    # piedino ovale
    mesh.lathe((cx, y0, cz), [(0.0, 0.0, '#18181a'), (1.0, 0.0, '#18181a'), (0.95, foot_h + 0.002, '#1c1c1e')], seg=24, caps=False, ell=lambda y: (0.52 * L / 2 / 1.0 * 0.0 + 0.028, 0.050), k=1.0) if False else None
    foot = [(0.0, 0.0, '#18181a'), (0.030, 0.0, '#18181a'), (0.030, foot_h, '#1c1c1e'), (0.0, foot_h, '#1c1c1e')]
    mesh.lathe((cx, y0, cz), foot, seg=24, caps=False, ell=lambda y: (0.55, 1.35), k=1.0)
    # cioccolatini: (z relativo, x relativo, quota sul fondo, tipo, colore, rotazione)
    rng = np.random.RandomState(seed)
    gold = (176, 126, 34); gold_hi = (236, 198, 96); gold_lo = (88, 56, 10)
    items = [(-0.085, 0.004, 0.012, 'fr'), (-0.064, -0.016, 0.009, 'cup'), (-0.058, 0.012, 0.014, 'fr'), (-0.040, -0.014, 0.014, 'mc_pink'), (-0.020, 0.014, 0.014, 'mc_pink2'),
             (-0.012, -0.012, 0.014, 'fr'), (0.010, 0.012, 0.014, 'mc_label'), (0.020, -0.014, 0.014, 'mc_red'), (0.040, 0.010, 0.014, 'fr'), (0.056, -0.012, 0.014, 'mc_pink'),
             (0.070, 0.012, 0.014, 'fr'), (0.086, 0.002, 0.012, 'mc_red'),
             (-0.048, 0.000, 0.030, 'mc_pink'), (-0.026, -0.002, 0.030, 'fr'), (0.000, 0.002, 0.031, 'mc_pink2'), (0.026, 0.002, 0.030, 'fr'), (0.050, 0.000, 0.030, 'mc_red'),
             (-0.012, 0.004, 0.046, 'mc_label'), (0.012, -0.004, 0.045, 'fr'), (-0.034, -0.004, 0.045, 'mc_pink2')]
    for k_, (dz, dx, dy, kind) in enumerate(items):
        s = dz / (L / 2); yb_ = bottom_of(s, 0.003)
        P0 = np.array([cx + dx, yb_ + dy, cz + dz])
        if kind == 'fr':
            f = foil_color(seed + k_, gold, gold_hi, gold_lo, (24, 24))
            sphere(mesh, P0, 0.0128, f, seg=14, rings=10, squash=(1.0, 0.95, 1.0), k=1.05)
        elif kind == 'cup':
            mesh.lathe(P0 - np.array([0, 0.010, 0]), [(0.010, 0.0, '#3a2312'), (0.016, 0.012, '#4a2f19'), (0.018, 0.014, '#2a190c')], seg=16, caps=True, k=1.0)
        else:
            base = {'mc_pink': (196, 66, 88), 'mc_pink2': (208, 96, 112), 'mc_label': (224, 150, 160), 'mc_red': (162, 26, 38)}[kind]
            rot = _rotz(rng.uniform(-0.5, 0.5)) @ _roty(rng.uniform(-0.9, 0.9))
            f = foil_color(seed + 40 + k_, base, tuple(min(255, v * 1.25 + 30) for v in base), tuple(v * 0.55 for v in base), (24, 24))
            rbox(mesh, P0, (0.0105, 0.0100, 0.0115), f, e=0.5, rot=rot, k=1.05)

def rbox(mesh, c, half, color_fn, e=0.45, rot=None, seg=14, rings=10, k=1.0):
    """scatola con gli spigoli arrotondati (superellissoide): carta stagnola dei cioccolatini"""
    c = np.asarray(c, float); h = np.asarray(half, float); R = np.eye(3) if rot is None else rot
    def sp(x, e_): return np.sign(x) * np.abs(x) ** e_
    def f(U, V):
        th = 2 * np.pi * U - np.pi; ph = np.pi * V - np.pi / 2
        x = sp(np.cos(ph), e) * sp(np.sin(th), e); y = sp(np.sin(ph), e); z = sp(np.cos(ph), e) * sp(np.cos(th), e)
        return c + (np.stack([h[0] * x, h[1] * y, h[2] * z], -1) @ R.T)
    return param(mesh, f, seg, rings, color_fn, ref=c, k=k)

def _rotz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
def _roty(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def base_face_colors(base, rng):
    b = np.array(base, float)
    return {f: tuple(np.clip(b * rng.uniform(0.82, 1.12), 0, 255)) for f in ('+x', '-x', '+y', '-y', '+z', '-z')}

# ---------------------------------------------------------------- figure a rilievo, custodia, basi
ASSETS = os.environ.get('CONSOLE_ASSETS', '')        # ritagli e maschere dalle foto (fuori dal repository)
Y0 = 0.776                                           # piano della console
POS = dict(camera=(7.015, 2.868), mando=(6.96, 3.033), case=(7.0, 3.36), dish=(6.99, 3.675), art=(6.936, 3.969), pw=(6.885, 4.26), lamp=(7.0, 4.43))

def jpg(img, q=88):
    ok, b = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q, cv2.IMWRITE_JPEG_OPTIMIZE, 1]); assert ok; return b.tobytes()

def relief_part(name, x, z, y=Y0, scale=0.5, step=0.0022, R=0.025, flat=0.85, shade_min=0.72, height_m=None, q=86, z_off=0.0, az_deg=0.0):
    """figura a rilievo da ritaglio+maschera: ritorna (parte, immagini). x = profondita' del piano centrale, z = centro (bbox) della figura"""
    import json
    P = json.load(open(f'{ASSETS}/params.json'))[name]
    rgb = cv2.imread(f'{ASSETS}/{name}_rgb.png'); mask = cv2.imread(f'{ASSETS}/{name}_mask.png', 0)
    ys, xs = np.nonzero(mask > 127)
    u0 = (xs.min() + xs.max()) / 2.0; v0 = P['base_px'][1]
    ppm = (v0 - P['top_row']) / (height_m or P['height_m'])
    m = Mesh(); tmp = Mesh(); relief(tmp, rgb, mask, ppm, (u0, v0), (x, y, z + z_off), step=step, R=R, flat=flat, shade_min=shade_min)
    c0 = np.array([x, 0.0, z + z_off]); Rz = _roty(np.radians(az_deg))          # il piano guarda verso chi ha scattato la foto
    m.extend(tmp, lambda P: c0 + (P - c0) @ Rz.T)
    tex = fill_outside(rgb, mask)
    tex = cv2.resize(tex, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    al = cv2.resize(cv2.GaussianBlur(mask, (0, 0), 0.9), None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    part = dict(name=name, mesh=m, map=f'cobj_{name}', amap=f'cobj_{name}_a', atest=0.5)
    return part, {f'cobj_{name}': jpg(tex, q), f'cobj_{name}_a': jpg(al, 92)}, ppm

def quad_tex(mesh, p00, p10, p11, p01, uv=((0, 0), (1, 0), (1, 1), (0, 1)), col=(255, 255, 255)):
    """quadrilatero con texture (angoli in ordine: basso-sx, basso-dx, alto-dx, alto-sx)"""
    mesh._add([p00, p10, p11, p01], [col] * 4, [(0, 1, 2), (0, 2, 3)], list(uv))

def case_parts(x, z, yaw=0.0, depth=0.085, W=0.179, Hc=0.268, floor=0.0125):
    """custodia acrilica del fumetto: base nera, frontale con la foto rettificata, pannelli trasparenti e spigoli chiari; ritorna (parti, immagini)"""
    R = _roty(yaw)
    def T(px, py, pz): return np.array([x, Y0, z]) + R @ np.array([px, py, pz])           # locale: x verso l'interno della stanza = -x, py su, pz lungo la console
    parts = []; imgs = {}
    base = Mesh()
    hx, hz = depth / 2 + 0.003, W / 2 + 0.0015
    pts = lambda sx, sy, sz: T(sx * hx, sy, sz * hz)
    # base nera (scatola ruotata)
    for (a, b, c, d, col, two) in [((-1, 0, -1), (-1, 0, 1), (-1, floor, 1), (-1, floor, -1), (20, 20, 22), True), ((1, 0, -1), (1, 0, 1), (1, floor, 1), (1, floor, -1), (16, 16, 18), True),
                                   ((-1, 0, -1), (1, 0, -1), (1, floor, -1), (-1, floor, -1), (16, 16, 18), True), ((-1, 0, 1), (1, 0, 1), (1, floor, 1), (-1, floor, 1), (16, 16, 18), True),
                                   ((-1, floor, -1), (-1, floor, 1), (1, floor, 1), (1, floor, -1), (38, 38, 42), True)]:
        base.quad(pts(*a), pts(*b), pts(*c), pts(*d), col, two=True)
    parts.append(dict(name='case_base', mesh=base, map=None))
    # frontale con la foto (piano verticale a x - depth/2)
    fr = Mesh(); xf = -depth / 2; xcard = depth / 2 - 0.012           # la foto sta sul fondo della custodia, dietro alla figura
    quad_tex(fr, T(xcard, 0, -W / 2), T(xcard, 0, W / 2), T(xcard, Hc, W / 2), T(xcard, Hc, -W / 2))
    rgb = cv2.imread(f'{ASSETS}/case_front_clean.png'); rgb = cv2.resize(rgb, None, fx=0.8, fy=0.8, interpolation=cv2.INTER_AREA)
    imgs['cobj_case'] = jpg(rgb, 86); parts.append(dict(name='case_front', mesh=fr, map='cobj_case'))
    # pannelli trasparenti e spigoli
    glass = Mesh(); edges = Mesh()
    cg = (232, 238, 242)
    xb = depth / 2
    for (a, b, c, d) in [((xf, Hc, -W / 2), (xb, Hc, -W / 2), (xb, Hc, W / 2), (xf, Hc, W / 2)),               # tetto
                         ((xf, 0, -W / 2), (xb, 0, -W / 2), (xb, Hc, -W / 2), (xf, Hc, -W / 2)),               # lato sinistro (verso -z)
                         ((xf, 0, W / 2), (xb, 0, W / 2), (xb, Hc, W / 2), (xf, Hc, W / 2)),                    # lato destro
                         ((xb, 0, -W / 2), (xb, 0, W / 2), (xb, Hc, W / 2), (xb, Hc, -W / 2))]:                 # dietro
        glass.quad(T(*a), T(*b), T(*c), T(*d), cg, two=True)
    def edge(a, b, t=0.0022):
        a = np.array(a, float); b = np.array(b, float); d = b - a; L_ = np.linalg.norm(d); d /= L_
        u = np.cross(d, [0, 1, 0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0]); v = np.cross(d, u)
        for k_ in range(4):
            c0 = [(u * np.cos(np.pi / 2 * k_ + np.pi / 4) + v * np.sin(np.pi / 2 * k_ + np.pi / 4)) * t, (u * np.cos(np.pi / 2 * (k_ + 1) + np.pi / 4) + v * np.sin(np.pi / 2 * (k_ + 1) + np.pi / 4)) * t]
            edges.quad(a + c0[0], a + c0[1], b + c0[1], b + c0[0], (214, 222, 226), two=True)
    for (a, b) in [((xf, Hc, -W / 2), (xb, Hc, -W / 2)), ((xf, Hc, W / 2), (xb, Hc, W / 2)), ((xb, Hc, -W / 2), (xb, Hc, W / 2)), ((xb, 0, -W / 2), (xb, Hc, -W / 2)), ((xb, 0, W / 2), (xb, Hc, W / 2)),
                   ((xf, floor, -W / 2), (xb, floor, -W / 2)), ((xf, floor, W / 2), (xb, floor, W / 2)), ((xb, floor, -W / 2), (xb, floor, W / 2))]:
        edge(T(*a), T(*b))
    parts.append(dict(name='case_edges', mesh=edges, map=None))
    parts.append(dict(name='case_glass', mesh=glass, map=None, alpha=0.10))
    return parts, imgs

def brick_base(mesh, c, W=0.050, Dp=0.034, Hh=0.017):
    cx, y0, cz = c
    brick = (138, 70, 54); mort = (172, 146, 130)
    bands = [(0.30, brick), (0.06, mort), (0.30, brick), (0.06, mort), (0.28, brick)]
    mesh.box((cx - Dp / 2, y0, cz - W / 2), (cx + Dp / 2, y0 + Hh, cz + W / 2), {'-x': bands, '+x': brick, '-z': brick, '+z': brick, '+y': (150, 150, 156), '-y': (60, 30, 24)})

def mando_base(mesh, c, label_tex=None):
    cx, y0, cz = c
    steps = [(0.0335, 0.0, 0.0065), (0.0305, 0.0065, 0.0125), (0.0265, 0.0125, 0.0195)]
    prof = []
    for r, ya, yb in steps: prof += [(r, ya, '#141416'), (r, yb, '#1a1a1d')]
    prof += [(0.0, 0.0195, '#1c1c1f')]
    mesh.lathe((cx, y0, cz), prof, seg=36, caps=True, k=1.0)

def penny_blood(mesh, c):
    """pozza e gocce di sangue della base: lastra sottile sul piano che arriva al bordo, velo e gocce sul fronte della console"""
    cx, y0, cz = c; red = (84, 8, 16); hi = (140, 26, 34); dark = (58, 4, 10)
    x_edge = 6.86
    W = 0.052
    mesh.box((x_edge, y0, cz - W / 2), (x_edge + 0.050, y0 + 0.003, cz + W / 2), {'+y': red, '-x': dark, '+x': dark, '-z': dark, '+z': dark})
    mesh.box((x_edge - 0.0015, y0 - 0.012, cz - W / 2 + 0.002), (x_edge, y0 + 0.003, cz + W / 2 - 0.002), {'-x': dark, '+x': dark, '-y': dark, '+y': red, '-z': dark, '+z': dark})
    for (dz, ln, w) in [(-0.021, 0.026, 0.0034), (-0.010, 0.020, 0.0030), (0.002, 0.030, 0.0036), (0.012, 0.016, 0.0030), (0.021, 0.024, 0.0034), (-0.002, 0.012, 0.0024)]:
        mesh.box((x_edge - 0.0030, y0 - 0.012 - ln, cz + dz - w / 2), (x_edge - 0.0010, y0 - 0.011, cz + dz + w / 2), {'-x': hi, '+x': dark, '-y': red, '-z': dark, '+z': dark, '+y': dark})

def build(case_yaw=0.0):
    """tutte le parti degli oggetti sopra la console: lista di dict(name, mesh, map, amap, atest, alpha) e le immagini (jpeg) per il pacchetto"""
    parts = []; imgs = {}
    # figure a rilievo
    for name, x, z, y, kw in [('art', POS['art'][0], POS['art'][1], Y0, {}), ('pw', POS['pw'][0], POS['pw'][1], Y0 + 0.003, dict(height_m=0.098, az_deg=-22.0)),
                              ('mando', POS['mando'][0], POS['mando'][1], Y0 + 0.0195, dict(az_deg=-6.0))]:
        p, im, ppm = relief_part(name, x, z, y=y, **kw); parts.append(p); imgs.update(im)
    # custodia + figura Daredevil
    xc, zc = POS['case']
    cp, ci = case_parts(xc, zc, yaw=case_yaw); parts += cp; imgs.update(ci)
    R = _roty(case_yaw)
    def W3(px, py, pz): return np.array([xc, Y0, zc]) + R @ np.array([px, py, pz])
    xfig = W3(-0.0425 + 0.030, 0, 0)[0]
    p, im, ppm = relief_part('dd', xfig, zc - 0.0075, y=Y0 + 0.0290, R=0.02, height_m=0.0915, az_deg=10.0); parts.append(p); imgs.update(im)
    # il resto: oggetti a colori per vertice in una mesh sola
    misc = Mesh()
    lamp(misc, (POS['lamp'][0], Y0, POS['lamp'][1]))
    camera(misc, (POS['camera'][0], Y0, POS['camera'][1]))
    dish(misc, (POS['dish'][0], Y0, POS['dish'][1]))
    mando_base(misc, (POS['mando'][0], Y0, POS['mando'][1]))
    penny_blood(misc, (POS['pw'][0], Y0, POS['pw'][1]))
    c3 = W3(-0.0425 + 0.030, 0.0125, -0.0075); brick_base(misc, (c3[0], c3[1], c3[2]), W=0.050, Hh=0.0165)
    parts.append(dict(name='misc', mesh=misc, map=None))
    # etichetta STAR WARS sul fronte della base
    import json
    lab = cv2.imread(f'{ASSETS}/mando_label.png')
    imgs['cobj_label'] = jpg(lab, 90)
    lm = Mesh(); xm, zm = POS['mando']; xl = xm - 0.0336
    quad_tex(lm, (xl, Y0 + 0.0004, zm - 0.0108), (xl, Y0 + 0.0004, zm + 0.0108), (xl, Y0 + 0.0096, zm + 0.0108), (xl, Y0 + 0.0096, zm - 0.0108))
    parts.append(dict(name='label', mesh=lm, map='cobj_label'))
    # piano in legno con le ombre di contatto (la luce arriva da sinistra/davanti: l'ombra cade verso il muro e verso +z)
    sh = [(POS['camera'][0] + 0.010, POS['camera'][1] + 0.008, 0.032, 0.030, 0.9), (POS['mando'][0] + 0.008, POS['mando'][1] + 0.006, 0.040, 0.040, 0.9),
          (POS['case'][0] + 0.012, POS['case'][1] + 0.006, 0.062, 0.100, 0.8), (POS['dish'][0] + 0.008, POS['dish'][1] + 0.006, 0.032, 0.060, 0.8),
          (POS['art'][0] + 0.010, POS['art'][1] + 0.004, 0.030, 0.034, 0.9), (POS['pw'][0] + 0.010, POS['pw'][1] + 0.004, 0.032, 0.034, 0.7), (POS['lamp'][0] + 0.004, POS['lamp'][1] + 0.003, 0.052, 0.052, 0.8)]
    tp, ti = console_top(shadows=sh); parts.append(tp); imgs.update(ti)
    return parts, imgs


def console_top(z0=2.76, z1=4.50, x0=6.86, x1=7.08, ppm=500, seed=11, shadows=()):
    """piano della console: legno scuro rustico con venature lungo z, fascia piu' chiara verso il bordo anteriore e ombre di contatto morbide.
    shadows: lista di (x, z, rx, rz, forza) ellissi d'ombra sul piano. Ritorna (parte, immagini)"""
    Wz = int(round((z1 - z0) * ppm)); Hx = int(round((x1 - x0) * ppm))
    rng = np.random.RandomState(seed)
    # venature: rumore molto allungato lungo z (le colonne dell'immagine vanno con z, le righe con x)
    g1 = cv2.resize(rng.rand(Hx // 3 + 2, Wz // 60 + 2).astype(np.float32), (Wz, Hx), interpolation=cv2.INTER_CUBIC)
    g2 = cv2.resize(rng.rand(Hx // 1 + 2, Wz // 14 + 2).astype(np.float32), (Wz, Hx), interpolation=cv2.INTER_CUBIC)
    g3 = cv2.resize(rng.rand(Hx // 8 + 2, Wz // 220 + 2).astype(np.float32), (Wz, Hx), interpolation=cv2.INTER_CUBIC)
    g = 0.45 * g1 + 0.25 * g2 + 0.30 * g3; g = (g - g.min()) / (g.max() - g.min())
    base = np.array([52.0, 34.0, 24.0]); dark = np.array([42.0, 27.0, 19.0]); light = np.array([68.0, 45.0, 31.0])
    t = (g - 0.5) * 2.0
    col = np.where(t[..., None] >= 0, base * (1 - t[..., None]) + light * t[..., None], base * (1 + t[..., None]) + dark * (-t[..., None]))
    # assi del piano: righe = x (0 = fronte, bordo anteriore), colonne = z
    xx = (np.arange(Hx) / max(1, Hx - 1))[:, None] * np.ones((1, Wz))
    col *= (1.0 + 0.16 * np.exp(-((xx - 0.05) / 0.10) ** 2))[..., None]            # fascia lucida lungo il bordo anteriore
    col *= (0.96 + 0.06 * (1 - xx))[..., None]
    # giunture delle assi (due linee scure lungo z) e qualche nodo
    for fr in (0.34, 0.68):
        r0 = int(fr * Hx); col[max(0, r0 - 1):r0 + 1, :, :] *= 0.55
    sh = np.zeros((Hx, Wz), np.float32)
    for (sx, sz, rx, rz, f) in shadows:
        cr = (sx - x0) * ppm; cc = (sz - z0) * ppm
        yy, zz = np.mgrid[0:Hx, 0:Wz]
        sh = np.maximum(sh, f * np.exp(-(((yy - cr) / (rx * ppm)) ** 2 + ((zz - cc) / (rz * ppm)) ** 2) ** 1.0))
    sh = cv2.GaussianBlur(sh, (0, 0), 0.004 * ppm)
    col *= (1 - 0.55 * np.clip(sh, 0, 1))[..., None]
    img = np.clip(col, 0, 255).astype(np.uint8)[..., ::-1]
    m = Mesh(); y = Y0 + 0.0004
    # u = z (0 a z0, 1 a z1), v = x invertito: la riga 0 (fronte) in cima all'immagine -> v = 1 sul fronte
    quad_tex(m, (x0, y, z0), (x0, y, z1), (x1, y, z1), (x1, y, z0), uv=((0, 1), (1, 1), (1, 0), (0, 0)))
    return dict(name='top', mesh=m, map='cobj_top'), {'cobj_top': jpg(img, 84)}
