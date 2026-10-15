import cv2, numpy as np, sys
pid = sys.argv[1]; out = sys.argv[2]; pts = eval(sys.argv[3]); r = int(sys.argv[4]) if len(sys.argv) > 4 else 40; z = int(sys.argv[5]) if len(sys.argv) > 5 else 6
im = cv2.imread(f'/tmp/claude-0/s/st3/und_new/{pid}.png'); tiles = []
for k, (cx, cy) in pts.items():
    x0, y0 = cx - r, cy - r; c = im[y0:y0 + 2 * r, x0:x0 + 2 * r].copy(); c = cv2.resize(c, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
    for g in range(0, 2 * r + 1, 10):
        cv2.line(c, (g * z, 0), (g * z, 2 * r * z), (0, 200, 200) if g % 20 == 0 else (90, 90, 90), 1); cv2.line(c, (0, g * z), (2 * r * z, g * z), (0, 200, 200) if g % 20 == 0 else (90, 90, 90), 1)
        if g % 20 == 0: cv2.putText(c, str(x0 + g), (g * z + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1); cv2.putText(c, str(y0 + g), (2, g * z + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    tiles.append(c)
n = len(tiles); cols = 2; rows = (n + 1) // 2
H, W = tiles[0].shape[:2]; canvas = np.zeros((rows * H, cols * W, 3), np.uint8)
for i, t in enumerate(tiles): canvas[(i // cols) * H:(i // cols + 1) * H, (i % cols) * W:(i % cols + 1) * W] = t
cv2.imwrite(out, canvas, [cv2.IMWRITE_JPEG_QUALITY, 90]); print(out, canvas.shape)
