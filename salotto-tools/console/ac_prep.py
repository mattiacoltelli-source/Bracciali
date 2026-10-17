"""Texture dello split dalla foto frontale dell'utente (81d8e52c, non registrata): i due quadrilateri della foto (cappuccio e fronte della bocca d'aria) si raddrizzano sui due rettangoli del modello 3D (reg/ac_obj.py).
Cappuccio: rette adattate ai massimi del gradiente sui bordi sinistro, destro e alto (angoli alti (640,9, 130,2) e (1671,8, 126,9)); il bordo basso e' la linea scura sopra la bocca d'aria, letta sulla foto ingrandita
(angoli (652,5, 489,0) e (1664,0, 483,0)). Bocca d'aria: stessi angoli alti sotto il cappuccio, angoli bassi (712, 641) e (1602, 638) letti sulla foto ingrandita. Il campionamento e' bilineare fra gli angoli
(come l'UV della mesh, che sul trapezio e' suddivisa): nessuna posa della camera, quindi la forma 3D si sceglie a parte (vedi ac_obj.py: le misure dalle foto registrate e dalla frontale non tornano a +-3 cm).
Uso: python3 ac_prep.py FOTO.jpg [OUT_DIR]  ->  OUT_DIR/ac_t.png (cappuccio in alto, 4 px di margine, fronte della bocca d'aria in basso)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reg')); sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
import ac_obj
HOOD_PX = [(640.9, 130.2), (1671.8, 126.9), (1664.0, 483.0), (652.5, 489.0)]            # alto-sx, alto-dx, basso-dx, basso-sx
CHIN_PX = [(659.0, 490.0), (1658.0, 484.0), (1602.0, 638.0), (712.0, 641.0)]
def bilinear(q, wpx, hpx):
    q = np.array(q, np.float32); s = (np.arange(wpx) + 0.5) / wpx; t = (np.arange(hpx) + 0.5) / hpx; S, T = np.meshgrid(s, t)
    top = q[0][None, None, :] * (1 - S[..., None]) + q[1][None, None, :] * S[..., None]; bot = q[3][None, None, :] * (1 - S[..., None]) + q[2][None, None, :] * S[..., None]
    return (top * (1 - T[..., None]) + bot * T[..., None]).astype(np.float32)
def warp(photo, q, wpx, hpx):
    px = bilinear(q, wpx, hpx)
    return cv2.remap(photo, px[..., 0], px[..., 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
if __name__ == '__main__':
    photo = cv2.imread(sys.argv[1]); out = sys.argv[2] if len(sys.argv) > 2 else '.'
    wpx, hh, ch = ac_obj.tex_size(); gap = 4; atlas = np.zeros((hh + gap + ch, wpx, 3), np.uint8)
    atlas[:hh] = warp(photo, HOOD_PX, wpx, hh); atlas[hh + gap:] = warp(photo, CHIN_PX, wpx, ch); atlas[hh:hh + gap] = atlas[hh - 1:hh]
    os.makedirs(out, exist_ok=True); cv2.imwrite(os.path.join(out, 'ac_t.png'), atlas); print('atlas', atlas.shape)
