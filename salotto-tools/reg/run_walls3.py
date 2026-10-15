import sys, time, json
sys.path.insert(0, '/tmp/claude-0/s/reg')
from bake4 import *
from scene_def import BOXES, as_occluders
fr = FR(); names = sorted(fr.cams)
occ = as_occluders(BOXES)
ppm = float(sys.argv[1]); tag = sys.argv[2]; scale = float(sys.argv[3])
for wid in sys.argv[4:] or ['T', 'W', 'F', 'A']:
    t0 = time.time()
    P, N, shape = wall_points(fr, wid, ppm)
    img, valid, tot = bake(fr, P, N, shape, names, occ, scale=scale, power=3.0, smooth=ppm / 100.0, tag=wid, verbose=False)
    np.savez_compressed(f'/tmp/claude-0/s/reg/out/wall3_{wid}_{tag}.npz', img=img, valid=valid)
    out = img.copy(); out[~valid] = (0, 0, 255)
    cv2.imwrite(f'/tmp/claude-0/s/reg/out/wall3_{wid}_{tag}.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(wid, shape, 'validi', round(float(valid.mean()), 3), round(time.time() - t0), 's', flush=True)
