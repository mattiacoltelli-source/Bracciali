"""Come run_walls8.py (bake dei muri con le foto del corridoio, solo per i raggi che passano dentro l'arco) ma in parallelo e piu' veloce:
- ogni foto e' un lavoro a parte (multiprocessing, fork: P e le scatole sono condivise);
- l'occlusione a scatole si calcola solo per i punti con peso > 0 (per le foto che vedono poco il muro e' 10-1000 volte meno lavoro): il risultato e' lo stesso di bake4.bake, perche' dove il peso e' 0 l'occlusione non conta.
Uso: [EXCLUDE=id,id] FRAME_EXT=1 python3 run_walls9.py <ppm> <tag> <scala> [pareti...]   ->  out/wall3_<parete>_<tag>.npz"""
import os, sys, time
os.environ.setdefault('FRAME_EXT', '1')
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from multiprocessing import Pool
import run_walls8                                   # patch arco (box_hit con arch_blocked) e costanti
from run_walls8 import box_hit
from bake4 import FR, wall_points, view_weight, solve_gains
from bake2 import remap
from scene_def import BOXES, as_occluders

G = {}

def layer(n):
    fr, P, N, shape, occ, scale, smooth = (G[k] for k in ('fr', 'P', 'N', 'shape', 'occ', 'scale', 'smooth'))
    ny, nx = shape
    img = fr.image(n, scale); uv, z = fr.project(n, P); uv = uv * scale
    w = view_weight(fr, n, P, N, uv, z, img.shape, margin=60.0, cos_pow=1.5, dist_pow=1.0, min_cos=0.12)
    nz = np.nonzero(w > 0)[0]
    if len(nz) == 0: return n, None
    w[nz] = w[nz] * (~box_hit(fr.cams[n]['C'], P[nz], occ))
    wm = w.reshape(ny, nx).astype(np.float32)
    if wm.max() <= 0: return n, None
    col = remap(img, uv, (ny, nx)).astype(np.uint8)
    if smooth > 0:
        k = int(2 * smooth) * 2 + 1
        vis = cv2.erode((wm > 0).astype(np.uint8), np.ones((k, k), np.uint8)).astype(np.float32)
        wm = cv2.GaussianBlur(wm, (0, 0), smooth) * vis
    return n, (col, wm, float((wm > 0).mean()))

if __name__ == '__main__':
    ppm = float(sys.argv[1]); tag = sys.argv[2]; scale = float(sys.argv[3]); nproc = int(os.environ.get('NPROC', '4'))
    fr = FR(); occ = as_occluders(BOXES)
    skip = set(filter(None, os.environ.get('EXCLUDE', '').split(',')))      # foto da scartare (es. la foto buia dal fondo del corridoio, guadagno 3,9: la vedeva bruciata)
    names = [n for n in sorted(fr.cams) if n not in skip]
    for wid in sys.argv[4:] or ['F']:
        t0 = time.time()
        P, N, shape = wall_points(fr, wid, ppm)
        G.update(fr=fr, P=P, N=N, shape=shape, occ=occ, scale=scale, smooth=ppm / 100.0)
        layers = {}
        with Pool(nproc) as pool:
            for n, r in pool.imap_unordered(layer, names):
                if r is None: print(wid, n, 'nessuna copertura', flush=True); continue
                col, wm, cop = r; layers[n] = (col.astype(np.float32), wm); print(wid, n, 'cop', round(cop, 3), '%.0f s' % (time.time() - t0), flush=True)
        cams = sorted(layers)
        gains = solve_gains(layers, cams, wid, True); print('guadagni calcolati', '%.0f s' % (time.time() - t0), flush=True)
        ny, nx = shape; acc = np.zeros((ny, nx, 3), np.float64); tot = np.zeros((ny, nx), np.float64)
        for n in cams:
            col, wm = layers[n]; wp = wm.astype(np.float64) ** 3.0
            acc += (col * gains[n][None, None, :]) * wp[..., None]; tot += wp
        out = acc / np.maximum(tot, 1e-30)[..., None]
        valid = tot > 1e-12 * max(1.0, tot.max()) * 1e-3
        img = np.clip(out, 0, 255).astype(np.uint8)
        np.savez_compressed(f'/tmp/claude-0/s/reg/out/wall3_{wid}_{tag}.npz', img=img, valid=valid)
        o = img.copy(); o[~valid] = (0, 0, 255)
        cv2.imwrite(f'/tmp/claude-0/s/reg/out/wall3_{wid}_{tag}.jpg', o, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(wid, shape, 'validi', round(float(valid.mean()), 3), round(time.time() - t0), 's', flush=True)
