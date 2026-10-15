"""Ritaglio a risoluzione piena con griglia in pixel dell'immagine e (opz.) spigoli di scatole proiettati.
Uso: zoom.py cam x0 y0 x1 y1 out [grid=50] [boxes=a,b] [outw=1400]"""
import os, sys, json
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
from scene_def import BOXES
from ov import corners, EDGES
cam = sys.argv[1]; x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]; out = sys.argv[6]
grid = int(sys.argv[7]) if len(sys.argv) > 7 else 50
names = sys.argv[8].split(',') if len(sys.argv) > 8 and sys.argv[8] != '-' else []
outw = int(sys.argv[9]) if len(sys.argv) > 9 else 1400
fr = FR(); img = fr.image(cam)
crop = img[y0:y1, x0:x1].copy()
k = outw / crop.shape[1]
crop = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
for gx in range((x0 // grid + 1) * grid, x1, grid):
    X = int((gx - x0) * k); cv2.line(crop, (X, 0), (X, crop.shape[0]), (0, 255, 255), 1); cv2.putText(crop, str(gx), (X + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)
for gy in range((y0 // grid + 1) * grid, y1, grid):
    Y = int((gy - y0) * k); cv2.line(crop, (0, Y), (crop.shape[1], Y), (0, 255, 255), 1); cv2.putText(crop, str(gy), (2, Y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)
for b in BOXES:
    if b['name'] not in names: continue
    P = corners(b['min'], b['max']); uv, z = fr.project(cam, P)
    for a, c in EDGES:
        if z[a] > 0.1 and z[c] > 0.1:
            p = ((uv[a] - [x0, y0]) * k).astype(int); q = ((uv[c] - [x0, y0]) * k).astype(int)
            cv2.line(crop, tuple(p), tuple(q), (255, 0, 255), 1, cv2.LINE_AA)
    for i in range(8):
        p = ((uv[i] - [x0, y0]) * k).astype(int)
        cv2.putText(crop, f'{b["name"][:3]}{i}', tuple(p + [3, -3]), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 128, 0), 1, cv2.LINE_AA)
        print(b['name'], i, 'xyz', P[i].round(3), 'px', uv[i].round(0))
cv2.imwrite(out, crop, [cv2.IMWRITE_JPEG_QUALITY, 92])
