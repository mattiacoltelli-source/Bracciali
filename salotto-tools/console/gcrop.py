"""Ritaglio con griglia numerata (coordinate in pixel della foto non distorta a piena risoluzione). Uso: gcrop.py pid x0 y0 x1 y1 out [zoom] [passo]"""
import sys, os, cv2, numpy as np
sys.path.insert(0, '/tmp/claude-0/s/reg')
import phototex as PT
pid = sys.argv[1]; x0, y0, x1, y1 = map(int, sys.argv[2:6]); out = sys.argv[6]
z = float(sys.argv[7]) if len(sys.argv) > 7 else 3.0; step = int(sys.argv[8]) if len(sys.argv) > 8 else 20
im = PT.Cam(pid).img[y0:y1, x0:x1].copy()
im = cv2.resize(im, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
for gx in range((x0 // step + 1) * step, x1, step):
    X = int((gx - x0) * z); strong = gx % (step * 5) == 0
    cv2.line(im, (X, 0), (X, im.shape[0]), (0, 255, 255) if strong else (110, 110, 110), 1)
    if strong: cv2.putText(im, str(gx), (X + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
for gy in range((y0 // step + 1) * step, y1, step):
    Y = int((gy - y0) * z); strong = gy % (step * 5) == 0
    cv2.line(im, (0, Y), (im.shape[1], Y), (0, 255, 255) if strong else (110, 110, 110), 1)
    if strong: cv2.putText(im, str(gy), (2, Y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
cv2.imwrite(out, im, [cv2.IMWRITE_JPEG_QUALITY, 90]); print(out, im.shape)
