"""Texture delle due porte, rettificate dalle foto frontali dell'utente (non registrate): le foto verticali 2304 x 4096 si tolgono dalla distorsione radiale (f = 3024,6, k1 = 0,0276),
poi si raddrizza il rettangolo esterno del coprifilo (4 angoli letti a mano nella foto, misure vere dalle foto registrate) a 600 px/m.
Porta interna (parete A): coprifilo largo 0,886 m, alto 2,035 m. Portone d'ingresso (parete F): 1,236 x 2,24 m.
Uso: FOTO_DIR=... python3 door_prep.py  ->  DOOR_ASSETS/door_A_raw.png e door_F_raw.png"""
import os, cv2, numpy as np
D = os.environ['FOTO_DIR']; OUT = os.environ.get('DOOR_ASSETS', '/tmp/claude-0/s/st3/assets/doors'); os.makedirs(OUT, exist_ok=True)
UND = os.environ.get('UND_NEW', '/tmp/claude-0/s/st3/und_new'); os.makedirs(UND, exist_ok=True)

def undistort(pid):
    p = f'{UND}/{pid}.png'
    if os.path.exists(p): return cv2.imread(p)
    im = cv2.imread(f'{D}/{pid}-image.jpg'); h, w = im.shape[:2]; K = np.array([[3024.6, 0, w / 2], [0, 3024.6, h / 2], [0, 0, 1.0]])
    u = cv2.undistort(im, K, np.array([0.0276, 0, 0, 0], float), None, K); cv2.imwrite(p, u); return u

def rect(pid, quad, W, H, ppm, out):
    im = undistort(pid); w = int(round(W * ppm)); h = int(round(H * ppm))
    M = cv2.getPerspectiveTransform(np.array(quad, np.float32), np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32))
    r = cv2.warpPerspective(im, M, (w, h), flags=cv2.INTER_CUBIC); cv2.imwrite(f'{OUT}/{out}', r); print(out, r.shape); return r

if __name__ == '__main__':
    # angoli esterni del coprifilo (alto sinistra, alto destra, basso destra, basso sinistra) nella foto non distorta
    rect('81d8e52c', [(582, 1186), (1659.5, 1172.5), (1659, 3490), (641, 3509)], 0.886, 2.035, 600, 'door_A_raw.png')
    rect('afd7ab79', [(408.75, 608), (1950.5, 550), (1910, 3340), (549.5, 3347)], 1.236, 2.24, 600, 'door_F_raw.png')
