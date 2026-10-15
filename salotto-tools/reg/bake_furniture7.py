"""Bake delle facce dei mobili in un atlante. Uso: python3 bake_furniture.py [scala_sorgenti] [tag]"""
import sys, time, json
sys.path.insert(0, '/tmp/claude-0/s/reg')
from bake4 import *
from scene_def import BOXES

# facce: (normale, origine (callable sul box), right, up, larghezza, altezza)
def face_def(b, f):
    (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
    X, Y, Z = x1 - x0, y1 - y0, z1 - z0
    if f == '+z': return (0, 0, 1), (x0, y0, z1), (1, 0, 0), (0, 1, 0), X, Y
    if f == '-z': return (0, 0, -1), (x1, y0, z0), (-1, 0, 0), (0, 1, 0), X, Y
    if f == '+x': return (1, 0, 0), (x1, y0, z1), (0, 0, -1), (0, 1, 0), Z, Y
    if f == '-x': return (-1, 0, 0), (x0, y0, z0), (0, 0, 1), (0, 1, 0), Z, Y
    if f == '+y': return (0, 1, 0), (x0, y1, z1), (1, 0, 0), (0, 0, -1), X, Z
    raise ValueError(f)

def face_points(b, f, ppm):
    n, o, r, u, W, H = face_def(b, f)
    w, h = max(4, int(round(W * ppm))), max(4, int(round(H * ppm)))
    j = (np.arange(w) + 0.5) / w * W; i = (np.arange(h) + 0.5) / h * H
    JJ, II = np.meshgrid(j, H - i)
    P = np.array(o)[None, :] + JJ.reshape(-1, 1) * np.array(r)[None, :] + II.reshape(-1, 1) * np.array(u)[None, :]
    return P, np.array(n, float), (h, w)

def fill_invalid(img, valid, fallback):
    if valid.all(): return img
    if valid.mean() < 0.05:
        out = img.copy(); out[:] = fallback; return out
    m = (~valid).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    out = cv2.inpaint(img, m, 4, cv2.INPAINT_TELEA)
    return out

def hex2bgr(h): return tuple(int(h[i:i + 2], 16) for i in (5, 3, 1))

if __name__ == '__main__':
    scale = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    tag = sys.argv[2] if len(sys.argv) > 2 else 'v1'
    fr = FR(); from cams_sel import select; names = select(fr)
    occ_all = [dict(min=(np.array(b['min']) - 0.012).tolist(), max=(np.array(b['max']) + 0.012).tolist(), name=b['name']) for b in BOXES]
    faces = []
    t0 = time.time()
    for b in BOXES:
        for f in b['faces']:
            P, n, shape = face_points(b, f, b['ppm'])
            img, valid, tot = bake(fr, P, n, shape, names, occ_all, skip=b['name'], scale=scale, power=4.0, smooth=1.0, tag=f"{b['name']}{f}", verbose=False, cos_pow=1.0, min_cos=0.08)
            cov = float(valid.mean())
            img = fill_invalid(img, valid, hex2bgr(b['color']))
            faces.append(dict(name=b['name'], face=f, img=img, cov=cov))
            print(b['name'], f, shape, 'cop', round(cov, 2), round(time.time() - t0), 's', flush=True)
    np.save(f'/tmp/claude-0/s/reg/out/faces_{tag}.npy', np.array([(fc['name'], fc['face'], fc['img'], fc['cov']) for fc in faces], dtype=object), allow_pickle=True)
    print('fatto', len(faces), 'facce')
