"""Rettifica i sei quadretti dalla foto delle mensole portaquadri (angoli = bordo interno della cornice, cioe' il bordo esterno del passepartout bianco).
Scrive in ASSETS un'immagine per quadretto (poster_<nome>.png)."""
import os, cv2, numpy as np, json
A = '/tmp/claude-0/s/st3/assets'; os.makedirs(A, exist_ok=True)
und = cv2.imread('/tmp/claude-0/s/st3/work/ledges_und.png'); s = 4096 / 1100.0
det = json.load(open('/tmp/claude-0/s/st3/work/posters_det.json'))
def order(pts):
    p = np.array(pts, float); p = p[np.argsort(p[:, 1])]; top = p[:2][np.argsort(p[:2, 0])]; bot = p[2:][np.argsort(p[2:, 0])]
    return np.array([top[0], top[1], bot[1], bot[0]], np.float32)        # TL TR BR BL
quads = {n: order(det[n]['pts']) for n in ('shining', 'thing', 'jaws', 'evildead')}
quads['exorcist'] = (np.array([(216.5, 221.0), (318.5, 220.7), (312.4, 363.5), (210.5, 363.0)], np.float32) * s)
quads['clockwork'] = (np.array([(374.3, 219.0), (475.0, 219.0), (474.5, 360.0), (370.6, 360.8)], np.float32) * s)
OW, OH = 300, 408            # mat 0.216 x 0.294 m (rapporto 0,735)
dst = np.array([(0, 0), (OW, 0), (OW, OH), (0, OH)], np.float32)
for n, q in quads.items():
    Hm = cv2.getPerspectiveTransform(q.astype(np.float32), dst)
    out = cv2.warpPerspective(und, Hm, (OW, OH), flags=cv2.INTER_CUBIC)
    cv2.imwrite(f'{A}/poster_{n}.png', out)
    w_t = np.linalg.norm(q[1] - q[0]); w_b = np.linalg.norm(q[2] - q[3]); h_l = np.linalg.norm(q[3] - q[0]); h_r = np.linalg.norm(q[2] - q[1])
    print(n, 'larghezza', round((w_t + w_b) / 2), 'altezza', round((h_l + h_r) / 2), 'rapporto', round((w_t + w_b) / (h_l + h_r), 3))
sheet = np.hstack([cv2.imread(f'{A}/poster_{n}.png') for n in ('shining', 'exorcist', 'clockwork', 'thing', 'jaws', 'evildead')])
cv2.imwrite('/tmp/claude-0/s/st3/work/posters_sheet.jpg', cv2.resize(sheet, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 90])
