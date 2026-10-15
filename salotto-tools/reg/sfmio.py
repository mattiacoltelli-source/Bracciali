import pycolmap, numpy as np, json
ROT = {n['name']: n['rot'] for n in json.load(open('/tmp/claude-0/s/sfm/names.json'))}
def load(path='/tmp/claude-0/s/sfm/work_hi/sparse_i/1'):
    r = pycolmap.Reconstruction(path)
    cam = list(r.cameras.values())[0]
    return r, cam
def gravity_frame(r):
    H = []
    for iid, im in r.images.items():
        n = im.name[:8]; R = im.cam_from_world().rotation.matrix()
        H.append(R.T @ (np.array([0, 1.0, 0]) if ROT[n] else np.array([1.0, 0, 0])))
    H = np.array(H); w, v = np.linalg.eigh(H.T @ H); g = v[:, 0]
    dn = np.array([im.cam_from_world().rotation.matrix().T @ (np.array([1.0, 0, 0]) if ROT[im.name[:8]] else np.array([0, 1.0, 0])) for im in r.images.values()])
    if (dn @ g).mean() < 0: g = -g
    up = -g; a = np.cross(up, [1.0, 0, 0]); a /= np.linalg.norm(a); b = np.cross(a, up)
    B = np.stack([a, up, b])
    res = np.degrees(np.arcsin(np.clip(np.abs(H @ g), 0, 1)))
    return B, res
def ray(cam, im, px):
    f, cx, cy, k = cam.params
    pose = im.cam_from_world(); R = pose.rotation.matrix(); t = pose.translation
    x = (px[0] - cx) / f; y = (px[1] - cy) / f; xu, yu = x, y
    for _ in range(6):
        r2 = xu * xu + yu * yu; xu = x / (1 + k * r2); yu = y / (1 + k * r2)
    d = np.array([xu, yu, 1.0]); return -R.T @ t, R.T @ d / np.linalg.norm(d)
