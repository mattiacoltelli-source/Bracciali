import sys, json, numpy as np
sys.path.insert(0, '/tmp/claude-0/s/reg')
import phototex as PT, credenza_obj as C
from scipy.optimize import least_squares
C.RACK.update(cx=0.1581, cz=0.5575, yaw=-0.4819, W=0.2148, D=0.1934, y1=1.1061)
# picks: (riga, estremo 'b' base / 't' punta) -> pixel
PICKS = {
 '3039c671': {(0,'b'): (2913.8, 553.8), (0,'t'): (3436.3, 474.4), (1,'t'): (3437.5, 660.0), (1,'b'): (2997.0, 674.0), (2,'b'): (2921.9, 836.9), (2,'t'): (3436.3, 810.0)},
 '6d89137e': {(0,'b'): (2622.7, 1201.7), (0,'t'): (2792.3, 1207.3), (1,'t'): (2800.7, 1258.3), (1,'b'): (2650.0, 1258.3), (2,'b'): (2623.3, 1316.7), (2,'t'): (2791.7, 1318.3)},
 '4bd3d963': {(0,'b'): (2664.6, 1948.1), (0,'t'): (2838.5, 1955.8), (1,'t'): (2849.2, 2006.9), (1,'b'): (2702.0, 2007.7), (2,'b'): (2669.2, 2065.4), (2,'t'): (2842.7, 2072.3)},
}
cams = {p: PT.Cam(p) for p in PICKS}
# parametri: lx, y0, y1, y2, lzb0, L0, lzb2, L2, lzt1
def endpoint(par, row, end):
    lx, y0, y1, y2, lzb0, L0, lzb2, L2, lzt1, lzb1 = par
    y = (y0, y1, y2)[row]
    if row == 0: lz = lzb0 if end == 'b' else lzb0 - L0
    elif row == 2: lz = lzb2 if end == 'b' else lzb2 - L2
    else: lz = lzb1 if end == 'b' else lzt1
    return C.rack_world(lx, y, lz)
def resid(par):
    r = []
    for p, pk in PICKS.items():
        for (row, end), (u0, v0) in pk.items():
            u, v, z = cams[p].project(endpoint(par, row, end)[None]); r += [u[0] - u0, v[0] - v0]
    return np.array(r)
x0 = np.array([0.046, 1.05, 0.95, 0.85, 0.14, 0.285, 0.14, 0.285, -0.17, 0.10])
r0 = resid(x0); print('rms iniziale', np.sqrt(np.mean(r0**2)).round(1))
import os
LX = float(os.environ.get('LXFIX', 'nan'))
if LX == LX:
    f2 = lambda q: resid(np.concatenate([[LX], q]))
    sol = least_squares(f2, x0[1:], loss='soft_l1', f_scale=5.0); sol.x = np.concatenate([[LX], sol.x])
else:
    sol = least_squares(resid, x0, loss='soft_l1', f_scale=5.0)
names = ['lx', 'y0', 'y1', 'y2', 'lzb0', 'L0', 'lzb2', 'L2', 'lzt1', 'lzb1']
print(dict(zip(names, sol.x.round(4))))
r = resid(sol.x); print('rms', np.sqrt(np.mean(r**2)).round(1), 'max', np.abs(r).max().round(1))
n = 0
for p, pk in PICKS.items():
    for key in pk: print(p, key, r[n:n+2].round(1)); n += 2
