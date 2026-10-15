import sys, json
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from sfmio import *
from calib import run

class Frame:
    """Sistema della stanza (x lungo la parete TV dall'angolo split, y su, z verso l'ingresso) ricavato dallo SfM.
    La mappa SfM -> stanza è: allineamento con la gravità e la parete TV, poi scala per asse in modo che i 6 piani
    coincidano col box (L, W, H)."""
    def __init__(self, planes, M, r, cam, dims=(7.4, 4.5, 3.0), img_dir='/tmp/claude-0/s/sfm/img_full', xshift=0.0):
        # xshift: la parete split (A) sta davvero a `xshift` metri dal vecchio piano xA (misurato con le foto di dettaglio e la scansione):
        # l'origine di x si sposta sulla parete vera e la lunghezza della stanza diventa dims[0] - xshift; la scala per asse non cambia.
        self.L, self.W, self.H = dims
        self.M = M; self.r = r; self.cam = cam
        self.xA, self.xW, self.zT, self.zF, self.yF, self.yC = [planes[k] for k in ('xA', 'xW', 'zT', 'zF', 'yFloor', 'yCeil')]
        self.sx = self.L / (self.xW - self.xA); self.sz = self.W / (self.zF - self.zT); self.sy = self.H / (self.yC - self.yF)
        self.xA = self.xA + xshift / self.sx; self.L = self.L - xshift
        self.f, self.cx, self.cy, self.k = cam.params
        self.img_dir = img_dir
        self.cams = {}
        for im in r.images.values():
            n = im.name[:8]; pose = im.cam_from_world()
            self.cams[n] = dict(R=pose.rotation.matrix(), t=pose.translation, name=n)
            self.cams[n]['C'] = self.sfm_to_room(-pose.rotation.matrix().T @ pose.translation)
    def sfm_to_room(self, X):
        Xa = np.atleast_2d(X) @ self.M.T
        out = np.stack([(Xa[:, 0] - self.xA) * self.sx, (Xa[:, 1] - self.yF) * self.sy, (Xa[:, 2] - self.zT) * self.sz], 1)
        return out if np.ndim(X) > 1 else out[0]
    def room_to_sfm(self, P):
        P = np.atleast_2d(P)
        Xa = np.stack([P[:, 0] / self.sx + self.xA, P[:, 1] / self.sy + self.yF, P[:, 2] / self.sz + self.zT], 1)
        return Xa @ self.M          # M^T applicata: (M^T Xa) per righe = Xa @ M
    def project(self, n, P):
        c = self.cams[n]
        X = self.room_to_sfm(P) @ c['R'].T + c['t']
        z = X[:, 2]
        with np.errstate(divide='ignore', invalid='ignore'):
            xn = X[:, 0] / z; yn = X[:, 1] / z
        r2 = xn * xn + yn * yn
        return np.stack([self.f * xn * (1 + self.k * r2) + self.cx, self.f * yn * (1 + self.k * r2) + self.cy], 1), z
    def image(self, n, scale=1.0):
        im = cv2.imread(f'{self.img_dir}/{n}.jpg')
        return cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale != 1 else im

NEW_MODEL = '/tmp/claude-0/s/sfm/work_new/sparse/0'
XSHIFT = 0.30   # m: parete split vera rispetto al vecchio piano xA (interruttore 0.297, stipite porta 0.300, quadro 0.32, credenza)
def make_frame(dims=(7.4, 4.5, 3.0), extended=None, xshift=None):
    """extended=True (o env FRAME_EXT=1): usa il modello esteso con le foto di dettaglio (le vecchie pose sono identiche).
    xshift (o env FRAME_SHIFT=0 per tornare al vecchio sistema): sposta l'origine sulla vera parete A."""
    import os, pycolmap
    if extended is None: extended = os.environ.get('FRAME_EXT') == '1'
    if xshift is None: xshift = 0.0 if os.environ.get('FRAME_SHIFT') == '0' else XSHIFT
    o = run()
    pl = json.load(open('/tmp/claude-0/s/reg/planes_u.json'))
    r = pycolmap.Reconstruction(NEW_MODEL) if extended else o['r']
    return Frame(pl, o['M'], r, o['cam'], dims, xshift=xshift)

if __name__ == '__main__':
    fr = make_frame()
    print('scale per asse: sx=%.4f sy=%.4f sz=%.4f' % (fr.sx, fr.sy, fr.sz))
    for n, c in sorted(fr.cams.items()): print(n, np.round(c['C'], 2), end=' | ')
    print()
