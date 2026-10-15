import sys
sys.path.insert(0, '/tmp/claude-0/s/splat')
import numpy as np, spzload
path = sys.argv[1]; ang = 29.0
g = spzload.load(path); P = g['pos']; C = g['rgb']; A = g['alpha']; S = g['scale']
med = np.median(P, axis=0); r = np.linalg.norm(P - med, axis=1)
m = (r < 6) & (A > 0.3); P, C, A, S = P[m], C[m], A[m], S[m]
n = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))]); t = np.array([-n[1], n[0]])
v = P[:, [0, 2]] @ n; u = P[:, [0, 2]] @ t; y = P[:, 1]
# Barca: punti arancioni/scuri sul rettangolo
orange = (C[:, 0] > 0.45) & (C[:, 1] < 0.45) & (C[:, 2] < 0.3)
s = orange & (y > 0.5) & (y < 1.1) & (u > -0.4) & (u < 0.6)
print('barca arancio n', s.sum(), ' v percentili 5/50/95', np.percentile(v[s], [5, 50, 95]).round(3), ' u', np.percentile(u[s], [2, 98]).round(3), ' y', np.percentile(y[s], [2, 98]).round(3))
sa = (y > 0.5) & (y < 1.05) & (u > -0.25) & (u < 0.4)
hh, e = np.histogram(v[sa], bins=np.arange(-1.2, 0.2, 0.01)); top = np.argsort(hh)[::-1][:6]
print('piano parete (y 0.5-1.05): picchi v', [(round(float(e[i]), 2), int(hh[i])) for i in sorted(top)])
# console: piano superiore
st = (y > -0.14) & (y < -0.06) & (u > -0.6) & (u < 1.1)
hh, e = np.histogram(v[st], bins=np.arange(-1.2, 0.2, 0.01)); 
print('piano console (y -0.14..-0.06): profilo v', ' '.join(f'{e[i]:.2f}:{hh[i]}' for i in range(len(hh)) if hh[i] > 60))
# estensione in u del piano
sel = st & (v > -0.75) & (v < -0.5)
print('estensione u piano console', np.percentile(u[sel], [0.5, 99.5]).round(3))
# gambe: punti sotto il piano
sl = (y < -0.2) & (y > -0.9) & (u > -0.8) & (u < 1.2) & (v > -0.9) & (v < -0.3)
print('punti sotto il piano', sl.sum())
