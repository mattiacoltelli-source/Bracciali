"""Ritaglio a risoluzione piena con griglia px e segmenti 3D candidati (colorati). 
Uso: zoomc.py cam x0 y0 x1 y1 out segs_json [grid] [outw]   segs: [[ [x,y,z],[x,y,z], 'color' ], ...]  colori: r,g,b,c,m,y,w"""
import os, sys, json
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
CO = dict(r=(0,0,255), g=(0,255,0), b=(255,0,0), c=(255,255,0), m=(255,0,255), y=(0,255,255), w=(255,255,255), o=(0,128,255))
cam = sys.argv[1]; x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]; out = sys.argv[6]
segs = json.loads(sys.argv[7]); grid = int(sys.argv[8]) if len(sys.argv) > 8 else 50; outw = int(sys.argv[9]) if len(sys.argv) > 9 else 1400
fr = FR(); img = fr.image(cam); crop = img[y0:y1, x0:x1].copy(); k = outw / crop.shape[1]
crop = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
if grid:
    for gx in range((x0 // grid + 1) * grid, x1, grid):
        X = int((gx - x0) * k); cv2.line(crop, (X, 0), (X, 8), (0, 255, 255), 1); cv2.putText(crop, str(gx), (X + 2, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)
    for gy in range((y0 // grid + 1) * grid, y1, grid):
        Y = int((gy - y0) * k); cv2.line(crop, (0, Y), (8, Y), (0, 255, 255), 1); cv2.putText(crop, str(gy), (10, Y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)
for s in segs:
    A, B = np.array(s[0], float), np.array(s[1], float); col = CO[s[2]]
    t = np.linspace(0, 1, 40)[:, None]; P = A + (B - A) * t
    uv, z = fr.project(cam, P)
    pts = ((uv - [x0, y0]) * k).astype(np.int32)
    cv2.polylines(crop, [pts.reshape(-1, 1, 2)], False, col, 1, cv2.LINE_AA)
cv2.imwrite(out, crop, [cv2.IMWRITE_JPEG_QUALITY, 92])
