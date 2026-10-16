"""Finestra della parete W (z 0,73-1,63 m): texture nitide e DRITTE dalla foto frontale dell'utente (non registrata, 25d46ef1), al posto della finestra sfocata cotta nel muro.

Perche' era sfocata: il telaio sta 12 cm dietro il filo del muro e le foto registrate lo vedono da 5-7 m con pose diverse, quindi cotte sul piano del muro finiscono sdoppiate.
Qui il telaio si rifa su un piano suo (x = 7,10 + 0,12) con la foto frontale; le spalle (rivestimento in ottone, svasate: l'apertura nel muro e' piu' larga del telaio) sono quattro facce piane
campionate dalla stessa foto con omografie esatte dei loro quadrilateri.

Come si raddrizza (la prima versione usava un riferimento cotto da una foto registrata e un ECC: veniva fuori leggermente storta e asimmetrica, 1-2 cm di scivolamento):
 1. foto senza distorsione radiale (f = 3024,6, k1 = 0,0276);
 2. otto angoli dei vetri letti a mano nella foto ingrandita (due vetri: sinistro TL TR BR BL, destro TL TR BR BL);
 3. omografia foto -> riquadro ideale: due vetri UGUALI, simmetrici attorno all'asse centrale, con bordo alto e basso allineati (un telaio vero e' cosi'); si cercano insieme l'omografia e la geometria
    del riquadro (distanza fra i vetri g; l'altezza h, in unita' di larghezza del vetro, non e' ricavabile dai soli angoli: la si trova col vincolo di K, cioe' con le colonne della rotazione
    ortonormali). Risultato: residuo di 1 px sugli 8 angoli (la finestra e' davvero simmetrica), h = 4,359, camera a 2,35 m dal telaio, 11 cm a destra dell'asse; con h giusta le colonne tornano
    ortonormali entro 0,03% (norme 0,13790 e 0,13787);
 4. scala metrica: 0,329 m per unita' (larghezza del vetro): da altezza del vetro nel riferimento registrato (1,436 m / 4,359) e da larghezza dell'apertura (0,906 m / 2,76 unita'); posizione dall'asse
    z = 1,178 e dal bordo basso dei vetri y = 0,995 (letti nelle foto registrate);
 5. contorno del telaio (faccia esterna) = rettangolo X +-1,26, Y da -0,05 a 4,466 (unita' del riquadro; letto sugli angoli in alto, simmetrico entro 0,006 unita');
    apertura nel muro: i quattro angoli esterni delle spalle (a mano), riportati sul piano del muro con la camera: z 0,726-1,630, y 0,925-2,466, centrata e dritta entro 5 mm;
 6. texture del telaio: la foto rimappata sul rettangolo, a 800 px/m; il riflesso del fotografo (e del vaso) nei vetri si copre con la griglia a persiane copiata da 9 stecche sopra;
 7. spalle: per ogni faccia (alto, basso, sinistra, destra) il quadrilatero fra l'apertura (angoli a mano, un po' verso l'interno) e il contorno del telaio e' raddrizzato su una striscia.
Uso: FOTO_DIR=... python3 win_prep.py  ->  WIN_ASSETS/frame_clean.png e lining_atlas.png (e i numeri da riportare in reg/win_obj.py)"""
import os, sys, numpy as np, cv2
from scipy.optimize import least_squares, brentq
OUT = os.environ.get('WIN_ASSETS', '/tmp/claude-0/s/st3/assets/win'); os.makedirs(OUT, exist_ok=True)
UND = os.environ.get('UND_NEW', '/tmp/claude-0/s/st3/und_new'); os.makedirs(UND, exist_ok=True)
PID = '25d46ef1'
K = np.array([[3024.6, 0, 1152], [0, 3024.6, 2048], [0, 0, 1.0]])
# angoli dei vetri (foto non distorta, px): sinistro TL TR BR BL; destro TL TR BR BL
PH = np.array([[645.5, 382.7], [1090.0, 364.6], [1110.0, 2283.3], [700.0, 2285.0], [1222.5, 357.5], [1675.8, 342.0], [1659.7, 2279.7], [1240.0, 2283.3]], float)
WQ = np.array([[513.3, 259.3], [1806.7, 201.7], [1783.3, 2399.3], [576.7, 2410.0]], float)      # angoli esterni delle spalle sul filo del muro: TL TR BR BL
S = 0.329                                      # metri per unita' del riquadro (= larghezza di un vetro)
XF, YF0, YF1 = 1.26, -0.05, 4.466              # contorno del telaio (faccia esterna) nel riquadro
D = 0.12                                       # il telaio sta 12 cm dietro il filo del muro
PPM = 800; PPM_L = 700; EPS = 0.025            # px/m del telaio e delle spalle; le spalle si campionano un po' verso l'interno del bordo con l'intonaco

