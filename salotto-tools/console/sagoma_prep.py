"""Prepara i ritagli per la statua a rilievo (reg/sagoma_obj.py) dalla foto e dalla maschera (sagoma_cut.py): la figura con la maschera, il davanti (la foto) e il dietro (la stessa foto con pelle,
telefono e braccialetti sostituiti dai colori vicini, cioe' capelli e vestito, e sfocata: niente volto sul retro). I buchi piccoli della maschera (fino a 6000 px^2) si chiudono: nella mesh
restavano come fessure che lasciavano vedere la faccia interna del davanti.
Uso: SAGOMA_FOTO=foto.jpg SAGOMA_MASK=maschera.png SAGOMA_ASSETS=cartella python3 sagoma_prep.py   (i ritagli sono foto di casa: stanno fuori dal repository, solo il pacchetto cifrato li contiene)"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reg'))
import numpy as np, cv2
from console_obj import fill_outside
from fill import push_pull
SRC = os.environ['SAGOMA_FOTO']; MASK = os.environ['SAGOMA_MASK']; OUT = os.environ['SAGOMA_ASSETS']; HEIGHT_M = float(os.environ.get('SAGOMA_ALTEZZA', '1.68'))
os.makedirs(OUT, exist_ok=True)
im = cv2.imread(SRC); m = cv2.imread(MASK, 0)
cnts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
for c, h in zip(cnts, hier[0]):
    if h[3] >= 0 and cv2.contourArea(c) < 6000: cv2.drawContours(m, [c], -1, 255, -1)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
n, lab, st, _ = cv2.connectedComponentsWithStats(m); m = ((lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])) * 255).astype(np.uint8)   # una sola figura
x, y, w, h = cv2.boundingRect(m); pad = 6
x0, y0, x1, y1 = x - pad, y - pad, x + w + pad, y + h + pad
c = im[y0:y1, x0:x1].copy(); mk = cv2.erode(m[y0:y1, x0:x1], np.ones((3, 3), np.uint8), iterations=1)      # via l'alone di parete sul bordo
cv2.imwrite(f'{OUT}/sagoma_rgb.png', c); cv2.imwrite(f'{OUT}/sagoma_mask.png', mk)
ys, xs = np.nonzero(mk > 127)
json.dump(dict(top_row=int(ys.min()), bottom_row=int(ys.max()), cx=float((xs.min() + xs.max()) / 2), w=int(c.shape[1]), h=int(c.shape[0]), height_m=HEIGHT_M), open(f'{OUT}/params.json', 'w'))
# ---- dietro: pelle (tinta arancio, saturazione media, chiara) e telefono si sostituiscono con i colori vicini ----
hsv = cv2.cvtColor(c, cv2.COLOR_BGR2HSV); H, S, V = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
skin = (H >= 3) & (H <= 19) & (S >= 55) & (S <= 200) & (V >= 115)
phone = np.zeros(mk.shape, np.uint8); cv2.fillPoly(phone, [np.array([[420 - x0, 376 - y0], [503 - x0, 376 - y0], [503 - x0, 548 - y0], [420 - x0, 548 - y0]], np.int32)], 1)   # riquadro del telefono (a mano)
rep = cv2.dilate(((skin | (phone > 0)) & (mk > 127)).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))) > 0
good = ((mk > 127) & ~rep).astype(np.float32)
back = push_pull(c.astype(np.float32), good, levels=9)
back = np.where(good[..., None] > 0, c.astype(np.float32), back)
back = cv2.GaussianBlur(cv2.medianBlur(back.clip(0, 255).astype(np.uint8), 15), (0, 0), 2.0)
cv2.imwrite(f'{OUT}/sagoma_back.png', fill_outside(back, mk))
print('ritaglio', c.shape, 'altezza px', ys.max() - ys.min())
