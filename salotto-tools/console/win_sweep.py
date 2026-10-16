import sys, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/s/reg')
import phototex as PT
PIDS = ['23446e1f', '896e2721', '36b5d801', '4d2e8ed4', '679522f2']
cams = [PT.Cam(p) for p in PIDS]
z0, z1, y0, y1 = 0.60, 1.90, 1.00, 2.45
ppm = 400
zs = np.arange(z0, z1, 1 / ppm); ys = np.arange(y1, y0, -1 / ppm)
Z, Y = np.meshgrid(zs, ys)
def profiles(d):
    P = np.stack([np.full_like(Z, 7.10 + d), Y, Z], -1).reshape(-1, 3); out = []
    for c in cams:
        u, v, _ = c.project(P); col = c.sample(u.reshape(Z.shape), v.reshape(Z.shape))
        g = cv2.cvtColor(np.clip(col, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        g = cv2.GaussianBlur(g, (0, 0), 1.2)
        gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3))
        pr = gx.mean(0); pr = pr - cv2.GaussianBlur(pr.reshape(1, -1), (0, 0), 25).ravel()     # profilo orizzontale dei bordi verticali, senza la parte lenta
        out.append(pr / (np.linalg.norm(pr) + 1e-6))
    return np.stack(out)
res = []
for d in np.arange(0.0, 0.40, 0.01):
    S = profiles(d); C = S @ S.T; n = len(S); score = (C.sum() - np.trace(C)) / (n * (n - 1))    # correlazione media fra le coppie
    res.append((float(d), float(score)))
for d, s in res: print(f'd={d:.2f} corr={s:.3f}')
print('migliore', max(res, key=lambda r: r[1]))
