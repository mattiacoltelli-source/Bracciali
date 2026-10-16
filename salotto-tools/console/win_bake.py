import sys, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/s/reg')
import phototex as PT
PIDS = ['23446e1f', '896e2721', '36b5d801', '4d2e8ed4', '679522f2']
def bake(d, z0=0.60, z1=1.90, y0=0.80, y1=2.65, ppm=500, pids=PIDS, power=3.0):
    cams = [PT.Cam(p) for p in pids]
    zs = np.arange(z0, z1, 1 / ppm) + 0.5 / ppm; ys = np.arange(y1, y0, -1 / ppm) - 0.5 / ppm
    Z, Y = np.meshgrid(zs, ys)
    P = np.stack([np.full_like(Z, 7.10 + d), Y, Z], -1); N = np.zeros_like(P); N[..., 0] = -1.0
    img, wt = PT.bake(P, N, cams, power=power, min_cos=0.12, kill_highlights=False)
    return img, wt
if __name__ == '__main__':
    d = float(sys.argv[1]); out = sys.argv[2]
    img, wt = bake(d); cv2.imwrite(out, np.clip(img, 0, 255).astype(np.uint8)); print(out, img.shape, float(wt.mean()))
