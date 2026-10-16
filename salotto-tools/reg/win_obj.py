"""La finestra della parete W (z 0,73-1,63 m), in 3D: buco nel muro, spalle svasate d'intonaco e telaio con i vetri 12 cm piu' dentro.
Prima il telaio era cotto nella texture del muro: le foto registrate lo vedono da 5-7 m con pose diverse e, siccome sta dietro il filo del muro, finiva sfocato e sdoppiato.
Ora: il telaio e' un piano a parte (x = 7,10 + 0,12) con la foto frontale dell'utente (non registrata) rimappata a 800 px/m, e le quattro spalle sono facce piane svasate fra l'apertura nel muro e il
contorno del telaio (piu' stretto di 4 cm per lato: nel muro l'apertura e' 0,904 m, il telaio 0,829 m). Il telaio esce dritto e simmetrico (console/win_prep.py: raddrizzamento con gli
otto angoli dei vetri e un riquadro ideale simmetrico; riflessi del fotografo coperti). Apertura e telaio sono rettangoli esatti: z 0,726-1,630 e 0,7635-1,5925,
y 0,925-2,466 e 0,9786-2,4644 (centro z = 1,178; bordo basso dei vetri a y = 0,995; scala 0,329 m per larghezza di vetro). Il manifesto lo dice a real.js (`holes`), che ritaglia la parete e attacca le
parti alla parete, come per le porte. La texture del telaio si porta alla luce del muro (guadagno per canale = intonaco cotto nel pacchetto / intonaco della foto frontale).
Le spalle erano ottone preso dalla foto frontale (cerniere comprese) e da un fianco la banda piu' lontana, grossa e dorata, contro quella vicina, sottile e senza riflessi, faceva sembrare il contorno
asimmetrico: nelle foto la finestra sta in uno sguardo d'intonaco bianco, quindi ora le spalle sono tinta unita d'intonaco (la mediana del muro attorno al buco) piu' scura verso il telaio, uguali a destra e a sinistra."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from meshlib import Mesh

ASSETS = os.environ.get('WIN_ASSETS', '/tmp/claude-0/s/st3/assets/win')
X_WALL = 7.10; D = 0.12                                           # filo del muro e profondita' del telaio
HOLE = dict(z0=0.726, z1=1.630, y0=0.925, y1=2.466)               # apertura nel muro
FRAME = dict(z0=0.7635, z1=1.5925, y0=0.9786, y1=2.4644)          # contorno del telaio (faccia esterna)
GAIN = (1.10, 1.12, 1.14)                                         # RGB
PLASTER = (205, 204, 200)                                          # intonaco attorno al buco: mediana RGB della texture del muro W (anello di 12-22 cm, senza il lato basso)
DEEP = 0.80                                                       # le spalle si scuriscono verso il telaio (ombra d'angolo)

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
    imgs = {'win_t': jpg(fr, 90)}
    z0, z1, y0, y1 = (HOLE[k] for k in ('z0', 'z1', 'y0', 'y1')); fz0, fz1, fy0, fy1 = (FRAME[k] for k in ('z0', 'z1', 'y0', 'y1'))
    xf = X_WALL + D; xw = X_WALL; white = [(255, 255, 255)] * 4
    m1 = Mesh()
    m1._add([(xf, fy0, fz0), (xf, fy0, fz1), (xf, fy1, fz1), (xf, fy1, fz0)], white, [(0, 1, 2), (0, 2, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)])
    # spalle: quattro facce piane tinta unita d'intonaco, dal filo del muro (colore pieno) al telaio (scurito); il colore e' moltiplicato per l'ombra della faccia (alto piu' scuro, davanzale piu' chiaro)
    plaster = np.array(PLASTER, float); deep = plaster * DEEP; ref = (X_WALL - 0.6, (y0 + y1) / 2, (z0 + z1) / 2); m2 = Mesh()
    for fa, fb, wb, wa in (((xf, fy1, fz0), (xf, fy1, fz1), (xw, y1, z1), (xw, y1, z0)),                  # alto (sotto)
                           ((xf, fy0, fz0), (xf, fy0, fz1), (xw, y0, z1), (xw, y0, z0)),                  # basso (davanzale)
                           ((xf, fy0, fz0), (xf, fy1, fz0), (xw, y1, z0), (xw, y0, z0)),                  # sinistra
                           ((xf, fy0, fz1), (xf, fy1, fz1), (xw, y1, z1), (xw, y0, z1))):                # destra
        m2.quad_grad([fa, fb, wb, wa], [deep, deep, plaster, plaster], ref=ref, two=True)
    return [dict(name='win_frame', mesh=m1, map='win_t', wall='W'), dict(name='win_lining', mesh=m2, map=None, wall='W')], imgs

if __name__ == '__main__':
    p, im = build(); print([(q['name'], len(q['mesh'].P)) for q in p], {k: len(v) for k, v in im.items()}, wall_rects(), holes())
