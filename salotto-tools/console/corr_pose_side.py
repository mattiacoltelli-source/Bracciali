"""Posa di una foto del corridoio vista di lato, da destra attraverso l'arco (foto C dell'utente, 2304 x 4096, non registrata), e posizione della porta sul muro sinistro.
Foto non distorta come in `corr_prep.py` (f = 3024,6, k1 = 0,0276); i pixel sono letti a mano su ritagli con griglia (`corr2/pickgrid.py`).
1) PnP sui punti vicini: angoli alto dell'imbotte a sinistra (z = 0 e z = -0,40, quota 1,989), il suo piede al battiscopa e la targa nera della parete TV (coordinate dalla foto registrata).
2) Le sole misure vicine non bastano per il campo lontano (muro sinistro a 3 m): si aggiungono lo spigolo fra muro sinistro e muro di fondo (x = 0,02, z = -1,40; il punto al battiscopa e la retta verticale) e il bordo
   destro della cornice della porta (retta verticale sul muro sinistro con z incognita). Esce zR = -1,23 .. -1,25 e quota della cornice 1,92 (come la porta di fondo, 1,93).
La posa non e' perfetta (rms 25 px su 2304 x 4096): la porta e' posizionata a +-3 cm. Il lato verso l'arco della cornice sta dietro lo stipite nella foto: la foglia e' larga come quella di fondo.
Uso: python3 corr_pose_side.py  ->  stampa camera, zR e la quota; salva poseC2.npy"""
import numpy as np, cv2
from scipy.optimize import least_squares
K = np.array([[3024.6, 0, 1152], [0, 3024.6, 2048], [0, 0, 1.0]])
X0, YA, D = 0.46, 1.989, 0.40
XL, ZF = 0.02, -1.40
NEAR = [((X0, YA, 0.0), (887, 530)), ((X0, YA, -D), (1342, 603)), ((X0, 'hb', 0.0), (928, 3043)), ((X0, 'hb', -D), (1303, 2954)), ((1.695, 1.26, 0.0), (2233, 1832)), ((1.693, 1.17, 0.0), (2224, 2041))]
CORNER_PT = ((XL, 'hb', ZF), (1700, 2495))
CORNER_LINE = [(1755, 800), (1741, 1250), (1728, 1700), (1714, 2100)]
DOOR_EDGE = [(1667, 872), (1650, 1250), (1630, 1680), (1620, 2100), (1612, 2490)]
def proj(rv, tv, P): q, _ = cv2.projectPoints(np.array([P], float), rv, tv, K, None); return q[0, 0]
def line_dist(rv, tv, x, z, uv, y0=0.0, y1=2.6):
    a = proj(rv, tv, (x, y0, z)); b = proj(rv, tv, (x, y1, z)); d = b - a; n = np.array([-d[1], d[0]]) / np.linalg.norm(d); return float(np.dot(np.array(uv) - a, n))
def res(p, far=0.0):
    rv, tv, hb, zR = p[:3], p[3:6], p[6], p[7]; r = []
    for P, uv in NEAR:
        q = proj(rv, tv, tuple(hb if v == 'hb' else v for v in P)); r += [q[0] - uv[0], q[1] - uv[1]]
    if far:
        P, uv = CORNER_PT; q = proj(rv, tv, tuple(hb if v == 'hb' else v for v in P)); r += [far * (q[0] - uv[0]), far * (q[1] - uv[1])]
        for uv in CORNER_LINE: r.append(far * line_dist(rv, tv, XL, ZF, uv))
        for uv in DOOR_EDGE: r.append(far * line_dist(rv, tv, XL, zR, uv))
    return np.array(r)
def start():
    best = None
    for z0 in (0.8, 1.5):
        for x0 in (2.0, 3.0):
            C0 = np.array([x0, 1.4, z0]); f = np.array([0.3, 0, -0.5]) - C0; f /= np.linalg.norm(f)
            r = np.cross(f, [0, 1.0, 0]); r /= np.linalg.norm(r); d = np.cross(f, r); R = np.stack([r, d, f]); rv0, _ = cv2.Rodrigues(R)
            s = least_squares(res, np.concatenate([rv0.ravel(), -R @ C0, [0.07, -1.2]]), args=(0.0,), bounds=([-10] * 6 + [0.04, -1.2000001], [10] * 6 + [0.12, -1.2]))
            if best is None or s.cost < best.cost: best = s
    return best.x
if __name__ == '__main__':
    p0 = start()
    s = least_squares(res, p0, args=(2.0,), bounds=([-10] * 6 + [0.04, -1.38], [10] * 6 + [0.12, -0.7])); p = s.x
    R, _ = cv2.Rodrigues(p[:3]); C = -R.T @ p[3:6]
    print('camera', C.round(3), 'zoccolo', round(p[6], 3), 'zR (bordo destro esterno della cornice)', round(p[7], 3), 'rms px', np.sqrt(np.mean(s.fun ** 2)).round(1))
    d = R.T @ np.linalg.solve(K, np.array([1667, 872, 1.0])); Q = C + ((XL - C[0]) / d[0]) * d
    print('angolo alto-dx della cornice sul muro sinistro: z', round(Q[2], 3), 'y', round(Q[1], 3)); np.save('poseC2.npy', p)
