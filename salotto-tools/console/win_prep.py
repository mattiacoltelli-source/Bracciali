"""Finestra della parete W (z 0,72-1,63 m): texture nitide dalla foto frontale dell'utente (non registrata, 25d46ef1), al posto della finestra sfocata cotta nel muro.

Perche' era sfocata: il telaio sta 13 cm dietro il filo del muro e le foto registrate lo vedono da 5-7 m con pose diverse, quindi cotte sul piano del muro finiscono sdoppiate.
Qui il telaio si rifa su un piano suo (x = 7,10 + 0,13) con la foto frontale, e le spalle (rivestimento in ottone) si campionano dalla stessa foto.

Passi (tutto riproducibile; servono FOTO_DIR e le pose in reg/poses_room.json):
 1. foto senza distorsione radiale (f = 3024,6, k1 = 0,0276);
 2. riferimento metrico: il piano del telaio (a 0,13 m dietro il muro: lo sweep win_sweep.py cerca la profondita' dove le foto registrate concordano di piu') cotto da UNA foto registrata (36b5d801);
 3. omografia foto -> riferimento: 6 angoli dei vetri a mano (H0), poi ECC sulle mappe di 'ottone' (H1: ignora riflessi e quello che si vede dai vetri);
 4. camera della foto frontale dalla decomposizione dell'omografia (con K: colonne ortonormali entro l'1%: la f e' quella giusta); controllo: gli angoli dell'apertura, riportati sul piano del muro,
    danno bordi orizzontali concordi a 5 mm e verticali a 2 cm: apertura z 0,725-1,631, y 0,9225-2,466;
 5. texture del telaio: la foto rimappata sul rettangolo dell'apertura a 800 px/m; il riflesso del fotografo (e del vaso) nei vetri si copre con la griglia a persiane copiata da 9 stecche sopra;
 6. spalle: quattro strisce campionate dalla foto con la camera (alto, basso, sinistra, destra), in un atlante.
Uso: FOTO_DIR=... python3 win_prep.py  ->  WIN_ASSETS/frame_clean.png e lining_atlas.png"""
import os, sys, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/s/reg')
OUT = os.environ.get('WIN_ASSETS', '/tmp/claude-0/s/st3/assets/win'); os.makedirs(OUT, exist_ok=True)
UND = os.environ.get('UND_NEW', '/tmp/claude-0/s/st3/und_new'); os.makedirs(UND, exist_ok=True)
PID = '25d46ef1'; REF_PID = '36b5d801'
X_WALL = 7.10; D = 0.13                                              # filo del muro e profondita' del telaio
HOLE = dict(z0=0.725, z1=1.631, y0=0.9225, y1=2.466)                # apertura nel muro (m)
K = np.array([[3024.6, 0, 1152], [0, 3024.6, 2048], [0, 0, 1.0]])
REF = dict(z0=0.60, z1=1.90, y0=0.80, y1=2.65, ppm=500)
S = np.array([[1 / 500, 0, 0.60], [0, -1 / 500, 2.65], [0, 0, 1.0]])   # px del riferimento -> (z, y) in metri
PPM = 800; PPM_L = 700
# 6 angoli dei vetri: foto (px) -> riferimento (px a 500 px/m)
PH_PTS = np.float32([[646, 382], [1090, 394], [1110, 2282], [694, 2284], [1242, 2284], [1660, 2278]])
REF_PTS = np.float32([[108, 107], [271, 103], [259, 825], [98, 825], [312, 828], [480, 828]])

def undistort():
    p = f'{UND}/{PID}.png'
    if os.path.exists(p): return cv2.imread(p)
    im = cv2.imread(f"{os.environ['FOTO_DIR']}/{PID}-image.jpg"); h, w = im.shape[:2]; Kp = np.array([[3024.6, 0, w / 2], [0, 3024.6, h / 2], [0, 0, 1.0]])
    u = cv2.undistort(im, Kp, np.array([0.0276, 0, 0, 0], float), None, Kp); cv2.imwrite(p, u); return u