def undistort():
    p = f'{UND}/{PID}.png'
    if os.path.exists(p): return cv2.imread(p)
    im = cv2.imread(f"{os.environ['FOTO_DIR']}/{PID}-image.jpg"); h, w = im.shape[:2]; Kp = np.array([[3024.6, 0, w / 2], [0, 3024.6, h / 2], [0, 0, 1.0]])
    u = cv2.undistort(im, Kp, np.array([0.0276, 0, 0, 0], float), None, Kp); cv2.imwrite(p, u); return u

def layout(g, h):
    return np.array([(-(1 + g), h), (-g, h), (-g, 0), (-(1 + g), 0), (g, h), (1 + g, h), (1 + g, 0), (g, 0)], float)
def hom(p): return np.array([[p[0], p[1], p[2]], [p[3], p[4], p[5]], [p[6], p[7], 1.0]])
def apply(H, P):
    Q = np.c_[P, np.ones(len(P))] @ H.T; return Q[:, :2] / Q[:, 2:3]
def fit_h(h):
    def res(x): return ((apply(hom(x[:8]), PH) - layout(x[8], h)) * 430.0).ravel()
    T0 = layout(0.15, h); H0, _ = cv2.findHomography(PH.astype(np.float32), T0.astype(np.float32), 0); x0 = np.r_[(H0 / H0[2, 2]).ravel()[:8], 0.15]
    r = least_squares(res, x0, method='lm', x_scale='jac'); return hom(r.x[:8]), float(r.x[8]), float(np.sqrt((r.fun ** 2).mean()))
def norm_ratio(h):
    H, g, _ = fit_h(h); M = np.linalg.inv(H); M /= M[2, 2]; A = np.linalg.inv(K) @ M; return np.linalg.norm(A[:, 0]) / np.linalg.norm(A[:, 1]) - 1
def solve():
    h = brentq(norm_ratio, 3.8, 5.0, xtol=1e-4); H, g, rms = fit_h(h); return H, g, h, rms
def camera(H):
    M = np.linalg.inv(H); M /= M[2, 2]; A = np.linalg.inv(K) @ M; lam = 1 / np.linalg.norm(A[:, 0]); r1 = lam * A[:, 0]; r2 = lam * A[:, 1]; t = lam * A[:, 2]
    if t[2] < 0: r1, r2, t = -r1, -r2, -t
    R = np.stack([r1, r2, np.cross(r1, r2)], 1); U, _, Vt = np.linalg.svd(R); R = U @ Vt; return R, t, -R.T @ t

def frame_texture(ph, H):
    U = S * PPM; w = int(round(2 * XF * U)); hh = int(round((YF1 - YF0) * U))
    xs = -XF + (np.arange(w) + 0.5) / U; ys = YF1 - (np.arange(hh) + 0.5) / U; X, Y = np.meshgrid(xs, ys)
    p = np.linalg.inv(H) @ np.stack([X.ravel(), Y.ravel(), np.ones(X.size)]); u = (p[0] / p[2]).reshape(X.shape).astype(np.float32); v = (p[1] / p[2]).reshape(X.shape).astype(np.float32)
    return cv2.remap(ph, u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def clean_reflections(src):
    """il fotografo e il vaso si riflettono nei vetri in basso: si coprono con la stessa zona 9 stecche (339 px a 800 px/m) piu' su (le stecche e le barre della grata si ripetono ogni 3 stecche)"""
    out = src.astype(np.float32).copy(); SH = 339
    def fill(x0, x1, y0, y1, ft=30, fb=8, fs=5):
        h, w = y1 - y0, x1 - x0; patch = src[y0 - SH:y1 - SH, x0:x1].astype(np.float32); al = np.ones((h, w), np.float32)
        al[:ft] *= np.linspace(0, 1, ft)[:, None]; al[-fb:] *= np.linspace(1, 0, fb)[:, None]; al[:, :fs] *= np.linspace(0, 1, fs)[None, :]; al[:, -fs:] *= np.linspace(1, 0, fs)[None, :]
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - al[..., None]) + patch * al[..., None]
    fill(34, 288, 880, 1172); fill(376, 630, 880, 1150, fb=60)
    return np.clip(out, 0, 255).astype(np.uint8)

