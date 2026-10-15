import os, cv2, numpy as np, json
d = os.environ['FOTO_DIR']
im = cv2.imread('work/ledges_und.png'); s = 4096 / 1100.0
boxes = {'shining': (35, 210, 172, 372), 'exorcist': (198, 208, 348, 368), 'clockwork': (362, 204, 492, 366), 'thing': (640, 204, 765, 372), 'jaws': (795, 203, 940, 372), 'evildead': (952, 200, 1092, 372)}
out = {}
for name, (x0, y0, x1, y1) in boxes.items():
    X0, Y0, X1, Y1 = [int(v * s) for v in (x0, y0, x1, y1)]
    c = im[Y0:Y1, X0:X1]; g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (0, 0), 2)
    dark = (g < 70).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cnts, hier = cv2.findContours(dark, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    for i, cn in enumerate(cnts):
        if hier[0][i][3] < 0: continue          # solo i fori (interno della cornice)
        a = cv2.contourArea(cn)
        if best is None or a > best[0]: best = (a, cn)
    vis = c.copy()
    if best is not None:
        a, cn = best; peri = cv2.arcLength(cn, True)
        ap = cv2.approxPolyDP(cn, 0.02 * peri, True)
        cv2.drawContours(vis, [ap], -1, (0, 255, 255), 3)
        pts = ap.reshape(-1, 2)
        out[name] = dict(area=float(a), n=len(pts), pts=[[float(px + X0), float(py + Y0)] for px, py in pts])
        print(name, 'area', int(a), 'vertici', len(pts), pts.tolist() if len(pts) <= 6 else '')
    cv2.imwrite(f'work/det_{name}.jpg', cv2.resize(vis, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA))
json.dump(out, open('work/posters_det.json', 'w'))