def reference():
    import phototex as PT
    cam = PT.Cam(REF_PID); r = REF
    zs = np.arange(r['z0'], r['z1'], 1 / r['ppm']) + 0.5 / r['ppm']; ys = np.arange(r['y1'], r['y0'], -1 / r['ppm']) - 0.5 / r['ppm']
    Z, Y = np.meshgrid(zs, ys); P = np.stack([np.full_like(Z, X_WALL + D), Y, Z], -1); N = np.zeros_like(P); N[..., 0] = -1.0
    img, _ = PT.bake(P, N, [cam], power=3.0, min_cos=0.12, kill_highlights=False); return np.clip(img, 0, 255).astype(np.uint8)

def bronze(bgr, sig):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32); h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = np.clip((s - 40) / 40.0, 0, 1) * np.clip((v - 45) / 40.0, 0, 1) * ((h > 8) & (h < 38))
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), sig)

def homography(ref, ph):
    H0, _ = cv2.findHomography(PH_PTS, REF_PTS, 0)
    w0 = cv2.warpPerspective(ph, H0, (ref.shape[1], ref.shape[0]), flags=cv2.INTER_AREA)
    W = np.eye(3, dtype=np.float32); crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 400, 1e-7)
    cc, W = cv2.findTransformECC(bronze(ref, 1.5), bronze(w0, 3.0), W, cv2.MOTION_HOMOGRAPHY, crit, None, 5)
    print('ECC cc', round(float(cc), 3)); return np.linalg.inv(W) @ H0

class Cam:
    """camera della foto frontale nel sistema del piano del telaio: X = z stanza, Y = y, Z verso la stanza (Z = D e' il filo del muro)"""
    def __init__(s, H):
        s.G = S @ H; s.G /= s.G[2, 2]; M = np.linalg.inv(s.G); M /= M[2, 2]; A = np.linalg.inv(K) @ M
        lam = 1 / np.linalg.norm(A[:, 0]); r1 = lam * A[:, 0]; r2 = lam * A[:, 1]; t = lam * A[:, 2]
        if t[2] < 0: r1, r2, t = -r1, -r2, -t
        R = np.stack([r1, r2, np.cross(r1, r2)], 1); U, _, Vt = np.linalg.svd(R); s.R, s.t = U @ Vt, t; s.C = -s.R.T @ t; s.M = M
        print('camera nel sistema del piano', np.round(s.C, 3), '| ortogonalita', round(abs(float(r1 @ r2)), 3), 'rapporto norme', round(float(np.linalg.norm(A[:, 0]) / np.linalg.norm(A[:, 1])), 3))
    def project(s, P):
        P = np.asarray(P, float).reshape(-1, 3); c = (s.R @ P.T).T + s.t; p = (K @ c.T).T; return (p[:, :2] / p[:, 2:3])

def frame_texture(ph, cam):
    z0, z1, y0, y1 = (HOLE[k] for k in ('z0', 'z1', 'y0', 'y1')); w = int(round((z1 - z0) * PPM)); h = int(round((y1 - y0) * PPM))
    xs = z0 + (np.arange(w) + 0.5) / PPM; ys = y1 - (np.arange(h) + 0.5) / PPM; X, Y = np.meshgrid(xs, ys)
    p = cam.M @ np.stack([X.ravel(), Y.ravel(), np.ones(X.size)]); u = (p[0] / p[2]).reshape(X.shape).astype(np.float32); v = (p[1] / p[2]).reshape(X.shape).astype(np.float32)
    return cv2.remap(ph, u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def clean_reflections(src):
    """il fotografo e il vaso si riflettono nei vetri in basso: si coprono con la stessa zona 9 stecche (339 px a 800 px/m) piu' su (le stecche e le barre della grata si ripetono ogni 3 stecche)"""
    out = src.astype(np.float32).copy(); SH = 339
    def fill(x0, x1, y0, y1, ft=26, fb=8, fs=5):
        h, w = y1 - y0, x1 - x0; patch = src[y0 - SH:y1 - SH, x0:x1].astype(np.float32); al = np.ones((h, w), np.float32)
        al[:ft] *= np.linspace(0, 1, ft)[:, None]; al[-fb:] *= np.linspace(1, 0, fb)[:, None]; al[:, :fs] *= np.linspace(0, 1, fs)[None, :]; al[:, -fs:] *= np.linspace(1, 0, fs)[None, :]
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - al[..., None]) + patch * al[..., None]
    fill(62, 312, 905, 1196); fill(404, 662, 905, 1100, fb=50)
    return np.clip(out, 0, 255).astype(np.uint8)

