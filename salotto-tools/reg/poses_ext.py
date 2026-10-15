import os, sys, json
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np
from frame import make_frame
fr = make_frame()
rots = {}
for f in ('/tmp/claude-0/s/sfm/names.json', '/tmp/claude-0/s/sfm/names_new.json'):
    try:
        for e in json.load(open(f)): rots[e['name']] = e.get('rot', 0)
    except Exception as ex: print('names', f, ex)
out = {}
for n, c in sorted(fr.cams.items()):
    R, t = c['R'], c['t']
    Csfm = -R.T @ t
    fwd = R.T @ np.array([0, 0, 1.0]); up = R.T @ np.array([0, -1.0, 0])
    C = fr.sfm_to_room(Csfm)
    tgt = fr.sfm_to_room(Csfm + fwd * 1.0)
    u = fr.sfm_to_room(Csfm + up * 1.0) - C
    u /= np.linalg.norm(u)
    vfov = 2 * np.degrees(np.arctan(fr.cy / fr.f))
    out[n] = dict(pos=C.tolist(), target=tgt.tolist(), up=u.tolist(), vfov=float(vfov), rot=rots.get(n, 0))
old = json.load(open('/tmp/claude-0/s/reg/out/poses.json'))
# controllo: le pose vecchie devono coincidere
mx = 0
for n in old:
    if n in out: mx = max(mx, np.abs(np.array(old[n]['pos']) - np.array(out[n]['pos'])).max(), np.abs(np.array(old[n]['target']) - np.array(out[n]['target'])).max())
print('differenza massima con le pose vecchie (m):', mx, '| nuove:', sorted(set(out) - set(old)))
json.dump(out, open('/tmp/claude-0/s/reg/out/poses_ext.json', 'w'), indent=1)
