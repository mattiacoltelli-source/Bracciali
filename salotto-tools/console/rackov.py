"""Sovrappone il telaio del portabottiglie (spigoli) e i cilindri delle bottiglie alle foto registrate, per aggiustare i parametri RACK. Uso: rackov.py out.jpg [pid ...]  (override: env RACK_JSON)"""
import sys, os, json, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/s/reg')
import phototex as PT, credenza_obj as C
if os.environ.get('RACK_JSON'): C.RACK.update(json.loads(os.environ['RACK_JSON']))
def draw(pid, zoom=1.0, pad=60):
    cam = PT.Cam(pid); im = cam.img.copy()
    W2, D2, y0, y1 = C.RACK['W'] / 2, C.RACK['D'] / 2, C.RACK['y0'], C.RACK['y1']
    cor = {(i, j, k): C.rack_world((D2 * (1 if i else -1)), (y1 if j else y0), (W2 * (1 if k else -1))) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    pts = np.array(list(cor.values())); u, v, z = cam.project(pts)
    edges = [((i, j, k), (i2, j2, k2)) for (i, j, k) in cor for (i2, j2, k2) in cor if (i, j, k) < (i2, j2, k2) and sum(a != b for a, b in zip((i, j, k), (i2, j2, k2))) == 1]
    for a, b in edges:
        ua, va, _ = cam.project(cor[a]); ub, vb, _ = cam.project(cor[b])
        col = (0, 0, 255) if (a[0] == 1 and b[0] == 1) else (0, 200, 255)
        cv2.line(im, (int(ua), int(va)), (int(ub), int(vb)), col, 2, cv2.LINE_AA)
    for b in C.bottles():
        for s in (0.0, b['L']):
            P = C.rack_world(b['lx'], b['y'], b['lzb'] + b['d'] * s); uu, vv, _ = cam.project(P); cv2.circle(im, (int(uu), int(vv)), 4, (0, 255, 0), -1)
    xa, xb, ya, yb = int(u.min()) - 200, int(u.max()) + 200, int(v.min()) - pad, int(v.max()) + pad
    xa, ya = max(0, xa), max(0, ya)
    return im[ya:yb, xa:xb]
if __name__ == '__main__':
    out = sys.argv[1]; pids = sys.argv[2:] or ['3039c671', '8ebbe415', '6d89137e', '4bd3d963']
    tiles = []
    for p in pids:
        t = draw(p); sc = 560.0 / t.shape[0]; t = cv2.resize(t, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA); tiles.append(t)
    h = max(t.shape[0] for t in tiles); tiles = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 6, cv2.BORDER_CONSTANT) for t in tiles]
    cv2.imwrite(out, np.concatenate(tiles, 1), [cv2.IMWRITE_JPEG_QUALITY, 92]); print(out)
