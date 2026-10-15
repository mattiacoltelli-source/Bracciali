"""Allinea lo SfM alla stanza: gravità, parete TV (z=0), angolo split (x=0), pavimento (y=0), pareti F e finestra, scala."""
import sys, json
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np
from sfmio import *

def peak(v, lo, hi, w=0.03):
    """posizione del picco più denso di v in [lo,hi] (finestra scorrevole ±w), poi mediana dei valori vicini."""
    best = None
    for c in np.arange(lo, hi, 0.01):
        n = np.sum(np.abs(v - c) < w)
        if best is None or n > best[0]: best = (n, c)
    sel = v[np.abs(v - best[1]) < w]
    return float(np.median(sel)), int(best[0])

def run(model='/tmp/claude-0/s/sfm/work_hi/sparse_i/1', user_dims=(7.4, 4.5, 3.0)):
    r, cam = load(model)
    B, res = gravity_frame(r)
    P0 = np.array([p.xyz for p in r.points3D.values()]) @ B.T      # y su
    # --- parete T: normale dal piano del Taj, poi rifinita con i punti vicini
    im = [i for i in r.images.values() if i.name.startswith('b4bfa2ec')][0]
    box = (2372, 386, 2704, 918)
    pts = np.array([B @ r.points3D[p2.point3D_id].xyz for p2 in im.points2D if p2.has_point3D() and box[0] <= p2.xy[0] <= box[2] and box[1] <= p2.xy[1] <= box[3]])
    c = pts.mean(0); u, s, vt = np.linalg.svd(pts - c); n = vt[2]
    Ccam = B @ (-im.cam_from_world().rotation.matrix().T @ im.cam_from_world().translation)
    if n @ (Ccam - c) < 0: n = -n
    n[1] = 0; n /= np.linalg.norm(n)          # parete verticale
    yaw = np.arctan2(n[0], n[2])              # angolo della normale dalla +z verso +x
    d = -yaw
    Ry = np.array([[np.cos(d), 0, np.sin(d)], [0, 1, 0], [-np.sin(d), 0, np.cos(d)]])
    M = Ry @ B
    P = np.array([p.xyz for p in r.points3D.values()]) @ M.T          # unità SfM, assi stanza (z=normale T)
    zT = peak(P[:, 2], c[2] * 0 + np.median(P[:, 2]) - 3, np.median(P[:, 2]) + 3) if False else None
    # T: picco di z fra i punti con y plausibile (parete); cerco in tutta la fascia
    m = (P[:, 1] > np.percentile(P[:, 1], 5)) & (P[:, 1] < np.percentile(P[:, 1], 95))
    # candidati: il piano T è quello che contiene il Taj
    taj = np.array([M @ (B.T @ q) for q in pts])  # stessi punti del Taj nello stesso sistema
    zT_, _ = peak(taj[:, 2], taj[:, 2].min() - 0.05, taj[:, 2].max() + 0.05, 0.03)
    # F: picco di z a ~ +4.3 unità da T (cerco tra +3.5 e +6)
    zF_, nF = peak(P[:, 2], zT_ + 3.4, zT_ + 6.2, 0.03)
    # W: picco di x dei punti vicini a T-F (il lato lungo): cerco il picco più alto a x grande
    mm = (P[:, 2] > zT_ + 0.4) & (P[:, 2] < zF_ - 0.4) & (P[:, 1] > np.percentile(P[:, 1], 10)) & (P[:, 1] < np.percentile(P[:, 1], 90))
    xs = P[mm, 0]
    xW_, nW = peak(xs, np.percentile(xs, 75), np.percentile(xs, 99.5), 0.03)
    # pavimento e soffitto: picchi di y nell'interno
    mi = (P[:, 0] > xW_ - 6.5) & (P[:, 0] < xW_ - 0.5) & (P[:, 2] > zT_ + 0.5) & (P[:, 2] < zF_ - 0.5)
    ys = P[mi, 1]
    yF_, nfl = peak(ys, np.percentile(ys, 1), np.percentile(ys, 12), 0.03)
    yC_, nce = peak(ys, np.percentile(ys, 88), np.percentile(ys, 99.5), 0.04)
    return dict(M=M, B=B, zT=zT_, zF=zF_, xW=xW_, yFloor=yF_, yCeil=yC_, nF=nF, nW=nW, nfl=nfl, nce=nce, taj=taj, P=P, r=r, cam=cam)

if __name__ == '__main__':
    o = run()
    print('T z=%.4f | F z=%.4f (%d pt) | W x=%.4f (%d pt) | pavimento y=%.4f (%d pt) | soffitto y=%.4f (%d pt)' % (o['zT'], o['zF'], o['nF'], o['xW'], o['nW'], o['yFloor'], o['nfl'], o['yCeil'], o['nce']))
    W_u = o['zF'] - o['zT']; H_u = o['yCeil'] - o['yFloor']
    print('unità SfM: W(T-F)=%.4f  H=%.4f' % (W_u, H_u))
    np.savez('calib_raw.npz', M=o['M'], zT=o['zT'], zF=o['zF'], xW=o['xW'], yFloor=o['yFloor'], yCeil=o['yCeil'])
