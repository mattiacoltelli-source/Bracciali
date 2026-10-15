import sys, time, json
sys.path.insert(0, '/tmp/claude-0/s/reg')
from bake4 import *
from scene_def import BOXES, as_occluders
fr = FR(); names = sorted(fr.cams)
occ = as_occluders(BOXES)
ppm = float(sys.argv[1]); tag = sys.argv[2]; scale = float(sys.argv[3])
t0 = time.time()
P, shape = floor_points(fr, ppm)
img, valid, tot = bake(fr, P, (0, 1.0, 0), shape, names, occ, scale=scale, power=3.0, smooth=ppm / 100.0, tag='floor', verbose=False, cos_pow=1.2)
np.savez_compressed(f'/tmp/claude-0/s/reg/out/floor3_{tag}.npz', img=img, valid=valid)
out = img.copy(); out[~valid] = (0, 0, 255)
cv2.imwrite(f'/tmp/claude-0/s/reg/out/floor3_{tag}.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 90])
print('floor', shape, 'validi', round(float(valid.mean()), 3), round(time.time() - t0), 's', flush=True)
