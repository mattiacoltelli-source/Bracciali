"""Toglie dal campo di quote del divano cio' che non e' divano: il bracciolo (ora e' una scatola smussata con le foto) e il piano del tavolino
con le rotelle che la scansione aveva incluso a sinistra del bracciolo. Parte sempre dall'originale (orig/sofa_h_full.bin): si puo' rilanciare."""
import json, numpy as np
D = '/tmp/claude-0/s/sofa'
m = json.load(open(f'{D}/sofa_meta.json')); nx, nz, c, x0, z0 = m['nx'], m['nz'], m['cell'], m['x0'], m['z0']
q = np.frombuffer(open(f'{D}/orig/sofa_h_full.bin', 'rb').read(), '<u2').reshape(nz, nx).copy()
xs = x0 + (np.arange(nx) + 0.5) * c; zs = z0 + (np.arange(nz) + 0.5) * c
cut = (xs[None, :] < 4.61) & (zs[:, None] >= 3.30)
print('celle tolte:', int(((q > 0) & cut).sum()), 'su', int((q > 0).sum()))
q[cut] = 0
open(f'{D}/sofa_h.bin', 'wb').write(q.astype('<u2').tobytes())
