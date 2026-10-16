"""La finestra della parete W (z 0,73-1,63 m), in 3D: buco nel muro, spalle svasate in ottone e telaio con i vetri 12 cm piu' dentro.
Prima il telaio era cotto nella texture del muro: le foto registrate lo vedono da 5-7 m con pose diverse e, siccome sta dietro il filo del muro, finiva sfocato e sdoppiato.
Ora: il telaio e' un piano a parte (x = 7,10 + 0,12) con la foto frontale dell'utente (non registrata) rimappata a 800 px/m, e le quattro spalle sono facce piane svasate fra l'apertura nel muro e il
contorno del telaio (piu' stretto di 4 cm per lato: nel muro l'apertura e' 0,904 m, il telaio 0,829 m), campionate dalla stessa foto con omografie esatte (console/win_prep.py: raddrizzamento con gli
otto angoli dei vetri e un riquadro ideale simmetrico, quindi il telaio esce dritto e simmetrico; riflessi del fotografo coperti). Apertura e telaio sono rettangoli esatti: z 0,726-1,630 e 0,7635-1,5925,
y 0,925-2,466 e 0,9786-2,4644 (centro z = 1,178; bordo basso dei vetri a y = 0,995; scala 0,329 m per larghezza di vetro). Il manifesto lo dice a real.js (`holes`), che ritaglia la parete e attacca le
parti alla parete, come per le porte. Le texture si portano alla luce del muro (guadagno per canale = intonaco cotto nel pacchetto / intonaco della foto frontale); i riflessi speculari dell'ottone
si comprimono per non avere macchie bianche."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh

ASSETS = os.environ.get('WIN_ASSETS', '/tmp/claude-0/s/st3/assets/win')
X_WALL = 7.10; D = 0.03                                           # filo del muro e profondita' del telaio: 3 cm (prima 12: dai fianchi la banda vicina spariva e quella lontana era grossa, il contorno sembrava asimmetrico)
HOLE = dict(z0=0.726, z1=1.630, y0=0.925, y1=2.466)               # apertura nel muro
FRAME = dict(z0=0.7635, z1=1.5925, y0=0.9786, y1=2.4644)          # contorno del telaio (faccia esterna)
GAIN = (1.10, 1.12, 1.14)                                         # RGB
PPM_L = 700; PADR = 2; D_ATLAS = 0.12                               # l'atlante e' stato cotto per 12 cm di profondita': le strisce si rimappano su D

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

def compress_highlights(img, knee=185.0, k=0.30):
    """i riflessi speculari dell'ottone (nella foto) sono macchie quasi bianche: sopra `knee` la luminosita' si comprime"""
    f = img.astype(np.float32); L = f.max(axis=2, keepdims=True); gain = np.where(L > knee, (knee + (L - knee) * k) / np.maximum(L, 1.0), 1.0)
    return np.clip(f * gain, 0, 255).astype(np.uint8)

def build():
    """parti: lista di dict(name, mesh, map, wall) e immagini jpeg"""
    g = np.array(GAIN[::-1], np.float32)[None, None, :]
    fr = np.clip(cv2.imread(f'{ASSETS}/frame_clean.png').astype(np.float32) * g, 0, 255).astype(np.uint8)
    at = compress_highlights(np.clip(cv2.imread(f'{ASSETS}/lining_atlas.png').astype(np.float32) * g, 0, 255).astype(np.uint8))
    rs = int(round(D_ATLAS * PPM_L)) + PADR; at[3 * rs:4 * rs] = at[2 * rs:3 * rs]       # i due fianchi sono la stessa striscia: stesso colore e niente riflesso solo a destra
    imgs = {'win_t': jpg(fr, 90), 'win_l': jpg(at, 88)}
    z0, z1, y0, y1 = (HOLE[k] for k in ('z0', 'z1', 'y0', 'y1')); fz0, fz1, fy0, fy1 = (FRAME[k] for k in ('z0', 'z1', 'y0', 'y1'))
    xf = X_WALL + D; xw = X_WALL; white = [(255, 255, 255)] * 4
    m1 = Mesh()
    m1._add([(xf, fy0, fz0), (xf, fy0, fz1), (xf, fy1, fz1), (xf, fy1, fz0)], white, [(0, 1, 2), (0, 2, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)])
    AH, AW = at.shape[:2]; nd = int(round(D_ATLAS * PPM_L)); m2 = Mesh()
    n_top = int(round(0.87 * PPM_L)); n_side = int(round(1.505 * PPM_L))
    # (indice della striscia nell'atlante, lunghezza in texel, punti del contorno del telaio, punti dell'apertura nel muro) all'inizio e alla fine della striscia
    strips = [(0, n_top, ((xf, fy1, fz0), (xf, fy1, fz1)), ((xw, y1, z0), (xw, y1, z1))),                  # alto (sotto)
              (1, n_top, ((xf, fy0, fz0), (xf, fy0, fz1)), ((xw, y0, z0), (xw, y0, z1))),                  # basso (davanzale)
              (2, n_side, ((xf, fy0, fz0), (xf, fy1, fz0)), ((xw, y0, z0), (xw, y1, z0))),                 # sinistra
              (3, n_side, ((xf, fy0, fz1), (xf, fy1, fz1)), ((xw, y0, z1), (xw, y1, z1)))]                 # destra
    for i, n, (fa, fb), (wa, wb) in strips:
        r0 = i * (nd + PADR); u1 = n / AW; vf = 1 - r0 / AH; vw = 1 - (r0 + nd) / AH
        m2._add([fa, fb, wb, wa], white, [(0, 1, 2), (0, 2, 3)], [(0, vf), (u1, vf), (u1, vw), (0, vw)])
    return [dict(name='win_frame', mesh=m1, map='win_t', wall='W'), dict(name='win_lining', mesh=m2, map='win_l', wall='W')], imgs

if __name__ == '__main__':
    p, im = build(); print([(q['name'], len(q['mesh'].P)) for q in p], {k: len(v) for k, v in im.items()}, wall_rects(), holes())
