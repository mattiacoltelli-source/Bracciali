# confronto foto vs render dai punti di vista delle foto registrate, ritaglio attorno a un riquadro 3D
import sys, os, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/s/reg')
import phototex as PT
def pair(pid, box, out, pad=0.08, scale=1.0, cmpdir='/tmp/claude-0/s/cmp3'):
    cam = PT.Cam(pid)
    (x0, y0, z0), (x1, y1, z1) = box
    pts = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    u, v, z = cam.project(pts)
    ph = cam.img; ren = cv2.imread(f'{cmpdir}/{pid}.png')
    ren = cv2.resize(ren, (ph.shape[1], ph.shape[0]), interpolation=cv2.INTER_CUBIC)
    xa, xb = int(u.min()), int(u.max()); ya, yb = int(v.min()), int(v.max())
    w = xb - xa; h = yb - ya; xa -= int(w * pad); xb += int(w * pad); ya -= int(h * pad); yb += int(h * pad)
    xa, ya = max(0, xa), max(0, ya); xb, yb = min(ph.shape[1], xb), min(ph.shape[0], yb)
    a = ph[ya:yb, xa:xb]; b = ren[ya:yb, xa:xb]
    both = np.concatenate([a, b], 1)
    if scale != 1.0: both = cv2.resize(both, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    cv2.imwrite(out, both); print(out, both.shape)
if __name__ == '__main__':
    pid = sys.argv[1]; box = eval(sys.argv[2]); out = sys.argv[3]; sc = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    pair(pid, box, out, scale=sc)
