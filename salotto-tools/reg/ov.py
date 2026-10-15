"""Sovrappone le scatole dei mobili alle foto, ritagliando intorno a una regione 3D. Uso: ov(cams, region, boxes, out, scale, names)"""
import sys, json
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
EDGES = [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)]
def corners(lo, hi): return np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])], float)
def draw_boxes(img, fr, cam, boxes, scale, colors=None, label=True, thick=1):
    for i, b in enumerate(boxes):
        P = corners(b['min'], b['max']); uv, z = fr.project(cam, P); uv = uv * scale
        col = (colors or {}).get(b['name'], (0, 255, 255))
        for a, c in EDGES:
            if z[a] > 0.1 and z[c] > 0.1 and np.all(np.abs(uv[[a, c]]) < 30000):
                cv2.line(img, tuple(np.round(uv[a]).astype(int)), tuple(np.round(uv[c]).astype(int)), col, thick, cv2.LINE_AA)
        if label and z.min() > 0.1:
            c0 = uv.mean(axis=0).astype(int)
            cv2.putText(img, b['name'], (int(c0[0]) - 20, int(c0[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
def crop_region(fr, cam, lo, hi, scale, margin=0.25):
    P = corners(lo, hi); uv, z = fr.project(cam, P); uv = uv * scale
    ok = z > 0.1
    if ok.sum() < 4: return None
    h, w = fr.image(cam, scale).shape[:2]
    uv = uv[ok]
    x0, y0 = uv.min(axis=0); x1, y1 = uv.max(axis=0)
    mx, my = (x1 - x0) * margin, (y1 - y0) * margin
    x0, y0, x1, y1 = [int(v) for v in (max(x0 - mx, 0), max(y0 - my, 0), min(x1 + mx, w), min(y1 + my, h))]
    if x1 - x0 < 120 or y1 - y0 < 60: return None
    return x0, y0, x1, y1
def ov(cams, boxes, out, scale=0.5, only=None, width=900, margin=0.10, max_h=640, thick=1, label=True, per_row=2, region=None):
    fr = FR(); tiles = []
    sel = [b for b in boxes if not only or b['name'] in only]
    for cam in cams:
        img0 = fr.image(cam, scale); h, w = img0.shape[:2]
        pts = []
        src = sel if region is None else [dict(min=region[0], max=region[1], name='r')]
        for b in src:
            uv, z = fr.project(cam, corners(b['min'], b['max'])); uv = uv * scale
            pts += [p for p, zz in zip(uv, z) if zz > 0.3]
        if len(pts) < 4: print('camera non adatta', cam); continue
        pts = np.array(pts); x0, y0 = pts.min(axis=0); x1, y1 = pts.max(axis=0)
        mx, my = (x1 - x0) * margin, (y1 - y0) * margin
        x0, y0, x1, y1 = [int(v) for v in (max(x0 - mx, 0), max(y0 - my, 0), min(x1 + mx, w), min(y1 + my, h))]
        if x1 - x0 < 100 or y1 - y0 < 60: print('crop troppo piccolo', cam); continue
        img = img0.copy()
        draw_boxes(img, fr, cam, sel, scale, thick=thick, label=label)
        crop = img[y0:y1, x0:x1]
        k = min(width / crop.shape[1], max_h / crop.shape[0])
        crop = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
        cv2.putText(crop, cam, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)
        tiles.append(crop)
    if not tiles: return
    H = max(t.shape[0] for t in tiles); Wd = max(t.shape[1] for t in tiles)
    tiles = [cv2.copyMakeBorder(t, 0, H - t.shape[0], 0, Wd - t.shape[1] + 4, cv2.BORDER_CONSTANT, value=(40, 40, 40)) for t in tiles]
    rows = []
    for i in range(0, len(tiles), per_row):
        row = tiles[i:i + per_row]; row += [np.zeros_like(tiles[0])] * (per_row - len(row)); rows.append(np.hstack(row))
    cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
if __name__ == '__main__':
    boxes = json.load(open('/tmp/claude-0/s/reg/furniture.json'))
    ov(sys.argv[2].split(','), boxes, sys.argv[1])
