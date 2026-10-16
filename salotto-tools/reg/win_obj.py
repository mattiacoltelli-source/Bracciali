"""La finestra della parete W (z 0,72-1,63 m), in 3D: buco nel muro, spalle in ottone e telaio con i vetri 13 cm piu' dentro.
Prima il telaio era cotto nella texture del muro: le foto registrate lo vedono da 5-7 m con pose diverse e, siccome sta 13 cm dietro il filo del muro, finiva sfocato e sdoppiato.
Ora: il telaio e' un piano a parte (x = 7,10 + 0,13) con la foto frontale dell'utente (non registrata) rimappata a 800 px/m, e le quattro spalle sono strisce campionate dalla stessa foto
(console/win_prep.py: omografia con ECC sul riferimento metrico, camera dalla decomposizione, riflessi del fotografo coperti). Il buco ha le misure dell'apertura (letta sugli angoli esterni
delle spalle): z 0,725-1,631, y 0,9225-2,466; il manifesto lo dice a real.js (`holes`), che ritaglia la parete e attacca le parti alla parete, come per le porte.
Le texture si portano alla luce del muro (guadagno per canale = intonaco cotto nel pacchetto / intonaco della foto frontale)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh

ASSETS = os.environ.get('WIN_ASSETS', '/tmp/claude-0/s/st3/assets/win')
X_WALL = 7.10; D = 0.13                                           # filo del muro e profondita' del telaio
HOLE = dict(z0=0.725, z1=1.631, y0=0.9225, y1=2.466)
GAIN = (1.10, 1.12, 1.14)                                         # RGB
PPM_L = 700; PADR = 2

def holes():
    """per il manifesto: buchi nelle pareti, (u0, u1, y0, y1) nel riferimento della parete (parete W: u = z)"""
    return {'W': [[HOLE['z0'], HOLE['z1'], HOLE['y0'], HOLE['y1']]]}

def wall_rects(margin_l=0.10, margin_r=0.14, margin_t=0.10, margin_low=0.035):
    """fascia (u0, u1, y0, y1, morbido) della parete W da rifare per diffusione: la finestra sfocata e le sue sbavature (a destra il telaio sdoppiato arriva a z = 1,72: la striscia d'ottone che restava);
    sotto si tiene un margine piccolo (li' comincia la nicchia del radiatore)"""
    h = HOLE
    return [(h['z0'] - margin_l, h['z1'] + margin_r, h['y0'] - margin_low, h['y1'] + margin_t, True)]

def jpg(img, q=90):
    ok, b = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q, cv2.IMWRITE_JPEG_OPTIMIZE, 1]); assert ok; return b.tobytes()

def build():
    """parti: lista di dict(name, mesh, map, wall) e immagini jpeg"""
    g = np.array(GAIN[::-1], np.float32)[None, None, :]
    fr = np.clip(cv2.imread(f'{ASSETS}/frame_clean.png').astype(np.float32) * g, 0, 255).astype(np.uint8)
    at = np.clip(cv2.imread(f'{ASSETS}/lining_atlas.png').astype(np.float32) * g, 0, 255).astype(np.uint8)
    imgs = {'win_t': jpg(fr, 90), 'win_l': jpg(at, 88)}
    z0, z1, y0, y1 = (HOLE[k] for k in ('z0', 'z1', 'y0', 'y1')); xf = X_WALL + D; xw = X_WALL
    white = [(255, 255, 255)] * 4
    m1 = Mesh()
    m1._add([(xf, y0, z0), (xf, y0, z1), (xf, y1, z1), (xf, y1, z0)], white, [(0, 1, 2), (0, 2, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)])
    AH, AW = at.shape[:2]; nd = int(round(D * PPM_L)); m2 = Mesh()
    nzs = int(round((z1 - z0) * PPM_L)); nys = int(round((y1 - y0) * PPM_L))
    # (riga della striscia nell'atlante, lunghezza in texel, punto sul lato del telaio e sul lato del muro all'inizio e alla fine della striscia)
    strips = [(0, nzs, ((xf, y1, z0), (xf, y1, z1)), ((xw, y1, z0), (xw, y1, z1))),                        # alto (sotto)
              (1, nzs, ((xf, y0, z0), (xf, y0, z1)), ((xw, y0, z0), (xw, y0, z1))),                        # basso (davanzale)
              (2, nys, ((xf, y0, z0), (xf, y1, z0)), ((xw, y0, z0), (xw, y1, z0))),                        # sinistra
              (3, nys, ((xf, y0, z1), (xf, y1, z1)), ((xw, y0, z1), (xw, y1, z1)))]                        # destra
    for i, n, (fa, fb), (wa, wb) in strips:
        r0 = i * (nd + PADR); u1 = n / AW; vf = 1 - r0 / AH; vw = 1 - (r0 + nd) / AH
        m2._add([fa, fb, wb, wa], white, [(0, 1, 2), (0, 2, 3)], [(0, vf), (u1, vf), (u1, vw), (0, vw)])
    return [dict(name='win_frame', mesh=m1, map='win_t', wall='W'), dict(name='win_lining', mesh=m2, map='win_l', wall='W')], imgs

if __name__ == '__main__':
    p, im = build(); print([(q['name'], len(q['mesh'].P)) for q in p], {k: len(v) for k, v in im.items()}, wall_rects(), holes())
