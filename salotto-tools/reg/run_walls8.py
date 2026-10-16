"""Bake dei muri CON le foto scattate dal corridoio (dietro l'arco della parete TV).

Perche': cams_sel.select() toglie tutte le foto con la camera nel corridoio (z < 0), perche' da li' i muri si vedrebbero "attraverso" la parete TV. Ma le foto fatte dal corridoio guardano la stanza
attraverso l'arco e vedono la parete d'ingresso quasi di fronte e tutta intera, con un'esposizione coerente: sono le migliori per il suo colore e la sua luce (nel muro cotto senza di loro la parte
vicino all'angolo era piu' scura e piu' fredda). Qui le si riammette, ma solo per i punti il cui raggio passa davvero dentro l'arco (sia sul piano z = -0,40, l'inizio dell'imbotte, sia sul piano z = 0):
per tutti gli altri punti la vista e' bloccata (si comporta come una scatola che occlude, come quelle dei mobili).
Uso: FRAME_EXT=1 python3 run_walls8.py <ppm> <tag> <scala> [pareti...]   ->  out/wall3_<parete>_<tag>.npz (come run_walls7.py)"""
import os, sys, time
os.environ.setdefault('FRAME_EXT', '1')
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
import bake4
from bake4 import FR, wall_points, bake
from scene_def import BOXES, as_occluders
from cams_sel import select

ARCH_X = (0.46, 1.53); ARCH_TOP = 2.0; Z_N = -0.40
_orig_box_hit = bake4.box_hit

def arch_blocked(C, P, m=0.05):
    """True per i punti P che dalla camera C (z < 0) non si vedono attraverso l'arco (imbotte profondo 40 cm: due piani da attraversare dentro l'apertura, con un margine m dai bordi)"""
    d = P - C; ok = np.ones(len(P), bool)
    with np.errstate(divide='ignore', invalid='ignore'):
        for zp in ((Z_N, 0.0) if C[2] < Z_N else (0.0,)):
            t = (zp - C[2]) / d[:, 2]; Q = C[None, :] + t[:, None] * d
            ok &= (t > 0) & (Q[:, 0] > ARCH_X[0] + m) & (Q[:, 0] < ARCH_X[1] - m) & (Q[:, 1] > 0.0) & (Q[:, 1] < ARCH_TOP - m)
    return ~ok

def box_hit(C, P, boxes, skip=None):
    hit = _orig_box_hit(C, P, boxes, skip)
    return hit | arch_blocked(C, P) if C[2] <= 0.0 else hit

bake4.box_hit = box_hit

if __name__ == '__main__':
    fr = FR(); names = sorted(fr.cams)      # tutte le foto, comprese quelle del corridoio: le vincola box_hit
    occ = as_occluders(BOXES)
    ppm = float(sys.argv[1]); tag = sys.argv[2]; scale = float(sys.argv[3])
    for wid in sys.argv[4:] or ['F']:
        t0 = time.time()
        P, N, shape = wall_points(fr, wid, ppm)
        img, valid, tot = bake(fr, P, N, shape, names, occ, scale=scale, power=3.0, smooth=ppm / 100.0, tag=wid, verbose=True)
        np.savez_compressed(f'/tmp/claude-0/s/reg/out/wall3_{wid}_{tag}.npz', img=img, valid=valid)
        out = img.copy(); out[~valid] = (0, 0, 255)
        cv2.imwrite(f'/tmp/claude-0/s/reg/out/wall3_{wid}_{tag}.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(wid, shape, 'validi', round(float(valid.mean()), 3), round(time.time() - t0), 's', flush=True)
