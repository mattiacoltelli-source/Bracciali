"""Posa della foto del corridoio (3d4294a2, non registrata nel modello): PnP sugli angoli dell'arco (parete TV, z = 0) e su tre punti della stessa parete letti in una foto registrata (b4bfa2ec: targa nera a
tre moduli e termostato, che stanno a destra dell'arco). Ricava anche l'altezza dell'arco. Salva work/pose3b_3d4294a2.npy (rvec, tvec, h, x0, x1, centro camera) usato da corr_prep.py.
Le coordinate in pixel sono lette a mano sulla foto non distorta (und_new/3d4294a2.png, K con f = 3024,6 e k1 = 0,0276). La foto e' verticale (2304 x 4096): punto principale (1152, 2048)."""
import sys, os, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/s/reg')
from scipy.optimize import least_squares
K = np.array([[3024.6, 0, 1152], [0, 3024.6, 2048], [0, 0, 1.0]])
ARCH_PX = {'TL': (46, 237), 'TR': (2064, 413), 'BL': (270, 3825), 'BR': (1893, 3495)}      # angoli dell'arco sul filo della parete TV
FEAT_PX = {'plate_TL': (2250, 1725), 'plate_BL': (2243.8, 1859), 'th_TL': (2223, 1310)}      # angolo alto-sinistra e basso-sinistra della targa nera, alto-sinistra del termostato
FEAT_B4 = {'plate_TL': (1921.7, 1093.8), 'plate_BL': (1922.9, 1159.2), 'th_TL': (1882.5, 901.3)}   # gli stessi punti in b4bfa2ec (4096 x 2304)
def wall_points():
    import phototex as PT
    cam = PT.Cam('b4bfa2ec'); out = {}
    for k, (u, v) in FEAT_B4.items():
        d_cam = np.array([(u - cam.cx) / cam.f, (v - cam.cy) / cam.f, 1.0]); d = np.linalg.solve(cam.V[:3, :3], d_cam); d /= np.linalg.norm(d)
        t = (0.0 - cam.C[2]) / d[2]; out[k] = cam.C + t * d            # intersezione col piano della parete TV (z = 0)
    return out
def fit(x0=0.46, x1=1.53):
    W3 = wall_points()
    def project(rv, tv, X): q, _ = cv2.projectPoints(np.array([X], float), rv, tv, K, None); return q[0, 0]
    def res(p):
        rv, tv, h = p[:3], p[3:6], p[6]
        P = {'TL': (x0, h, 0), 'TR': (x1, h, 0), 'BL': (x0, 0, 0), 'BR': (x1, 0, 0)}; r = []
        for k, uv in ARCH_PX.items(): q = project(rv, tv, P[k]); r += [q[0] - uv[0], q[1] - uv[1]]
        for k, uv in FEAT_PX.items(): q = project(rv, tv, W3[k]); r += [q[0] - uv[0], q[1] - uv[1]]
        return np.array(r)
    best = None
    for z0 in (1.0, 1.5, 2.0, 2.5):
        rv0 = np.array([np.pi, 0, 0.0]); R0, _ = cv2.Rodrigues(rv0); t0 = -R0 @ np.array([1.0, 1.5, z0])
        s = least_squares(res, np.concatenate([rv0, t0, [2.0]]))
        if best is None or s.cost < best.cost: best = s
    p = best.x; R, _ = cv2.Rodrigues(p[:3]); C = -R.T @ p[3:6]
    print('camera', C.round(3), 'altezza arco', round(p[6], 3), 'rms px', np.sqrt(np.mean(best.fun ** 2)).round(1))
    return np.concatenate([p, [x0, x1], C])
if __name__ == '__main__':
    out = fit(); os.makedirs('work', exist_ok=True); np.save('work/pose3b_3d4294a2.npy', out)
