import sys, os, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/s/reg')
import phototex as PT, credenza_obj as C
def draw(pid, pad=120):
    cam = PT.Cam(pid); im = cam.img.copy(); th = np.linspace(0, 2*np.pi, 90)
    def circ(y, r, col):
        P = np.stack([C.VASE_AXIS[0] + r*np.cos(th), np.full_like(th, C.Y_TOP + y), C.VASE_AXIS[1] + r*np.sin(th)], -1)
        u, v, z = cam.project(P); cv2.polylines(im, [np.stack([u, v], -1).astype(np.int32)], True, col, 2)
    for y, col in ((0.0, (0,255,0)), (0.10, (0,255,255)), (0.29, (255,128,0)), (0.40, (255,0,255))): circ(y, float(C._radius(y)), col)
    # profilo laterale (silhouette): punti del contorno per varie quote, nel piano perpendicolare alla vista
    C0 = cam.C; ax = np.array([C.VASE_AXIS[0], 0, C.VASE_AXIS[1]]); d = ax - C0; d[1] = 0; d /= np.linalg.norm(d); side = np.array([-d[2], 0, d[0]])
    for sgn in (-1, 1):
        pts = []
        for y in np.linspace(0, 0.40, 60):
            r = float(C._radius(y)); P = np.array([C.VASE_AXIS[0], C.Y_TOP + y, C.VASE_AXIS[1]]) + sgn * r * side; pts.append(P)
        u, v, z = cam.project(np.array(pts)); cv2.polylines(im, [np.stack([u, v], -1).astype(np.int32)], False, (0,0,255), 2)
    P0 = np.array([[C.VASE_AXIS[0], C.Y_TOP, C.VASE_AXIS[1]], [C.VASE_AXIS[0], C.Y_TOP + 0.4, C.VASE_AXIS[1]]]); u, v, z = cam.project(P0)
    cx, cy = int(u.mean()), int(v.mean())
    return im[max(0, cy-330):cy+330, max(0, cx-330):cx+330]
if __name__ == '__main__':
    out = sys.argv[1]; pids = sys.argv[2:]
    tiles = [draw(p) for p in pids]
    tiles = [cv2.resize(t, (500, int(500 * t.shape[0] / t.shape[1])), interpolation=cv2.INTER_AREA) for t in tiles]
    h = max(t.shape[0] for t in tiles); tiles = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 4, cv2.BORDER_CONSTANT) for t in tiles]
    cv2.imwrite(out, np.concatenate(tiles, 1), [cv2.IMWRITE_JPEG_QUALITY, 92]); print(out)
