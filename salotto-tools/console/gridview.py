"""Ritaglio con griglia numerata per scegliere punti a mano. Uso: gridview.py foto x0 y0 x1 y1 out [scala] [passo]  (coordinate nell'anteprima 1100 px di larghezza)"""
import sys, cv2, numpy as np, os
d = os.environ['FOTO_DIR']
foto, x0, y0, x1, y1, out = sys.argv[1], *map(float, sys.argv[2:6]), sys.argv[6]
sc = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
step = int(sys.argv[8]) if len(sys.argv) > 8 else 10
im = cv2.imread(f'{d}/{foto}-image.jpg'); H, W = im.shape[:2]; s = max(H, W) / 1100.0
c = im[int(y0 * s):int(y1 * s), int(x0 * s):int(x1 * s)].copy()
z = sc * 1.0 * (1.0)   # px del ritaglio originale -> immagine mostrata
c = cv2.resize(c, None, fx=z, fy=z, interpolation=cv2.INTER_AREA)
# griglia in coordinate anteprima
for gx in range(int(np.ceil(x0 / step) * step), int(x1) + 1, step):
    X = int((gx - x0) * s * z); col = (0, 255, 255) if gx % (step * 5) == 0 else (120, 120, 120)
    cv2.line(c, (X, 0), (X, c.shape[0]), col, 1)
    if gx % (step * 5) == 0 or step >= 20: cv2.putText(c, str(gx), (X + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
for gy in range(int(np.ceil(y0 / step) * step), int(y1) + 1, step):
    Y = int((gy - y0) * s * z); col = (0, 255, 255) if gy % (step * 5) == 0 else (120, 120, 120)
    cv2.line(c, (0, Y), (c.shape[1], Y), col, 1)
    if gy % (step * 5) == 0 or step >= 20: cv2.putText(c, str(gy), (2, Y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
cv2.imwrite(out, c, [cv2.IMWRITE_JPEG_QUALITY, 90]); print(out, c.shape)
