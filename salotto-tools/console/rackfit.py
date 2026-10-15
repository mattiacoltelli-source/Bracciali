import sys, json, numpy as np
sys.path.insert(0, '/tmp/claude-0/s/reg')
import phototex as PT
from scipy.optimize import least_squares
# corner picks: (i, j, k) i=+1 front(+lx)/-1 rear, j=1 top/0 bottom, k=+1 left(+lz)/-1 right; pixel in the undistorted full-res frame
PICKS = {
 '3039c671': {(1,1,1): (2937.5, 408.8), (1,1,-1): (3325, 361.9), (-1,1,1): (3000, 462), (-1,1,-1): (3353, 418), (1,0,1): (2938.8, 899.4), (-1,0,1): (3000, 918)},
 '6d89137e': {(1,1,1): (2628.3, 1168.3), (1,1,-1): (2749.3, 1166), (-1,1,1): (2665, 1162.7), (-1,1,-1): (2781.7, 1166.7), (1,0,1): (2627.3, 1348.3)},
 '4bd3d963': {(1,1,1): (2670.4, 1912.3), (1,1,-1): (2797.3, 1909.6), (-1,1,1): (2702.3, 1908.8), (-1,1,-1): (2826.2, 1912.3), (1,0,1): (2672.3, 2096.2)},
}
cams = {p: PT.Cam(p) for p in PICKS}
def world(par, i, j, k):
    cx, cz, yaw, W, D, H = par
    c, s = np.cos(yaw), np.sin(yaw); ed = np.array([c, 0, -s]); ew = np.array([s, 0, c])
    return np.array([cx, 0.801 + (H if j else 0.0), cz]) + (D / 2) * i * ed + (W / 2) * k * ew
def resid(par):
    r = []
    for p, pk in PICKS.items():
        for (i, j, k), (u0, v0) in pk.items():
            u, v, z = cams[p].project(world(par, i, j, k)[None]); r += [(u[0] - u0), (v[0] - v0)]
    return np.array(r)
x0 = np.array([0.14, 0.515, -0.672, 0.20, 0.21, 0.285])
r0 = resid(x0); print('rms iniziale', np.sqrt(np.mean(r0**2)).round(1))
sol = least_squares(resid, x0, loss='soft_l1', f_scale=6.0, bounds=([0.0, 0.3, -1.2, 0.15, 0.10, 0.22], [0.35, 0.7, -0.2, 0.32, 0.30, 0.40]))
print('parametri', dict(zip(['cx', 'cz', 'yaw', 'W', 'D', 'H'], sol.x.round(4))), 'yaw gradi', np.degrees(sol.x[2]).round(1))
r = resid(sol.x); print('rms', np.sqrt(np.mean(r**2)).round(1), 'max', np.abs(r).max().round(1))
n = 0
for p, pk in PICKS.items():
    for key in pk:
        print(p, key, r[n:n+2].round(1)); n += 2
