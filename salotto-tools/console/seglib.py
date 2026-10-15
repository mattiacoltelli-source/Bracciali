"""Segmentazione a mano assistita (GrabCut con semi). Coordinate nello spazio anteprima (foto ridotta a 1100 px di lato lungo)."""
import os, cv2, numpy as np
D = os.environ['FOTO_DIR']
def load(foto):
    im = cv2.imread(f'{D}/{foto}-image.jpg'); H, W = im.shape[:2]; return im, max(H, W) / 1100.0
def grabcut(foto, box, fg=(), bg=(), fg_poly=(), bg_poly=(), prob_fg=None, it=10, scale=0.5, border=6):
    """fg/bg: liste di (x, y, r) cerchi in coordinate anteprima; *_poly: liste di poligoni [(x,y)...]; prob_fg: poligono dove si presume figura"""
    im, s = load(foto)
    x0, y0, x1, y1 = [int(v * s) for v in box]
    c = im[y0:y1, x0:x1].copy(); h, w = c.shape[:2]
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    if prob_fg:
        pm = np.zeros((h, w), np.uint8); cv2.fillPoly(pm, [np.array([[int(px * s - x0), int(py * s - y0)] for px, py in prob_fg], np.int32)], 1); mask[pm > 0] = cv2.GC_PR_FGD
    mask[:border, :] = cv2.GC_BGD; mask[:, :border] = cv2.GC_BGD; mask[:, -border:] = cv2.GC_BGD; mask[-border:, :] = cv2.GC_BGD
    def circ(lst, val):
        for px, py, r in lst: cv2.circle(mask, (int(px * s - x0), int(py * s - y0)), max(1, int(r * s)), val, -1)
    def poly(lst, val):
        for pl in lst: cv2.fillPoly(mask, [np.array([[int(px * s - x0), int(py * s - y0)] for px, py in pl], np.int32)], val)
    circ(bg, cv2.GC_BGD); poly(bg_poly, cv2.GC_BGD); circ(fg, cv2.GC_FGD); poly(fg_poly, cv2.GC_FGD)
    small = cv2.resize(c, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    ms = cv2.resize(mask, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(small, ms, None, bgd, fgd, it, cv2.GC_INIT_WITH_MASK)
    out = ((ms == cv2.GC_FGD) | (ms == cv2.GC_PR_FGD)).astype(np.uint8) * 255
    out = cv2.resize(out, (w, h), interpolation=cv2.INTER_LINEAR)
    out = cv2.GaussianBlur(out, (0, 0), 1.2); out = (out > 127).astype(np.uint8) * 255
    return c, out, (x0, y0, x1, y1), s
def overlay(c, m, path, scale=0.5):
    v = c.copy(); bgm = m < 128
    v[bgm] = (v[bgm] * 0.2 + np.array([0, 200, 0]) * 0.3).astype(np.uint8)
    cnt, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(v, cnt, -1, (0, 255, 255), 1)
    cv2.imwrite(path, cv2.resize(v, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 90])
