"""Assembla il pacchetto cifrato della stanza a foto: muri (senza quadri), pavimento (buchi riempiti), atlante dei mobili, foto dei quadri.
Uso: python3 build_pack.py <tag_muri> <tag_pavimento> <tag_facce> [out]"""
import sys, os, json, struct, base64, secrets, time
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from fill import diffuse_fill, scene_complete, wall_fill
from scene_def import BOXES, PRIMS, ITEMS

R = '/tmp/claude-0/s/reg/out'
KEYFILE = '/tmp/claude-0/s/pack.key'
PPM_W = int(os.environ.get('PPM_W', 300))   # px/m dei muri
PPM_F = int(os.environ.get('PPM_F', 300))   # px/m del pavimento
H = 3.0
L, W = 7.4, 4.5

def jpg(img, q=88):
    ok, b = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q, cv2.IMWRITE_JPEG_OPTIMIZE, 1])
    assert ok
    return b.tobytes()

def erode_valid(valid, k=7):
    return cv2.erode(valid.astype(np.uint8), np.ones((k, k), np.uint8)).astype(bool)

def walls(tag):
    P = json.load(open(f'{R}/paintings_final.json'))
    out = {}
    for wid in 'TWFA':
        d = np.load(f'{R}/wall3_{wid}_{tag}.npz'); img, valid = d['img'], d['valid']
        v = erode_valid(valid, 7)
        for pid, p in P.items():
            if p['wall'] != wid: continue
            x0 = int((p['u'] - p['w'] / 2 - 0.07) * PPM_W); x1 = int((p['u'] + p['w'] / 2 + 0.07) * PPM_W)
            y0 = int((H - (p['y'] + p['h'] / 2) - 0.07) * PPM_W); y1 = int((H - (p['y'] - p['h'] / 2) + 0.10) * PPM_W)
            v[max(y0, 0):y1, max(x0, 0):x1] = False
        img = img.copy(); img[~v] = 0
        out[wid] = wall_fill(img, v, PPM_W)
        if wid == 'T':   # ombra morbida sulla parete sotto i mobili sospesi (li' le foto non vedono: si sarebbe riempito di bianco)
            Hh, Ww = out[wid].shape[:2]
            sh = np.ones((Hh, Ww), np.float32)
            for bx in BOXES:
                if bx['grp'] != 'tv' or bx['min'][1] < 0.2 or bx['min'][1] > 0.4: continue
                x0b, x1b = int((bx['min'][0] - 0.03) * PPM_W), int((bx['max'][0] + 0.03) * PPM_W)
                y0b = bx['min'][1]
                rows = np.arange(Hh); yy = (H - (rows + 0.5) / PPM_W)
                prof = np.clip(0.46 + 0.36 * (1 - yy / y0b), 0.46, 0.92)          # scuro sotto il mobile, piu' chiaro verso terra
                prof = np.where(yy < y0b, prof, 1.0).astype(np.float32)
                sh[:, x0b:x1b] = np.minimum(sh[:, x0b:x1b], prof[:, None])
            sh = cv2.GaussianBlur(sh, (0, 0), 0.03 * PPM_W)
            out[wid] = (out[wid].astype(np.float32) * sh[..., None]).clip(0, 255).astype(np.uint8)
        print('muro', wid, out[wid].shape, 'validi', round(float(v.mean()), 3), flush=True)
    return out

