"""Pulizia del divano (campo di quote + texture), senza nuove foto: la scansione lascia sulla seduta e sullo schienale pieghe e grumi di 4-10 cm che il divano vero non ha
(un divano di tessuto grigio scuro con cuscini lisci) e sulla texture macchie rosse e bianche (il tavolino rosso e i cuscini proiettati sul divano) e puntini chiari.
- quote: riduzione del rumore a variazione totale (spiana le pieghe di qualche cm e tiene i gradini veri: bracciolo, schienale, bordo della chaise) con le celle fuori impronta riempite col piu' vicino per non
  abbassare i bordi; la sagoma si ammorbidisce (apertura/chiusura + gaussiana sulla maschera) per togliere il bordo ondulato dello schienale;
- texture: i pixel scuri e poco saturi sono tessuto; il resto (macchie rosse, bianchi, puntini) si ricostruisce per diffusione dal tessuto vicino; poi la crominanza si porta a un grigio neutro
  leggermente caldo, i riflessi puntiformi si schiacciano sulla mediana locale e un filtro bilaterale toglie la grana del rumore.
Uso: python3 sofa_clean.py [dir_in] [dir_out]  (default: SOFA_DIR e SOFA_DIR + '_clean')"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from scipy.ndimage import distance_transform_edt, median_filter

SD = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SOFA_DIR', '/tmp/claude-0/s/sofa')
OD = sys.argv[2] if len(sys.argv) > 2 else SD + '_clean'

def tv_denoise(f, weight, n_iter=120):
    """riduzione del rumore a variazione totale (ROF, algoritmo di Chambolle): spiana le pieghe e tiene i gradini veri (bracciolo, schienale)"""
    f = f.astype(np.float64); px = np.zeros_like(f); py = np.zeros_like(f); tau = 0.125
    def div(px, py):
        d = np.zeros_like(px); d[:, 0] += px[:, 0]; d[:, 1:] += px[:, 1:] - px[:, :-1]; d[0, :] += py[0, :]; d[1:, :] += py[1:, :] - py[:-1, :]; return d
    def grad(u):
        gx = np.zeros_like(u); gy = np.zeros_like(u); gx[:, :-1] = u[:, 1:] - u[:, :-1]; gy[:-1, :] = u[1:, :] - u[:-1, :]; return gx, gy
    for _ in range(n_iter):
        u = f - weight * div(px, py); gx, gy = grad(u)
        nrm = 1.0 + tau / weight * np.hypot(gx, gy)
        px = (px + tau / weight * gx) / nrm; py = (py + tau / weight * gy) / nrm
    return (f - weight * div(px, py)).astype(np.float32)

def clean_heights(y, valid, weight=0.07, smooth=1.8):
    """y in metri (celle fuori impronta = 0)"""
    idx = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    yf = y[idx[0], idx[1]].astype(np.float32)                       # le celle vuote copiano la piu' vicina: i bordi non si abbassano
    yf = tv_denoise(yf, weight)
    yf = cv2.GaussianBlur(yf, (0, 0), smooth)                       # niente terrazze della variazione totale
    # sagoma: apertura e chiusura leggere + gaussiana, soglia a 0,5
    m = valid.astype(np.uint8); k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.3) > 0.5
    return np.where(m, yf, 0.0).astype(np.float32), m

def clean_texture(tex, valid_cells, cell_ratio):
    """tex: BGR uint8 (nz*r, nx*r); valid_cells: maschera delle celle (nz, nx)"""
    from fill import push_pull
    bgr = tex.astype(np.float32); fp = cv2.resize(valid_cells.astype(np.uint8), (tex.shape[1], tex.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    lab = cv2.cvtColor(tex, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0]; a = lab[..., 1] - 128; b = lab[..., 2] - 128; chroma = np.hypot(a, b)
    # tessuto = scuro e poco saturo; il resto (macchie rosse/bianche, riflessi) e' da ricostruire
    med = median_filter(L, size=21); good = (L < med * 1.35 + 6) & (L < 120) & (chroma < 15)
    good &= fp
    good = cv2.erode(good.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    w = good.astype(np.float32)
    filled = push_pull(bgr, w, levels=8)
    out = np.where(good[..., None], bgr, filled)
    out = np.where(fp[..., None], out, bgr)
    # crominanza neutra, leggermente calda; luminanza: si tiene il dettaglio ma si schiacciano i picchi
    lab = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    Lh = lab[..., 0]; Lm = cv2.GaussianBlur(Lh, (0, 0), 6.0)
    Lh = np.minimum(Lh, Lm * 1.18 + 4)                                             # niente puntini chiari
    Lh = Lm + (Lh - Lm) * 0.8                                                      # un po' meno contrasto nella grana
    ca = cv2.GaussianBlur(lab[..., 1] - 128, (0, 0), 10.0) * 0.5; cb = cv2.GaussianBlur(lab[..., 2] - 128, (0, 0), 10.0) * 0.5
    lab2 = np.stack([Lh, np.clip(ca + 128, 0, 255), np.clip(cb + 128, 0, 255)], -1)
    res = cv2.cvtColor(np.clip(lab2, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    res = cv2.bilateralFilter(res, d=7, sigmaColor=14, sigmaSpace=4)
    return res

if __name__ == '__main__':
    os.makedirs(OD, exist_ok=True)
    meta = json.load(open(f'{SD}/sofa_meta.json'))
    H = np.frombuffer(open(f'{SD}/sofa_h.bin', 'rb').read(), dtype=np.uint16).reshape(meta['nz'], meta['nx'])
    y = H.astype(np.float32) * meta['ymax'] / 65535; valid = H > 0
    y2, m2 = clean_heights(y, valid)
    print('celle valide prima/dopo', int(valid.sum()), int(m2.sum()), '| alta frequenza prima %.4f dopo %.4f m' % (
        (y - cv2.GaussianBlur(y, (0, 0), 3))[valid].std(), (y2 - cv2.GaussianBlur(y2, (0, 0), 3))[m2].std()))
    H2 = np.clip(np.round(y2 / meta['ymax'] * 65535), 0, 65535).astype(np.uint16); H2[~m2] = 0
    open(f'{OD}/sofa_h.bin', 'wb').write(H2.tobytes())
    tex = cv2.imread(f'{SD}/sofa_t.jpg'); r = tex.shape[1] // meta['nx']
    t2 = clean_texture(tex, m2 | valid, r)
    ok, b = cv2.imencode('.jpg', t2, [cv2.IMWRITE_JPEG_QUALITY, 88, cv2.IMWRITE_JPEG_OPTIMIZE, 1]); assert ok
    open(f'{OD}/sofa_t.jpg', 'wb').write(b.tobytes()); json.dump(meta, open(f'{OD}/sofa_meta.json', 'w'))
    print('scritti', OD, '| texture', t2.shape, len(b), 'byte')
