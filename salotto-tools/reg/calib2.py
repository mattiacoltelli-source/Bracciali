import sys; sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, json
from calib import *
o = run(); r, cam, M = o['r'], o['cam'], o['M']
def corner_x(name, px_list, zT):
    im = [i for i in r.images.values() if i.name.startswith(name)][0]
    out = []
    for px in px_list:
        C0, d = ray(cam, im, px)
        Cp = M @ C0; dp = M @ d
        t = (zT - Cp[2]) / dp[2]
        out.append((Cp + t * dp))
    return np.array(out)
pts = corner_x('b4bfa2ec', [(270, 700), (275, 800), (280, 900)], o['zT'])
print('angolo T/A in unità SfM: x =', np.round(pts[:, 0], 4), ' y =', np.round(pts[:, 1], 3))
xA = float(np.median(pts[:, 0]))
L_u = o['xW'] - xA; W_u = o['zF'] - o['zT']; H_u = 1.90 + 1.93
print('unità: L=%.4f W=%.4f H=%.4f' % (L_u, W_u, H_u))
# scala ai minimi quadrati sulle misure dell'utente (7.4, 4.5, 3.0)
dims_u = np.array([L_u, W_u, H_u]); user = np.array([7.4, 4.5, 3.0])
s = (dims_u @ user) / (dims_u @ dims_u)
print('scala ottima s=%.4f -> dimensioni %s | scarti %% %s' % (s, np.round(dims_u * s, 3), np.round((dims_u * s / user - 1) * 100, 1)))
for nm, sv in (('W', 4.5 / W_u), ('L', 7.4 / L_u), ('H', 3.0 / H_u)): print('  scala da', nm, '=', round(sv, 4))
json.dump(dict(xA=xA, xW=o['xW'], zT=o['zT'], zF=o['zF'], yFloor=-1.93, yCeil=1.90, s=s), open('planes_u.json', 'w'))
