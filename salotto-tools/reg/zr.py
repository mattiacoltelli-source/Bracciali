"""Ritaglio automatico (piena risoluzione) intorno a una regione 3D, con scatole sovrapposte (facoltative) e segmenti.
Uso: zr.py out cams lo hi [boxes|-] [margin=0.15] [outw=1200] [segs_json]"""
import os, sys, json
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
from scene_def import BOXES
from ov import corners, EDGES, draw_boxes
CO = dict(r=(0,0,255), g=(0,255,0), b=(255,0,0), c=(255,255,0), m=(255,0,255), y=(0,255,255), w=(255,255,255), o=(0,128,255))
out = sys.argv[1]; cams = sys.argv[2].split(','); lo = json.loads(sys.argv[3]); hi = json.loads(sys.argv[4])
names = sys.argv[5].split(',') if len(sys.argv) > 5 and sys.argv[5] != '-' else []
margin = float(sys.argv[6]) if len(sys.argv) > 6 else 0.15; outw = int(sys.argv[7]) if len(sys.argv) > 7 else 1200
segs = json.loads(sys.argv[8]) if len(sys.argv) > 8 else []
fr = FR(); tiles = []
for cam in cams:
    img = fr.image(cam); H, W = img.shape[:2]
    uv, z = fr.project(cam, corners(lo, hi))
    if (z < 0.3).any(): print('camera non adatta', cam); continue
    x0, y0 = uv.min(axis=0); x1, y1 = uv.max(axis=0); mx, my = (x1 - x0) * margin, (y1 - y0) * margin
    x0, y0, x1, y1 = [int(v) for v in (max(x0 - mx, 0), max(y0 - my, 0), min(x1 + mx, W), min(y1 + my, H))]
    crop = img[y0:y1, x0:x1].copy(); k = outw / crop.shape[1]
    crop = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    for b in BOXES:
        if b['name'] not in names: continue
        P = corners(b['min'], b['max']); u, zz = fr.project(cam, P)
        for a, c in EDGES:
            if zz[a] > 0.1 and zz[c] > 0.1:
                cv2.line(crop, tuple(((u[a] - [x0, y0]) * k).astype(int)), tuple(((u[c] - [x0, y0]) * k).astype(int)), (255, 0, 255), 1, cv2.LINE_AA)
    for s in segs:
        A, B = np.array(s[0], float), np.array(s[1], float); t = np.linspace(0, 1, 40)[:, None]
        u, zz = fr.project(cam, A + (B - A) * t)
        cv2.polylines(crop, [((u - [x0, y0]) * k).astype(np.int32).reshape(-1, 1, 2)], False, CO[s[2]], 1, cv2.LINE_AA)
    cv2.putText(crop, f'{cam} [{x0},{y0}]-[{x1},{y1}]', (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)
    tiles.append(crop)
Hm = max(t.shape[0] for t in tiles)
tiles = [cv2.copyMakeBorder(t, 0, Hm - t.shape[0], 0, 4, cv2.BORDER_CONSTANT, value=(40, 40, 40)) for t in tiles]
cv2.imwrite(out, np.vstack(tiles) if len(tiles) > 1 and len(tiles) <= 2 else np.hstack(tiles) if False else np.vstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 90])
