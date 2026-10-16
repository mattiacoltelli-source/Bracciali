"""Maschera della figura intera da una foto (statua a rilievo, vedi reg/sagoma_obj.py): GrabCut con un poligono 'probabile figura', semi sicuri dentro e fuori e i bordi dei capelli tracciati a mano
sulla foto ingrandita. Le coordinate sono i pixel della foto originale (899x1599): per un'altra foto vanno rifatte (guardare la foto con una griglia, come console/gridview.py).
Uso: python3 sagoma_cut.py foto.jpg maschera.png  (scrive anche maschera_ov.jpg: la foto con lo sfondo scurito, per controllare il contorno; poi sagoma_prep.py chiude i buchi piccoli e prepara i ritagli)"""
import sys, cv2, numpy as np
SRC = sys.argv[1]; OUT = sys.argv[2]
im = cv2.imread(SRC); H, W = im.shape[:2]
x0, y0, x1, y1 = 120, 90, 720, 1450                      # ritaglio di lavoro
c = im[y0:y1, x0:x1].copy(); h, w = c.shape[:2]
P = lambda pts: np.array([[x - x0, y - y0] for x, y in pts], np.int32)
mask = np.full((h, w), cv2.GC_BGD, np.uint8)
loose = [(380,125),(440,118),(505,132),(548,172),(572,240),(590,330),(612,420),(640,500),(668,590),(675,700),(650,752),(600,742),(578,770),(582,900),(580,1100),(584,1300),(580,1400),(545,1424),(420,1428),(330,1424),(298,1396),(300,1300),(302,1100),(302,1000),(286,950),(268,885),(262,800),(262,700),(250,650),(205,606),(228,545),(238,500),(222,452),(236,398),(258,328),(282,256),(318,188),(358,148)]
cv2.fillPoly(mask, [P(loose)], cv2.GC_PR_BGD)
# dentro il poligono: probabile figura
inner = [(382,135),(440,128),(498,142),(538,182),(560,242),(578,330),(598,420),(626,500),(652,590),(660,700),(640,742),(604,735),(566,760),(568,900),(566,1100),(570,1300),(566,1400),(540,1415),(420,1418),(332,1414),(312,1392),(314,1300),(316,1100),(314,1000),(296,950),(280,890),(274,800),(272,700),(260,655),(222,610),(240,548),(246,500),(234,455),(246,400),(268,330),(292,262),(326,196),(362,156)]
cv2.fillPoly(mask, [P(inner)], cv2.GC_PR_FGD)
def fg(poly): cv2.fillPoly(mask, [P(poly)], cv2.GC_FGD)
def bg(poly): cv2.fillPoly(mask, [P(poly)], cv2.GC_BGD)
# sicuro: vestito, viso, telefono, parte alta dei capelli, braccio sinistro, torso, calze
fg([(345,650),(500,650),(520,760),(540,900),(548,1300),(540,1370),(340,1370),(326,1300),(322,900),(336,760)])
fg([(332,470),(410,470),(410,640),(330,640)])
cv2.ellipse(mask, (385 - x0, 322 - y0), (52, 70), 0, 0, 360, cv2.GC_FGD, -1)
fg([(422,380),(500,380),(500,544),(424,544)])
fg([(372,172),(468,172),(478,232),(362,232)])
fg([(284,470),(304,470),(304,640),(288,640)])
fg([(395,1388),(432,1388),(432,1404),(395,1404)])
# bordi dei capelli (tracciati a mano sulla foto ingrandita): a sinistra e a destra e' parete
LH = [(436,128),(400,152),(385,170),(372,190),(362,215),(352,235),(345,255),(342,275),(340,295),(338,315),(333,350),(308,375),(290,400),(278,425),(272,445),(270,500),(270,560),(272,585)]
RH = [(505,126),(520,160),(527,185),(533,215),(539,250),(549,300),(559,350),(568,400),(577,440)]
bg([(100,80),(436,80)] + LH[::1] + [(272,585),(100,585)])
bg([(505,80),(720,80),(720,440),(577,440)] + RH[::-1])
bg([(322,1356),(350,1366),(350,1378),(322,1378)]); bg([(567,1236),(610,1236),(610,1334),(567,1334)])
# sicuro sfondo: panca e vestiti a sinistra, scarpa a destra, giacca, pavimento
bg([(120,860),(262,860),(262,1100),(120,1100)]); bg([(120,1100),(300,1100),(300,1450),(120,1450)])
bg([(590,1180),(720,1180),(720,1450),(590,1450)]); bg([(690,90),(720,90),(720,1100),(690,1100)])
bg([(120,90),(330,90),(330,125),(120,125)]); bg([(560,90),(720,90),(720,250),(560,250)])
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(c, mask, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
m = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8) * 255
full = np.zeros((H, W), np.uint8); full[y0:y1, x0:x1] = m
cv2.imwrite(OUT, full)
v = im.copy(); v[full < 128] = (v[full < 128] * 0.25 + np.array([0, 160, 0]) * 0.5).astype(np.uint8)
cnt, _ = cv2.findContours(full, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(v, cnt, -1, (0, 255, 255), 1)
cv2.imwrite(OUT.replace('.png', '_ov.jpg'), v[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 90])
print('area', (full > 0).sum(), 'bbox', cv2.boundingRect(full))
