"""Texture del vaso rosso (cilindro): la foto intorno al cilindro, ricavata dalle foto registrate che lo vedono.
Colonne = angolo (u=0 verso +z, cresce verso +x), righe = altezza (riga 0 in alto). Uso: FRAME_EXT=1 python3 vase_tex.py [out.jpg]"""
import os, sys
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
CX, CZ, R, Y0, H = 6.682, 0.30, 0.053, 0.341, 0.215
NU, NV = 256, 72
cams = sys.argv[2].split(',') if len(sys.argv) > 2 else ['50f7be75']
out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/s/vaso/vase_t.jpg'
fr = FR()
th = (np.arange(NU) + 0.5) / NU * 2 * np.pi
yy = Y0 + H * (1 - (np.arange(NV) + 0.5) / NV)
TH, YY = np.meshgrid(th, yy)
P = np.stack([CX + R * np.sin(TH), YY, CZ + R * np.cos(TH)], -1).reshape(-1, 3)
N = np.stack([np.sin(TH), np.zeros_like(TH), np.cos(TH)], -1).reshape(-1, 3)
acc = np.zeros((NU * NV, 3)); wt = np.zeros(NU * NV)
for c in cams:
    img = fr.image(c).astype(np.float32); Hh, Ww = img.shape[:2]
    img = cv2.GaussianBlur(img, (0, 0), 1.5)
    uv, z = fr.project(c, P)
    C = fr.cams[c]['C']; v = C[None, :] - P; d = np.linalg.norm(v, axis=1); cosv = (v * N).sum(1) / d
    ok = (z > 0.1) & (uv[:, 0] > 2) & (uv[:, 0] < Ww - 3) & (uv[:, 1] > 2) & (uv[:, 1] < Hh - 3) & (cosv > 0.30)
    col = cv2.remap(img, uv[:, 0].reshape(NV, NU).astype(np.float32), uv[:, 1].reshape(NV, NU).astype(np.float32), cv2.INTER_LINEAR).reshape(-1, 3)
    w = np.where(ok, np.clip(cosv, 0, 1) ** 1.5, 0.0)
    acc += col * w[:, None]; wt += w
    print(c, 'colonne coperte', int((w.reshape(NV, NU).max(0) > 0).sum()), 'su', NU)
tex = np.zeros((NV, NU, 3), np.float32); okm = (wt > 1e-6).reshape(NV, NU)
tex[okm] = (acc / np.maximum(wt, 1e-9)[:, None]).reshape(NV, NU, 3)[okm]
# colonne non viste: continuano con il colore dei bordi della zona vista (scurito: sono i lati che guardano la parete e il divisorio)
vis = okm.any(0)
cols = np.nonzero(vis)[0]
if len(cols) < NU:
    # la zona vista e' un arco: lo trovo come intervallo circolare
    gaps = np.nonzero(~vis)[0]
    # bordi: ultimo visto prima del buco e primo dopo
    first = cols[0]; last = cols[-1]
    if vis[0] and vis[-1]:   # arco spezzato a cavallo di u=0: cerco il buco continuo
        g0 = gaps[0]; g1 = gaps[-1]; left_edge = tex[:, g0 - 1].mean(0); right_edge = tex[:, g1 + 1].mean(0)
    else:
        left_edge = tex[:, last].mean(0); right_edge = tex[:, first].mean(0)
        g0, g1 = last + 1, first + NU - 1
    n = g1 - g0 + 1
    for k in range(n):
        t = (k + 0.5) / n; base = left_edge * (1 - t) + right_edge * t
        shade = 0.55 - 0.30 * np.sin(np.pi * t)     # il dietro e' il piu' scuro: guarda la parete
        tex[:, (g0 + k) % NU] = np.clip(base * shade, 0, 255)
    # sfumo il passaggio vista/non vista
    tex = np.concatenate([tex, tex, tex], 1); tex = cv2.GaussianBlur(tex, (0, 0), sigmaX=3.0, sigmaY=0.5)[:, NU:2 * NU]
tex8 = np.clip(tex, 0, 255).astype(np.uint8)
cv2.imwrite(out, tex8, [cv2.IMWRITE_JPEG_QUALITY, 90]); print('texture', tex8.shape, out, os.path.getsize(out), 'byte')
cv2.imwrite(out.replace('.jpg', '_big.png'), cv2.resize(tex8, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST))