def lining_atlas(ph, cam):
    """spalle: 4 strisce (alto, basso, sinistra, destra), riga 0 = lato telaio, ultima riga = filo del muro"""
    z0, z1, y0, y1 = (HOLE[k] for k in ('z0', 'z1', 'y0', 'y1')); nd = int(round(D * PPM_L)); PADR = 2
    faces = {'top': (int(round((z1 - z0) * PPM_L)), lambda s, d: (z0 + s * (z1 - z0), y1, D * d)), 'bottom': (int(round((z1 - z0) * PPM_L)), lambda s, d: (z0 + s * (z1 - z0), y0, D * d)),
             'left': (int(round((y1 - y0) * PPM_L)), lambda s, d: (z0, y0 + s * (y1 - y0), D * d)), 'right': (int(round((y1 - y0) * PPM_L)), lambda s, d: (z1, y0 + s * (y1 - y0), D * d))}
    aw = max(f[0] for f in faces.values()); at = np.zeros(((nd + PADR) * 4, aw, 3), np.uint8); lay = {}
    for i, (name, (n, fn)) in enumerate(faces.items()):
        ss = (np.arange(n) + 0.5) / n; dd = (np.arange(nd) + 0.5) / nd; S_, D_ = np.meshgrid(ss, dd)
        pts = np.stack([np.stack(fn(s, d)) for s, d in zip(S_.ravel(), D_.ravel())]); uv = cam.project(pts).reshape(S_.shape + (2,))
        tex = cv2.remap(ph, uv[..., 0].astype(np.float32), uv[..., 1].astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        tex = strip_plaster(tex)
        r0 = i * (nd + PADR); at[r0:r0 + nd, :n] = tex; at[r0 + nd:r0 + nd + PADR, :n] = tex[-1:]; lay[name] = (r0, nd, n)
    return at, lay

def strip_plaster(tex):
    """oltre il bordo vero dell'apertura (che non e' un rettangolo perfetto: i bordi si scostano di 1-2 cm) la camera campiona intonaco: dalla prima riga di intonaco in poi si prolunga l'ultimo colore d'ottone"""
    hsv = cv2.cvtColor(tex, cv2.COLOR_BGR2HSV); pl = ((hsv[..., 1] < 42) & (hsv[..., 2] > 110)).astype(np.uint8)
    pl = cv2.medianBlur(pl * 255, 5) > 0; out = tex.copy(); h, w = pl.shape
    for x in range(w):
        col = pl[:, x]; r = None
        for k in range(3, h - 2):
            if col[k] and col[k + 1] and col[k + 2]: r = k; break
        if r is not None:
            ref = tex[max(0, r - 5):max(1, r - 2), x].astype(np.float32).mean(0); out[r - 1:, x] = ref.astype(np.uint8)
    return cv2.GaussianBlur(out, (1, 5), 0)

if __name__ == '__main__':
    ph = undistort(); ref = reference(); cv2.imwrite(f'{OUT}/ref.png', ref)
    H = homography(ref, ph); np.save(f'{OUT}/H1.npy', H); cam = Cam(H)
    pk = {'TL': (513.3, 259.3), 'TR': (1806.7, 201.7), 'BR': (1783.3, 2399.3), 'BL': (576.7, 2410.0)}      # angoli esterni delle spalle (a mano nella foto)
    Ki = np.linalg.inv(K)
    for k, (u, v) in pk.items():
        d = cam.R.T @ (Ki @ np.array([u, v, 1.0])); P = cam.C + (D - cam.C[2]) / d[2] * d; print('angolo', k, 'z %.3f y %.3f' % (P[0], P[1]))
    tex = clean_reflections(frame_texture(ph, cam)); cv2.imwrite(f'{OUT}/frame_clean.png', tex)
    at, lay = lining_atlas(ph, cam); cv2.imwrite(f'{OUT}/lining_atlas.png', at); print('atlante spalle', at.shape, lay)