def floor(tag):
    d = np.load(f'{R}/floor3_{tag}.npz'); img, valid = d['img'], d['valid']
    Hh, Ww = valid.shape
    v = erode_valid(valid, 9)
    n, lab = cv2.connectedComponents((~valid).astype(np.uint8), connectivity=4)
    # buco centrale (quello piu' grande che non tocca divano/TV): il piu' grande con centro dentro la stanza e lontano dai mobili
    best = None
    for i in range(1, n):
        m = lab == i
        if m.sum() < 20000: continue
        ys, xs = np.nonzero(m)
        cx, cz = xs.mean() / PPM_F, ys.mean() / PPM_F
        if 2.3 < cx < 4.7 and 0.7 < cz < 2.5 and (best is None or m.sum() > best[1]): best = (i, m.sum())
    work = img.copy()
    work[~v] = cv2.inpaint(img, (~v).astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA)[~v]
    if best:
        central = cv2.dilate((lab == best[0]).astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool) & ~v
        allowed = np.zeros_like(v); allowed[0:int(3.1 * PPM_F), int(0.2 * PPM_F):int(2.9 * PPM_F)] = True
        ys, xs = np.nonzero(central)
        src_ok = (v & allowed).astype(np.uint8)
        integ = cv2.integral(src_ok)
        found = None
        for pad in (36, 28, 20, 12):
            y0, y1 = max(0, ys.min() - pad), min(Hh, ys.max() + 1 + pad); x0, x1 = max(0, xs.min() - pad), min(Ww, xs.max() + 1 + pad)
            h, w = y1 - y0, x1 - x0
            ok = np.zeros((Hh - h + 1, Ww - w + 1), bool)
            for yy in range(0, Hh - h + 1):
                row = integ[yy + h, w:] - integ[yy, w:] - integ[yy + h, :Ww - w + 1] + integ[yy, :Ww - w + 1]
                ok[yy] = row >= h * w - 0          # finestra interamente valida
            if ok.any(): found = (pad, y0, y1, x0, x1, h, w, ok); break
        if found:
            pad, y0, y1, x0, x1, h, w, ok = found
            T = work[y0:y1, x0:x1].astype(np.float32)
            ring = (v[y0:y1, x0:x1] & ~central[y0:y1, x0:x1]).astype(np.uint8)
            M = np.dstack([ring] * 3).astype(np.float32)
            res = cv2.matchTemplate(work.astype(np.float32), T, cv2.TM_SQDIFF, mask=M) / max(1.0, M.sum())
            res[~ok] = np.inf
            iy, ix = np.unravel_index(np.argmin(res), res.shape)
            print('pavimento: sorgente buco centrale a', (int(ix), int(iy)), 'pad', pad, 'costo', round(float(res[iy, ix]), 1), flush=True)
            src = work[iy:iy + h, ix:ix + w]
            m = (cv2.dilate(central[y0:y1, x0:x1].astype(np.uint8), np.ones((5, 5), np.uint8)) * 255).astype(np.uint8)
            m[:2] = 0; m[-2:] = 0; m[:, :2] = 0; m[:, -2:] = 0
            work = cv2.seamlessClone(src, work, m, (x0 + w // 2, y0 + h // 2), cv2.NORMAL_CLONE)
            v = v | central
        else:
            print('pavimento: ATTENZIONE nessuna sorgente per il buco centrale: riempimento sfumato', flush=True)
    out = diffuse_fill(work, v, down=4, feather=3)
    # ombra sotto i mobili sospesi (il pavimento li' non si vede nelle foto: e' buio)
    shade = np.ones((Hh, Ww), np.float32)
    for b in BOXES:
        gap = b['min'][1]
        if gap < 0.05 or b['name'].startswith(('tv', 'soundbar', 'speaker', 'ripiano', 'colonna', 'pensile', 'tav_ripiano')): continue
        x0b, x1b = int(b['min'][0] * PPM_F), int(b['max'][0] * PPM_F); z0b, z1b = int(b['min'][2] * PPM_F), int(b['max'][2] * PPM_F)
        f = 0.28 if gap < 0.2 else 0.42
        shade[z0b:z1b, x0b:x1b] = np.minimum(shade[z0b:z1b, x0b:x1b], f)
    shade = cv2.GaussianBlur(shade, (0, 0), 6)
    out = (out.astype(np.float32) * shade[..., None]).clip(0, 255).astype(np.uint8)
    return out

def atlas(tag):
    arr = np.load(f'{R}/faces_{tag}.npy', allow_pickle=True)
    faces = {}
    for name, face, img, cov in arr:
        faces[(name, face)] = (img, cov)
    # schermo della TV: spento (nelle foto c'e' un video diverso a ogni scatto)
    k = ('tv', '+z')
    if k in faces:
        im = faces[k][0].copy(); h, w = im.shape[:2]
        ins = max(3, int(0.012 * 300))
        yy, xx = np.mgrid[0:h - 2 * ins, 0:w - 2 * ins].astype(np.float32)
        base = np.stack([np.full(yy.shape, 20), np.full(yy.shape, 14), np.full(yy.shape, 12)], -1).astype(np.float32)   # BGR: nero-bluastro
        g = np.clip(1.0 - (xx / (w - 2 * ins) * 0.6 + yy / (h - 2 * ins) * 0.4), 0, 1)
        shine = (np.exp(-(((xx / (w - 2 * ins) - 0.28) ** 2) / 0.03 + ((yy / (h - 2 * ins) - 0.2) ** 2) / 0.05)) * 14)[..., None]
        base = base + g[..., None] * 6 + shine
        im[ins:h - ins, ins:w - ins] = base.clip(0, 255).astype(np.uint8)
        faces[k] = (im, 1.0)
    used = {(bx['name'], f) for bx in BOXES for f in bx['faces']}
    keep = {}
    for key, (img, cov) in faces.items():
        if cov >= 0.25 and key in used:
            if key != ('tv', '+z'):   # niente alone di parete/sfondo sul bordo (le scatole sono precise a ~1-2 cm): si tolgono 1,5 cm per lato e si riallarga
                h, w = img.shape[:2]; n = max(2, int(0.015 * 300))
                if h > 4 * n and w > 4 * n: img = cv2.resize(img[n:h - n, n:w - n], (w, h), interpolation=cv2.INTER_CUBIC)
            keep[key] = img
    # impacchetta (shelf packing) in un atlante di larghezza 4096
    PAD = 2
    items = sorted(keep.items(), key=lambda kv: -kv[1].shape[0])
    AW = 4096
    x = y = rowh = 0; place = {}
    for key, img in items:
        h, w = img.shape[:2]
        if x + w + 2 * PAD > AW: x = 0; y += rowh; rowh = 0
        place[key] = (x + PAD, y + PAD); x += w + 2 * PAD; rowh = max(rowh, h + 2 * PAD)
    AH = y + rowh
    AH = int(np.ceil(AH / 4) * 4)
    at = np.zeros((AH, AW, 3), np.uint8); at[:] = (90, 90, 90)
    rects = {}
    for key, img in keep.items():
        px, py = place[key]; h, w = img.shape[:2]
        at[py:py + h, px:px + w] = img
        at[py - PAD:py, px:px + w] = img[:1]; at[py + h:py + h + PAD, px:px + w] = img[-1:]
        at[py:py + h, px - PAD:px] = img[:, :1]; at[py:py + h, px + w:px + w + PAD] = img[:, -1:]
        rects[key] = [px, py, px + w, py + h]
    print('atlante', at.shape, 'facce', len(keep), 'scartate', len(faces) - len(keep), flush=True)
    # colore piatto di ogni scatola = media delle sue facce con foto (le altre facce prendono quel colore)
    means = {}
    for (name, face), img in keep.items():
        means.setdefault(name, []).append(img.reshape(-1, 3).mean(axis=0))
    return at, rects, means

def encrypt(plain, key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = secrets.token_bytes(12)
    return b'SLT1' + iv + AESGCM(key).encrypt(iv, plain, None)

def main():
    tw, tf, ta = sys.argv[1], sys.argv[2], sys.argv[3]
    outp = sys.argv[4] if len(sys.argv) > 4 else '/tmp/claude-0/s/salotto.bin'
    t0 = time.time()
    images = {}
    wl = walls(tw)
    for wid, im in wl.items(): images[f'wall_{wid}'] = jpg(im, 90)
    fl = floor(tf)
    images['floor'] = jpg(fl, 88)
    cv2.imwrite(f'{R}/final_floor.jpg', fl, [cv2.IMWRITE_JPEG_QUALITY, 90])
    for wid, im in wl.items(): cv2.imwrite(f'{R}/final_wall_{wid}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    at, rects, means = atlas(ta)
    images['atlas'] = jpg(at, 90)
    cv2.imwrite(f'{R}/final_atlas.jpg', at, [cv2.IMWRITE_JPEG_QUALITY, 90])
    P = json.load(open(f'{R}/paintings_final.json'))
    art = {}
    for pid in P:
        a = cv2.imread(f'{R}/art_{pid}.png')
        images[f'art_{pid}'] = jpg(a, 90); art[pid] = f'art_{pid}'
    boxes = []
    for b in BOXES:
        d = dict(name=b['name'], min=b['min'], max=b['max'], grp=b['grp'], solid=b['solid'])
        d['color'] = b['color']
        if b.get('round'): d['round'] = b['round']
        d['faces'] = {f: rects[(b['name'], f)] for f in b['faces'] if (b['name'], f) in rects}
        d['flat'] = [f for f in b['flat']] + [f for f in b['faces'] if (b['name'], f) not in rects]
        boxes.append(d)
    spawn = dict(pos=[1.7, 1.6, 3.9], yaw=float(np.arctan2(-(4.2 - 1.7), -(0 - 3.9))))
    # immagini in un'unica area binaria
    blob = b''; imap = {}
    for name, data in images.items():
        imap[name] = dict(o=len(blob), n=len(data), t='image/jpeg'); blob += data
    man = dict(v=1, images=imap, walls={w: f'wall_{w}' for w in 'TWFA'}, floor='floor', atlas='atlas', atlasSize=[at.shape[1], at.shape[0]],
               boxes=boxes, prims=PRIMS, items=ITEMS, art=art, spawn=spawn)
    mj = json.dumps(man, separators=(',', ':')).encode()
    plain = struct.pack('<I', len(mj)) + mj + blob
    if os.path.exists(KEYFILE): key = base64.urlsafe_b64decode(open(KEYFILE).read().strip() + '==')
    else:
        key = secrets.token_bytes(32); open(KEYFILE, 'w').write(base64.urlsafe_b64encode(key).decode().rstrip('=')); os.chmod(KEYFILE, 0o600)
    enc = encrypt(plain, key)
    open(outp, 'wb').write(enc)
    print('pacchetto', outp, round(len(enc) / 1e6, 2), 'MB in chiaro', round(len(plain) / 1e6, 2), 'MB;', {k: round(v['n'] / 1e3) for k, v in imap.items()}, round(time.time() - t0), 's')

if __name__ == '__main__':
    main()
