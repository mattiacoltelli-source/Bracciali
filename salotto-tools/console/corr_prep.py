"""Ritagli del corridoio dalle foto non distorte (und_new/): stampe rettificate (fa11fad8), foglia della porta, pavimento e muro di fondo rettificati con la posa della foto del corridoio (3d4294a2).
La posa di 3d4294a2 viene da una PnP sugli angoli dell'arco e su tre punti della parete TV letti in una foto registrata (b4bfa2ec); il muro di fondo sta a z = -1,40 (due stime indipendenti del pavimento)."""
import os, sys, numpy as np, cv2
OUT = os.environ.get('CORR_ASSETS', '/tmp/claude-0/s/st3/corr'); os.makedirs(OUT, exist_ok=True)
UND = '/tmp/claude-0/s/st3/und_new'
K = np.array([[3024.6, 0, 1152], [0, 3024.6, 2048], [0, 0, 1.0]])
pose = np.load('/tmp/claude-0/s/st3/work/pose3b_3d4294a2.npy'); RV, TV = pose[:3], pose[3:6]
Z_F = -1.40
R_, _ = cv2.Rodrigues(RV); np.save(f'{OUT}/cam.npy', (-R_.T @ TV).astype(np.float64))      # centro della camera della foto del corridoio

def project(P):
    q, _ = cv2.projectPoints(np.asarray(P, np.float64).reshape(-1, 1, 3), RV, TV, K, None); return q.reshape(-1, 2)

def undistort_photos(pids=('3d4294a2', 'fa11fad8', '96c295ad')):
    """foto verticali dell'utente (2304 x 4096) senza distorsione radiale: K con f = 3024,6 e k1 = 0,0276; servono FOTO_DIR e UND"""
    D = os.environ['FOTO_DIR']; os.makedirs(UND, exist_ok=True)
    for pid in pids:
        if os.path.exists(f'{UND}/{pid}.png'): continue
        im = cv2.imread(f'{D}/{pid}-image.jpg'); h, w = im.shape[:2]; Kp = np.array([[3024.6, 0, w / 2], [0, 3024.6, h / 2], [0, 0, 1.0]])
        cv2.imwrite(f'{UND}/{pid}.png', cv2.undistort(im, Kp, np.array([0.0276, 0, 0, 0], float), None, Kp))

def rectify_quad(img, quad, size):
    """quad = [TL, TR, BR, BL] in pixel; size = (w, h) del risultato"""
    w, h = size; dst = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)
    H = cv2.getPerspectiveTransform(np.array(quad, np.float32), dst); return cv2.warpPerspective(img, H, (w, h), flags=cv2.INTER_CUBIC)

def prints():
    im = cv2.imread(f'{UND}/fa11fad8.png')
    q1 = [(1050, 529), (1950, 537), (1913, 1803), (1053, 1802)]; q2 = [(1063, 1944), (1920, 1953), (1885, 3117), (1052, 3117)]
    a = rectify_quad(im, q1, (640, 896)); b = rectify_quad(im, q2, (640, 896))
    cv2.imwrite(f'{OUT}/print1.png', a); cv2.imwrite(f'{OUT}/print2.png', b); return a, b

def grid_to_image(xs, ys, z):
    X, Y = np.meshgrid(xs, ys); P = np.stack([X, Y, np.full_like(X, z)], -1).reshape(-1, 3); uv = project(P).reshape(X.shape + (2,)); return uv

def sample(img, uv):
    return cv2.remap(img, uv[..., 0].astype(np.float32), uv[..., 1].astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))

def reveal_colors(im, depth=0.40, h=1.989, x0=0.46, x1=1.53, n=(10, 6)):
    """colori dell'imbotte dell'arco (architrave e due stipiti) campionati dalla foto sui punti 3D (foto sfumata per mediare la grana dell'intonaco)"""
    bl = cv2.GaussianBlur(im, (0, 0), 7.0).astype(np.float32); out = {}
    zs = np.linspace(0, -depth, n[1])
    ys = np.linspace(0.05, h - 0.02, n[0]); Y, Z = np.meshgrid(ys, zs, indexing='ij')
    for name, x in (('left', x0), ('right', x1)):
        P = np.stack([np.full_like(Y, x), Y, Z], -1).reshape(-1, 3); uv = project(P).reshape(Y.shape + (2,)); out[name] = sample(bl, uv)[..., ::-1]
        out[name + '_uv'] = uv
    xs = np.linspace(x0, x1, n[0]); X, Z = np.meshgrid(xs, zs, indexing='ij')
    P = np.stack([X, np.full_like(X, h), Z], -1).reshape(-1, 3); uv = project(P).reshape(X.shape + (2,)); out['lintel'] = sample(bl, uv)[..., ::-1]; out['lintel_uv'] = uv
    return out

if __name__ == '__main__':
    undistort_photos()
    a, b = prints(); print('stampe', a.shape, b.shape)
    im = cv2.imread(f'{UND}/3d4294a2.png')
    # muro di fondo: x 0..2.8, y 0..2.7, 200 px/m
    ppm = 200; xs = np.arange(0, 2.8, 1 / ppm) + 0.5 / ppm; ys = np.arange(2.7, 0, -1 / ppm) - 0.5 / ppm
    uv = grid_to_image(xs, ys, Z_F); far = sample(im, uv); cv2.imwrite(f'{OUT}/far_raw.png', far)
    # foglia della porta a 600 px/m
    ppm = 600; xs = np.arange(0.34, 0.96, 1 / ppm); ys = np.arange(1.95, 0.0, -1 / ppm)
    door = sample(im, grid_to_image(xs, ys, Z_F)); cv2.imwrite(f'{OUT}/door_raw.png', door); print('porta', door.shape)
    # pavimento: x 0..2.8, z 0..-1.4, 250 px/m (righe: z da 0, il filo della parete TV, verso -1.4)
    ppm = 250; xs = np.arange(0, 2.8, 1 / ppm) + 0.5 / ppm; zs = np.arange(0.0, -1.4, -1 / ppm) - 0.5 / ppm
    X, Z = np.meshgrid(xs, zs); P = np.stack([X, np.zeros_like(X), Z], -1).reshape(-1, 3); uvf = project(P).reshape(X.shape + (2,)); floor = sample(im, uvf); cv2.imwrite(f'{OUT}/floor_raw.png', floor)
    rc = reveal_colors(im); np.savez(f'{OUT}/reveal.npz', **{k: v for k, v in rc.items() if not k.endswith('_uv')})
    for k in ('left', 'right', 'lintel'): print(k, rc[k].shape, rc[k].reshape(-1, 3).mean(0).round(0), rc[k][0, 0].round(0), rc[k][-1, -1].round(0), 'uv', rc[k + '_uv'][0, 0].round(0), rc[k + '_uv'][-1, -1].round(0))
    print('ok')
