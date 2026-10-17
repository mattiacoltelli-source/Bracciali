"""La finestra della parete W (z 0,726-1,630 m, y 0,95-2,49 m), in 3D: buco nel muro e un unico piano di telaio e vetri 1,5 cm dietro il filo, piu' quattro spalle d'ottone di 1,5 cm.
Misure: l'utente dice che la finestra e' alta 154 cm e sta a 95 cm da terra; la larghezza (0,904 m, centro z = 1,178) viene dalle foto registrate. Il piano non e' piu' il solo riquadro del telaio con
un anello d'ottone aggiunto fuori (a ogni giro i bordi d'oro uscivano piu' sottili del vero e il telaio deformato in altezza): la texture e' la foto vera della finestra con il quadrilatero esterno dell'oro
raddrizzato sul rettangolo 0,904 x 1,54 (console/win_prep2.py), quindi proporzioni e larghezza dei bordi sono quelle della foto (oro ~9% della larghezza); i vetri della foto sono scuri e pieni di riflessi
della stanza e si sostituiscono con quelli puliti della vecchia texture. Il manifesto lo dice a real.js (`holes`), che ritaglia la parete e attacca le parti alla parete, come per le porte.
Storia: telaio 12 cm dietro il muro con spalle d'ottone (dai fianchi la banda vicina spariva), spalle d'intonaco (sembrava incassata), telaio a filo (idem), anello d'ottone 1,25 / 3,75 / 4,5 cm: tutti con il
riquadro vecchio, piu' alto del vero e con il bordo troppo sottile."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh

ASSETS = os.environ.get('WIN_ASSETS', '/tmp/claude-0/s/st3/assets/win')
X_WALL = 7.10; D = 0.015                                          # filo del muro e profondita' del telaio (1,5 cm: la finestra e' quasi a filo; a incassarsi e' il termosifone)
HOLE = dict(z0=0.726, z1=1.630, y0=0.95, y1=2.49)                 # apertura = contorno esterno dell'oro: alta 1,54 e a 0,95 da terra (misure dell'utente), larga 0,904
GAIN = (1.15, 1.17, 1.19)                                         # RGB: la foto e' un po' piu' scura del vecchio telaio (gold V 131 contro 138) e il vecchio aveva 1,10-1,14
GOLD = (150, 112, 62)                                             # ottone delle spalle

def holes():
    """per il manifesto: buchi nelle pareti, (u0, u1, y0, y1) nel riferimento della parete (parete W: u = z)"""
    return {'W': [[HOLE['z0'], HOLE['z1'], HOLE['y0'], HOLE['y1']]]}

def wall_rects(margin_l=0.20, margin_r=0.26, margin_t=0.20, margin_low=0.035):
    """fascia (u0, u1, y0, y1, morbido) della parete W da rifare per diffusione: la finestra sfocata e le sue sbavature (a destra il telaio sdoppiato arriva a z = 1,72);
    sotto si tiene un margine piccolo (li' comincia la nicchia del radiatore)"""
    h = HOLE
    return [(h['z0'] - margin_l, h['z1'] + margin_r, h['y0'] - margin_low, h['y1'] + margin_t, True)]

def jpg(img, q=90):
    ok, b = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q, cv2.IMWRITE_JPEG_OPTIMIZE, 1]); assert ok; return b.tobytes()

def build():
    """parti: lista di dict(name, mesh, map, wall) e immagini jpeg"""
    g = np.array(GAIN[::-1], np.float32)[None, None, :]
    fr = np.clip(cv2.imread(f'{ASSETS}/frame_full.png').astype(np.float32) * g, 0, 255).astype(np.uint8)
    imgs = {'win_t': jpg(fr, 90)}
    z0, z1, y0, y1 = (HOLE[k] for k in ('z0', 'z1', 'y0', 'y1'))
    xf = X_WALL + D; xw = X_WALL; white = [(255, 255, 255)] * 4
    m1 = Mesh()
    m1._add([(xf, y0, z0), (xf, y0, z1), (xf, y1, z1), (xf, y1, z0)], white, [(0, 1, 2), (0, 2, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)])
    # spalle d'ottone di 1,5 cm lungo i quattro lati del buco (chiudono lo scalino fra il filo del muro e il telaio)
    gold = np.array(GOLD, float); m2 = Mesh(); ref = (X_WALL - 0.6, (y0 + y1) / 2, (z0 + z1) / 2)
    for a_, b_, c_, d_ in (((xf, y1, z0), (xf, y1, z1), (xw, y1, z1), (xw, y1, z0)), ((xf, y0, z0), (xf, y0, z1), (xw, y0, z1), (xw, y0, z0)),
                           ((xf, y0, z0), (xf, y1, z0), (xw, y1, z0), (xw, y0, z0)), ((xf, y0, z1), (xf, y1, z1), (xw, y1, z1), (xw, y0, z1))):
        m2.quad_grad([a_, b_, c_, d_], [gold * 0.85] * 2 + [gold] * 2, ref=ref, two=True)
    return [dict(name='win_frame', mesh=m1, map='win_t', wall='W'), dict(name='win_lining', mesh=m2, map=None, wall='W')], imgs

if __name__ == '__main__':
    p, im = build(); print([(q['name'], len(q['mesh'].P)) for q in p], {k: len(v) for k, v in im.items()}, wall_rects(), holes())
