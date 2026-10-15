"""Rifinitura di una scatola (min,max) sui bordi delle foto: costo = distanza chamfer (troncata) tra i bordi proiettati e i bordi di Canny.
Ottimizzazione a coordinate con passi decrescenti, ogni parametro limitato in un intervallo."""
import os, sys, json
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
from ov import corners, EDGES

FACES = {  # facce di una scatola come quartine di indici-spigolo (corner index = 4*ix + 2*iy + iz)
    '-x': ([0, 1, 3, 2], (-1, 0, 0)), '+x': ([4, 5, 7, 6], (1, 0, 0)),
    '-y': ([0, 1, 5, 4], (0, -1, 0)), '+y': ([2, 3, 7, 6], (0, 1, 0)),
    '-z': ([0, 2, 6, 4], (0, 0, -1)), '+z': ([1, 3, 7, 5], (0, 0, 1))}

class EdgeMaps:
    def __init__(self, cams, scale=0.25, blur=1.2, lo=40, hi=110):
        self.fr = FR(); self.scale = scale; self.m = {}
        for c in cams:
            img = self.fr.image(c, scale); g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            g = cv2.GaussianBlur(g, (0, 0), blur)
            e = cv2.Canny(g, lo, hi)
            dist = cv2.distanceTransform((e == 0).astype(np.uint8), cv2.DIST_L2, 3)
            self.m[c] = (dist, e, g.shape)

def visible_edges(lo, hi, Cam):
    P = corners(lo, hi)
    vis = set()
    for name, (idx, n) in FACES.items():
        ctr = P[idx].mean(axis=0)
        if np.dot(np.array(n), Cam - ctr) > 0:
            for k in range(4): vis.add(tuple(sorted((idx[k], idx[(k + 1) % 4]))))
    return [e for e in EDGES if tuple(sorted(e)) in vis], P

def box_cost(em, cams, lo, hi, dmax=14.0, step=5.0, skip_edges=None, return_detail=False):
    tot = 0.0; cnt = 0; det = {}
    for c in cams:
        dist, e, shp = em.m[c]; H, W = shp
        Cam = em.fr.cams[c]['C']
        edges, P = visible_edges(lo, hi, Cam)
        uv, z = em.fr.project(c, P); uv = uv * em.scale
        cc = 0.0; nn = 0
        for a, b in edges:
            if skip_edges and (c, a, b) in skip_edges: continue
            if z[a] < 0.15 or z[b] < 0.15: continue
            L = np.linalg.norm(uv[a] - uv[b]); n = max(2, int(L / step))
            t = np.linspace(0, 1, n)[:, None]; pts = uv[a] + (uv[b] - uv[a]) * t
            ok = (pts[:, 0] >= 1) & (pts[:, 0] < W - 2) & (pts[:, 1] >= 1) & (pts[:, 1] < H - 2)
            if ok.sum() < 3: continue
            pts = pts[ok]
            d = dist[np.round(pts[:, 1]).astype(int), np.round(pts[:, 0]).astype(int)]
            cc += np.minimum(d, dmax).sum(); nn += len(d)
        if nn: det[c] = cc / nn; tot += cc; cnt += nn
    return (tot / max(cnt, 1), det) if return_detail else tot / max(cnt, 1)

def fit(em, cams, lo, hi, free, ranges, iters=6, steps=(0.04, 0.02, 0.01, 0.005, 0.0025), verbose=True, **kw):
    """free: lista di indici parametro (0..5 = xmin,ymin,zmin,xmax,ymax,zmax); ranges: dict idx -> (a,b)"""
    p = np.array(list(lo) + list(hi), float)
    def cost(q): return box_cost(em, cams, q[:3], q[3:], **kw)
    best = cost(p)
    if verbose: print('costo iniziale %.3f' % best)
    for s in steps:
        for it in range(iters):
            improved = False
            for i in free:
                for sg in (-1, 1):
                    q = p.copy(); q[i] += sg * s
                    a, b = ranges.get(i, (-1e9, 1e9))
                    if not (a <= q[i] <= b): continue
                    if q[3] - q[0] < 0.03 or q[4] - q[1] < 0.03 or q[5] - q[2] < 0.03: continue
                    c = cost(q)
                    if c < best - 1e-4: best = c; p = q; improved = True
            if not improved: break
        if verbose: print('passo %.4f -> costo %.3f  box %s' % (s, best, np.round(p, 3).tolist()))
    return p[:3], p[3:], best
