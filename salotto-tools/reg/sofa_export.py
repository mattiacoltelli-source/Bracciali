"""Riempie i buchi della texture del divano e prepara i dati per il pacchetto: quote 16 bit (2 cm) + texture JPEG (5 mm).
Uso: python3 sofa_export.py <tag_bake> [out_dir]"""
import os, sys, json
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from fill import push_pull
tag = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/claude-0/s/sofa'
d = np.load(f'/tmp/claude-0/s/reg/out/sofa_bake_{tag}.npz')
img = d['img']; valid = d['valid']; fpu = d['fp']; Hup = d['Hup']; X0 = float(d['X0']); Z0 = float(d['Z0']); cu = float(d['cu'])
nzu, nxu = img.shape[:2]
print('texture', img.shape, 'cella', cu, 'validi', round(float(valid[fpu].mean()), 3))
# riempimento dei texel non validi dell'impronta: push-pull dai texel validi (colori del tessuto)
# il tessuto e' grigio scuro: tutto cio' che e' chiaro o colorato (parete vista di sbieco, oggetti accanto, aloni dei cuscini) si scarta,
# tranne la camicia sul letto (zona fissa) che e' un oggetto vero
bgr = img.astype(np.int32); lum = bgr.mean(2); sat = bgr.max(2) - bgr.min(2)
fabric = (lum < 112) & (sat < 30)
xs_ = X0 + (np.arange(nxu) + 0.5) * cu; zs_ = Z0 + (np.arange(nzu) + 0.5) * cu
shirt = (xs_[None, :] > 5.30) & (xs_[None, :] < 6.05) & (zs_[:, None] > 2.85) & (zs_[:, None] < 3.40)
keep = fabric | shirt
# angolo del bracciolo vicino al totem rosso e al tavolino: i colori sono di quegli oggetti, il bracciolo e' di tessuto grigio
keep &= ~((xs_[None, :] > 3.80) & (xs_[None, :] < 4.32) & (zs_[:, None] > 3.20) & (zs_[:, None] < 4.50))
print('texel scartati perche non tessuto:', int((valid & fpu & ~keep).sum()))
w = (valid & fpu & keep).astype(np.float32)
# erodo di poco: il bordo dell'impronta contiene colori di pavimento/sfondo
w = cv2.erode(w, np.ones((3, 3), np.uint8))
filled = push_pull(img.astype(np.float32), w, levels=8)
out_img = np.where((w > 0)[..., None], img.astype(np.float32), filled)
# fuori impronta: colore medio, cosi' la compressione JPEG non sporca i bordi
outside = ~fpu
bgcol = out_img[fpu].mean(0)
out_img[outside] = bgcol
# fusione morbida tra i texel originali e quelli riempiti
a = cv2.GaussianBlur(w, (0, 0), 1.2)[..., None]
out_img = (img.astype(np.float32) * a + filled * (1 - a)) * (fpu[..., None]) + bgcol * (~fpu[..., None])
out_img = np.clip(out_img, 0, 255).astype(np.uint8)
ok, jb = cv2.imencode('.jpg', out_img, [cv2.IMWRITE_JPEG_QUALITY, 86, cv2.IMWRITE_JPEG_OPTIMIZE, 1])
open(f'{out}/sofa_t.jpg', 'wb').write(jb.tobytes())
cv2.imwrite(f'{out}/sofa_t_preview.jpg', out_img, [cv2.IMWRITE_JPEG_QUALITY, 90])
print('texture JPEG', len(jb) // 1024, 'KB')
# quote a 2 cm: il campo di quote e' stato campionato a 1 cm/UP: ridimensiono a 2 cm (media sulla sola impronta)
H = Hup.copy(); H[~fpu] = 0
f = cu / 0.02
nx2, nz2 = int(round(nxu * f)), int(round(nzu * f))
num = cv2.resize(np.where(fpu, H, 0).astype(np.float32), (nx2, nz2), interpolation=cv2.INTER_AREA)
den = cv2.resize(fpu.astype(np.float32), (nx2, nz2), interpolation=cv2.INTER_AREA)
H2 = np.where(den > 0.5, num / np.maximum(den, 1e-6), 0).astype(np.float32)
H2 = np.clip(H2, 0, 1.2)
YMAX = 1.275
q = np.clip(np.round(H2 / YMAX * 65535), 0, 65535).astype('<u2')
open(f'{out}/sofa_h.bin', 'wb').write(q.tobytes())
fab = out_img[(w > 0) & fabric]
mc = fab.reshape(-1, 3).mean(0)[::-1] if len(fab) else np.array([60, 60, 62])      # RGB
skirt = '#%02x%02x%02x' % tuple(int(min(255, v * 0.95)) for v in mc)
meta = dict(x0=X0, z0=Z0, cell=0.02, nx=nx2, nz=nz2, ymax=YMAX, tex=dict(nx=nxu, nz=nzu), skirt=skirt)
json.dump(meta, open(f'{out}/sofa_meta.json', 'w'))
print('quote', q.shape, 'min>0', float(H2[H2 > 0].min()), 'max', float(H2.max()), meta)
