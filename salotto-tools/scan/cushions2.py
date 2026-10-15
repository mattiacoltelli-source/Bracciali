import sys, json
sys.path.insert(0, '/tmp/claude-0/s/splat')
import numpy as np, spzload
from scipy.cluster.vq import kmeans2
exec(open('/tmp/claude-0/s/sofa/cushions.py').read().split("res = []")[0])
rng = np.random.default_rng(0)
out = []
def fit(pts, name, color):
    c = pts.mean(0)
    u_, s, vt = np.linalg.svd(pts - c, full_matrices=False)
    proj = (pts - c) @ vt.T
    ext = np.percentile(proj, [4, 96], axis=0); size = ext[1] - ext[0]; cen = c + ((ext[0] + ext[1]) / 2) @ vt
    return dict(name=name, c=cen.tolist(), size=size.tolist(), axes=vt.tolist(), n=len(pts), color=color)
# beige: 3 cuscini lungo z (k-means su z)
pts = Qr[beige]
cent, lab = kmeans2(pts[:, 2:3], np.array([[2.9], [3.2], [3.5]]), minit='matrix', iter=30)
order = np.argsort(cent[:, 0])
for rank, k in enumerate(order):
    sel = lab == k
    d = fit(pts[sel], f'beige{rank + 1}', '#c5b9a4'); out.append(d)
    print(d['name'], 'n', d['n'], 'c', np.round(d['c'], 3), 'size', np.round(d['size'], 3), 'assi', np.round(d['axes'], 2).tolist())
pm = Qr[must]
sel = (pm[:, 2] > 3.6)
d = fit(pm[sel], 'senape', '#8a6535'); out.append(d); print(d['name'], 'n', d['n'], 'c', np.round(d['c'], 3), 'size', np.round(d['size'], 3), 'assi', np.round(d['axes'], 2).tolist())
json.dump(out, open('/tmp/claude-0/s/sofa/cushions_fit.json', 'w'), indent=1)
