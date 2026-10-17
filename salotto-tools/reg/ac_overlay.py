import os, sys
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
from bake4 import *
import ac_obj as A
fr = FR(); cr = A.corner_room
hq = [cr(*p) for p in A.hood_quad()]; cq = [cr(*p) for p in A.chin_quad()]
zl, zr = 4.5 - (A.U_C - A.W / 2), 4.5 - (A.U_C + A.W / 2)
back_top = [np.array([0.0, A.Y_TOP, zl]), np.array([0.0, A.Y_TOP, zr])]
outs = []
for n, (x0, y0, x1, y1) in {'6d89137e': (960, 100, 1640, 480), '4bd3d963': (1040, 830, 1720, 1230)}.items():
    img = fr.image(n, 1.0); k = 2.0
    c = cv2.resize(img[y0:y1, x0:x1].copy(), None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    def P(p):
        uv, z = fr.project(n, np.array([p])); return (int((uv[0, 0] - x0) * k), int((uv[0, 1] - y0) * k))
    def line(a, b, col): cv2.line(c, P(a), P(b), col, 1, cv2.LINE_AA)
    for i in range(4): line(hq[i], hq[(i + 1) % 4], (0, 0, 255))
    for i in range(4): line(cq[i], cq[(i + 1) % 4], (0, 255, 255))
    line(hq[0], back_top[0], (255, 0, 0)); line(hq[1], back_top[1], (255, 0, 0)); line(back_top[0], back_top[1], (255, 0, 0))
    outs.append(cv2.resize(c, (1000, int(c.shape[0] * 1000 / c.shape[1]))))
h = min(o.shape[0] for o in outs)
cv2.imwrite('/tmp/claude-0/s/ac_overlay.jpg', np.hstack([o[:h] for o in outs]), [cv2.IMWRITE_JPEG_QUALITY, 86]); print([o.shape for o in outs])
