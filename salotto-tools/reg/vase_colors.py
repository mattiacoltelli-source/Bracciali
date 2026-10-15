import os, sys, json
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
fr = FR()
ax = np.array([0.143, 1.937])      # asse del vaso (x, z)
BASE = 0.80
# profilo (y relativo, raggio) dalla scansione, con piede e labbro dalle foto
prof = [(0.000, 0.062), (0.010, 0.085), (0.028, 0.112), (0.050, 0.126), (0.070, 0.128), (0.090, 0.123), (0.110, 0.118), (0.130, 0.108), (0.150, 0.090), (0.170, 0.075),
        (0.190, 0.060), (0.210, 0.051), (0.235, 0.048), (0.260, 0.049), (0.285, 0.054), (0.305, 0.068), (0.325, 0.087), (0.345, 0.104), (0.365, 0.113), (0.375, 0.113)]
cams = ['3039c671', '8ebbe415', '6d89137e', '36b5d801', '4d2e8ed4']
imgs = {c: cv2.blur(fr.image(c, 0.5), (3, 3)) for c in cams}
out = []
for (yr, r) in prof:
    cols = []
    for c in cams:
        C = fr.cams[c]['C']; d = np.array([C[0] - ax[0], C[2] - ax[1]]); d /= np.linalg.norm(d)
        P = np.array([[ax[0] + d[0] * r, BASE + yr, ax[1] + d[1] * r]])
        uv, z = fr.project(c, P); uv = uv[0] * 0.5
        h, w = imgs[c].shape[:2]
        if z[0] > 0.3 and 2 <= uv[0] < w - 3 and 2 <= uv[1] < h - 3:
            cols.append(imgs[c][int(uv[1]), int(uv[0])][::-1])
    col = np.median(np.array(cols), axis=0) if cols else np.array([170, 150, 120])
    out.append([round(r, 3), round(yr, 3), '#%02x%02x%02x' % tuple(int(v) for v in col)])
print(json.dumps(out))
json.dump(out, open('/tmp/claude-0/s/sofa/vase_prof.json', 'w'))
