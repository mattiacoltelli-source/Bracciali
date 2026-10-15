"""Lettura di un file .spz (Niantic, v2/v3): posizioni, opacita', colore base, scale, rotazioni. Uso: import spzload; g = spzload.load(path)"""
import gzip, struct
import numpy as np
SH_C0 = 0.28209479177387814
def load(path):
    d = gzip.decompress(open(path, 'rb').read())
    magic, ver, n, shd, frac, flags, res = struct.unpack('<IIIBBBB', d[:16])
    assert magic == 0x5053474e, 'non e un file spz'
    off = 16
    b = np.frombuffer(d, np.uint8)
    p = b[off:off + n * 9].reshape(n, 3, 3).astype(np.int32); off += n * 9
    v = p[..., 0] | (p[..., 1] << 8) | (p[..., 2] << 16)
    v = np.where(v & 0x800000, v - (1 << 24), v)
    pos = v.astype(np.float32) / float(1 << frac)
    alpha = b[off:off + n].astype(np.float32) / 255.0; off += n
    col = b[off:off + n * 3].reshape(n, 3).astype(np.float32); off += n * 3
    f_dc = (col / 255.0 - 0.5) / 0.15
    rgb = np.clip(0.5 + SH_C0 * f_dc, 0, 1)
    sc = b[off:off + n * 3].reshape(n, 3).astype(np.float32); off += n * 3
    scale = np.exp(sc / 16.0 - 10.0)
    if ver >= 3:
        r = b[off:off + n * 4].reshape(n, 4).astype(np.uint32); off += n * 4
        comp = r[:, 0] | (r[:, 1] << 8) | (r[:, 2] << 16) | (r[:, 3] << 24)
        il = (comp >> 30).astype(np.int32)
        q = np.zeros((n, 4), np.float32); c = comp.copy(); ssum = np.zeros(n, np.float32)
        for i in (3, 2, 1, 0):
            mag = (c & 511).astype(np.float32); neg = ((c >> 9) & 1).astype(bool); c2 = c >> 10
            val = (np.sqrt(0.5) * mag / 511.0) * np.where(neg, -1.0, 1.0)
            use = il != i
            q[:, i] = np.where(use, val, 0)
            c = np.where(use, c2, c)
            ssum += np.where(use, val * val, 0)
        q[np.arange(n), il] = np.sqrt(np.maximum(0, 1 - ssum))
    else:
        r = b[off:off + n * 3].reshape(n, 3).astype(np.float32); off += n * 3
        xyz = r / 127.5 - 1.0; w = np.sqrt(np.maximum(0, 1 - (xyz ** 2).sum(1)))
        q = np.concatenate([xyz, w[:, None]], 1)
    return dict(n=n, ver=ver, shd=shd, pos=pos, alpha=alpha, rgb=rgb, scale=scale, quat=q, sh_off=off, raw=d)  # quat = x,y,z,w
if __name__ == '__main__':
    import sys
    g = load(sys.argv[1]); P = g['pos']
    print('punti', g['n'], 'minimo', P.min(0).round(2), 'massimo', P.max(0).round(2))
    print('percentili 1/99 di x,y,z:', np.percentile(P, 1, axis=0).round(2), np.percentile(P, 99, axis=0).round(2))
    print('alpha medio %.2f, scala mediana %.4f (m), p10 %.4f, p90 %.4f' % (g['alpha'].mean(), np.median(g['scale']), np.percentile(g['scale'].mean(1), 10), np.percentile(g['scale'].mean(1), 90)))