def deglare(tex, win=301, lo=1.25, hi=1.75, lift=1.25):
    """riflessi (la luce che scivola sull'ottone, nella foto fino a bianco pieno) non sono una proprieta' della spalla ma del punto di vista: dove la luminosita' supera di molto quella
    della striscia (mediana lungo la striscia, per canale: cosi' resta il colore dell'ottone) si sostituisce con quel colore, un po' schiarito"""
    from scipy.ndimage import median_filter
    f = tex.astype(np.float32); B = np.stack([median_filter(f[..., c], size=(1, win), mode='nearest') for c in range(3)], -1)
    V = f.max(axis=2); BV = np.maximum(B.max(axis=2), 1.0); m = np.clip((V - lo * BV) / ((hi - lo) * BV), 0, 1); m = cv2.GaussianBlur(m, (0, 0), 3.0)[..., None]
    return np.clip(f * (1 - m) + B * lift * m, 0, 255).astype(np.uint8)

def strip_plaster(tex):
    """oltre il bordo vero dell'apertura (le letture a mano scostano 1-2 mm) la camera campiona intonaco (grigio chiaro poco saturo, mai bruciato): dalla prima riga d'intonaco in poi si prolunga l'ultimo colore d'ottone"""
    hsv = cv2.cvtColor(tex, cv2.COLOR_BGR2HSV); pl = ((hsv[..., 1] < 30) & (hsv[..., 2] > 150) & (hsv[..., 2] < 228)).astype(np.uint8)
    pl = cv2.medianBlur(pl * 255, 5) > 0; out = tex.copy(); h, w = pl.shape; r0 = int(0.55 * h)           # solo nella parte vicina al muro
    for x in range(w):
        col = pl[:, x]; r = None
        for k in range(r0, h - 2):
            if col[k] and col[k + 1] and col[k + 2]: r = k; break
        if r is not None:
            ref = tex[max(0, r - 5):max(1, r - 2), x].astype(np.float32).mean(0); out[r - 1:, x] = ref.astype(np.uint8)
    return cv2.GaussianBlur(out, (1, 5), 0)

def lining_atlas(ph, H):
    """quattro facce svasate: ognuna e' il quadrilatero fra il contorno del telaio (riga 0) e l'apertura nel muro (ultima riga), raddrizzato con la sua omografia"""
    F = apply(np.linalg.inv(H), np.array([(-XF, YF1), (XF, YF1), (XF, YF0), (-XF, YF0)]))              # TL TR BR BL del telaio, nella foto
    W = WQ + EPS * (F - WQ)                                                                           # apertura, un po' verso l'interno
    nd = int(round(D * PPM_L)); PADR = 2; n_top = int(round(0.87 * PPM_L)); n_side = int(round(1.505 * PPM_L))
    faces = [('top', n_top, F[[0, 1]], W[[0, 1]]), ('bottom', n_top, F[[3, 2]], W[[3, 2]]), ('left', n_side, F[[3, 0]], W[[3, 0]]), ('right', n_side, F[[2, 1]], W[[2, 1]])]
    aw = max(f[1] for f in faces); at = np.zeros(((nd + PADR) * 4, aw, 3), np.uint8); lay = {}
    for i, (name, n, fr, wl) in enumerate(faces):
        src = np.float32([fr[0], fr[1], wl[1], wl[0]]); dst = np.float32([[0, 0], [n, 0], [n, nd], [0, nd]])
        tex = strip_plaster(deglare(cv2.warpPerspective(ph, cv2.getPerspectiveTransform(src, dst), (n, nd), flags=cv2.INTER_CUBIC)))
        r0 = i * (nd + PADR); at[r0:r0 + nd, :n] = tex; at[r0 + nd:r0 + nd + PADR, :n] = tex[-1:]; lay[name] = (r0, nd, n)
    return at, lay, F

if __name__ == '__main__':
    ph = undistort(); H, g, h, rms = solve(); R, t, C = camera(H); np.save(f'{OUT}/Hg.npy', H)
    print('g %.4f  h %.4f  residuo %.2f px  camera (unita) %s  (m: %s)' % (g, h, rms, np.round(C, 3), np.round(C * S, 3)))
    print('angoli dei vetri nel riquadro:', np.round(apply(H, PH), 3).tolist())
    tex = clean_reflections(frame_texture(ph, H)); cv2.imwrite(f'{OUT}/frame_clean.png', tex); print('telaio', tex.shape)
    at, lay, F = lining_atlas(ph, H); cv2.imwrite(f'{OUT}/lining_atlas.png', at); print('atlante spalle', at.shape, lay); print('contorno del telaio nella foto', np.round(F, 1).tolist())
