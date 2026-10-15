"""Assembla il pacchetto cifrato della stanza a foto: muri (senza quadri), pavimento (buchi riempiti), atlante dei mobili, foto dei quadri.
Uso: python3 build_pack.py <tag_muri> <tag_pavimento> <tag_facce> [out]"""
import sys, os, json, struct, base64, secrets, time
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np, cv2
from fill import diffuse_fill, scene_complete, wall_fill
from scene_def import BOXES, PRIMS, ITEMS
import shelf_unit, shelf_tex, console_obj, ledges, credenza_obj, wall_obj

R = '/tmp/claude-0/s/reg/out'
KEYFILE = '/tmp/claude-0/s/pack.key'
PPM_W = int(os.environ.get('PPM_W', 300))   # px/m dei muri
PPM_F = int(os.environ.get('PPM_F', 300))   # px/m del pavimento
H = 3.0
L, W = 7.1, 4.5
L_A_O = W   # parete A: u = W - z

def jpg(img, q=88):
    ok, b = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q, cv2.IMWRITE_JPEG_OPTIMIZE, 1])
    assert ok
    return b.tobytes()

def erode_valid(valid, k=7):
    return cv2.erode(valid.astype(np.uint8), np.ones((k, k), np.uint8)).astype(bool)

# (u0, u1, y0, y1, morbido) in metri, sistema nuovo: fasce della parete TV da rifare per diffusione. A sinistra e sopra il mobile a mensole (x 3,54-4,25) la pianta e i tralci si proiettavano sul muro
# (morbido = tiene anche l'intonaco piu' scuro, per non schiarire il gradiente della luce); dietro alle mensole portaquadri e ai sei quadretti, ora in 3D, la parete va ripulita (fill nitido).
WALL_EXCL = {'T': [(3.18, 3.58, 0.55, 2.68, True), (3.18, 4.50, 2.20, 2.68, True), (4.70, 5.84, 1.94, 2.34, False), (5.98, 7.10, 1.94, 2.34, False)],
             'A': wall_obj.wall_rects(L_A_O)}       # parete A: interruttore e presa (ora in 3D, nella texture avevano la doppia immagine)

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
        if WALL_EXCL.get(wid):      # fasce da rifare per diffusione, sfumate sui bordi
            for soft in (True, False):
                rects = [r for r in WALL_EXCL[wid] if r[4] == soft]
                if not rects: continue
                v2 = v.copy(); M = np.zeros(v.shape, np.float32)
                for (ua, ub, ya, yb, _s) in rects:
                    sl = (slice(max(int((H - yb) * PPM_W), 0), int((H - ya) * PPM_W)), slice(max(int(ua * PPM_W), 0), int(ub * PPM_W)))
                    v2[sl] = False; M[sl] = 1.0
                img2 = img.copy(); img2[~v2] = 0
                fill2 = wall_fill(img2, v2, PPM_W, soft=soft).astype(np.float32)
                al = np.clip(cv2.GaussianBlur(M, (0, 0), 0.035 * PPM_W) * 1.6, 0, 1)[..., None]
                out[wid] = (out[wid].astype(np.float32) * (1 - al) + fill2 * al).clip(0, 255).astype(np.uint8)
        # ombra morbida sulla parete sotto i mobili sospesi (li' le foto non vedono: si sarebbe riempito di bianco)
        Hh, Ww = out[wid].shape[:2]
        floaters = []
        for bx in BOXES:
            if wid == 'T' and bx['grp'] == 'tv' and 0.2 <= bx['min'][1] <= 0.4:
                floaters.append((bx['min'][0] - 0.03, bx['max'][0] + 0.03, bx['min'][1]))
            if wid == 'A' and bx['grp'] == 'cred' and bx['name'] == 'credenza':
                floaters.append((L_A_O - bx['max'][2] - 0.03, L_A_O - bx['min'][2] + 0.03, bx['min'][1]))   # parete A: u = W - z
        if floaters:
            sh = np.ones((Hh, Ww), np.float32)
            rows = np.arange(Hh); yy = (H - (rows + 0.5) / PPM_W)
            for (ua, ub, y0b) in floaters:
                x0b, x1b = max(0, int(ua * PPM_W)), min(Ww, int(ub * PPM_W))
                prof = np.clip(0.46 + 0.36 * (1 - yy / y0b), 0.46, 0.92)          # scuro sotto il mobile, piu' chiaro verso terra
                prof = np.where(yy < y0b, prof, 1.0).astype(np.float32)
                sh[:, x0b:x1b] = np.minimum(sh[:, x0b:x1b], prof[:, None])
            sh = cv2.GaussianBlur(sh, (0, 0), 0.03 * PPM_W)
            out[wid] = (out[wid].astype(np.float32) * sh[..., None]).clip(0, 255).astype(np.uint8)
        if wid == 'T':   # fondo del vano di destra del mobile TV: la parete li' dentro e' in ombra (le foto la vedono solo di striscio, il resto sarebbe intonaco bianco)
            r0, r1, c0, c1 = int((H - 0.70) * PPM_W), int((H - 0.341) * PPM_W), int(6.49 * PPM_W), int(6.76 * PPM_W)
            dark = np.array([48, 55, 66], np.float32)     # BGR di (66,55,48): (48,40,35) misurato nella foto x il guadagno di normalizzazione delle texture
            out[wid][r0:r1, c0:c1] = np.minimum(out[wid][r0:r1, c0:c1].astype(np.float32), dark[None, None, :]).astype(np.uint8)
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
        if 2.0 < cx < 4.4 and 0.7 < cz < 2.5 and (best is None or m.sum() > best[1]): best = (i, m.sum())
    work = img.copy()
    work[~v] = cv2.inpaint(img, (~v).astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA)[~v]
    if best:
        central = cv2.dilate((lab == best[0]).astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool) & ~v
        allowed = np.zeros_like(v); allowed[0:int(3.1 * PPM_F), int(0.0 * PPM_F):int(2.6 * PPM_F)] = True
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

def clean_fabric(img, region=None, fallback=(64, 61, 59)):
    """Solo tessuto grigio scuro: scarta cio' che e' chiaro o colorato (parete, tavolino rosso, tavolino con le rotelle, camicia) e lo riempie col tessuto vicino."""
    from fill import push_pull
    bgr = img.astype(np.int32); lum = bgr.mean(2); sat = bgr.max(2) - bgr.min(2)
    ok = (lum < 105) & (lum > 14) & (sat < 26)
    if region is not None: ok &= region
    w = cv2.erode(ok.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    if w.mean() < 0.04:
        out = np.empty_like(img); out[:] = fallback; return out
    filled = push_pull(img.astype(np.float32), w, levels=8)
    a = cv2.GaussianBlur(w, (0, 0), 1.0)[..., None]
    return np.clip(img.astype(np.float32) * a + filled * (1 - a), 0, 255).astype(np.uint8)

def tidy_faces(faces):
    """Bracciolo: le foto dei suoi lati vedono anche cio' che ci sta davanti (il tavolino rosso a 3 cm, il tavolino con le rotelle) e il piano di sopra e' quasi
    sempre coperto dal piano rosso o visto di striscio: della foto si tiene il fronte (solo tessuto) e il pezzo davanti al montante; piano e retro sono tinta unita
    (colori misurati sulle foto: tessuto grigio scuro, un po' piu' chiaro sopra)."""
    fr = faces.get(('s_bracciolo', '-z'))
    if fr is None: return faces
    h, w = fr[0].shape[:2]
    reg = np.ones((h, w), bool); reg[:, int(0.80 * w):] = False; reg[:, :int(0.06 * w)] = False; reg[:int(0.10 * h), :] = False   # le fasce degli spigoli smussati vedono anche parete, tavolino e piano rosso
    front = clean_fabric(fr[0], reg); faces[('s_bracciolo', '-z')] = (front, fr[1])
    flat = lambda rgb, shape: np.full(shape + (3,), rgb[::-1], np.uint8)
    for f, rgb in (('+y', (62, 62, 59)), ('+x', (46, 46, 44))):
        k = ('s_bracciolo', f)
        if k in faces: faces[k] = (flat(rgb, faces[k][0].shape[:2]), 1.0)
    k = ('s_bracciolo', '-x')
    if k in faces: faces[k] = (flat((52, 52, 51), faces[k][0].shape[:2]), 1.0)     # il lato si vede solo per 16 cm davanti al montante: le foto li' sono sporche, tinta unita misurata
    return faces

def atlas(tag):
    arr = np.load(f'{R}/faces_{tag}.npy', allow_pickle=True)
    faces = {}
    for name, face, img, cov in arr:
        faces[(name, face)] = (img, cov)
    faces = tidy_faces(faces)
    # dentro le mensole il fondo e il fianco del pilastro sono texture sintetiche (colore del laccato + ombre calcolate), non foto
    SYN = {('dorso', '+z'): 'dorso', ('pilastro', '-x'): 'pilastro_x', ('pilastro', '+z'): 'pilastro_z', ('pannello', '+z'): 'plate'}
    for (nm, fc), kind in SYN.items():
        bx = next((b for b in BOXES if b['name'] == nm), None)
        if bx and (nm, fc) in faces:
            faces[(nm, fc)] = (shelf_tex.make_face(kind, faces[(nm, fc)][0].shape[:2], bounds=(bx['min'], bx['max'])), 1.0)
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
            if key != ('tv', '+z') and key not in SYN:   # niente alone di parete/sfondo sul bordo (le scatole sono precise a ~1-2 cm): si tolgono 1,5 cm per lato e si riallarga
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
    VT = os.environ.get('VASE_TEX', '/tmp/claude-0/s/vaso/vase_t.jpg')     # texture del vaso rosso (vase_tex.py)
    for pr in PRIMS:
        if pr.get('t') == 'cylt':
            if os.path.exists(VT): images[pr['map']] = open(VT, 'rb').read()
            else: print('ATTENZIONE: manca la texture del vaso', VT, flush=True)
    cv2.imwrite(f'{R}/final_atlas.jpg', at, [cv2.IMWRITE_JPEG_QUALITY, 90])
    P = json.load(open(f'{R}/paintings_final.json'))
    art = {}
    for pid in P:
        a = cv2.imread(f'{R}/art_{pid}.png')
        images[f'art_{pid}'] = jpg(a, 90); art[pid] = f'art_{pid}'
    SD = os.environ.get('SOFA_DIR', '/tmp/claude-0/s/sofa'); bins = {}
    sofa = None
    if os.path.exists(f'{SD}/sofa_h.bin') and os.path.exists(f'{SD}/sofa_t.jpg') and not os.environ.get('NO_SOFA'):
        sofa = json.load(open(f'{SD}/sofa_meta.json'))
        images['sofa_t'] = open(f'{SD}/sofa_t.jpg', 'rb').read(); bins['sofa_h'] = open(f'{SD}/sofa_h.bin', 'rb').read()
        sofa['h'] = 'sofa_h'; sofa['t'] = 'sofa_t'
    voxs = []
    USE_CONSOLE = bool(os.environ.get('CONSOLE_ASSETS')) and os.path.isdir(os.environ.get('CONSOLE_ASSETS', ''))     # oggetti sulla console in 3D vero (ritagli dalle foto)
    for vn in sorted(os.listdir(SD)) if os.path.isdir(SD) else []:
        if vn.startswith('vox_') and vn.endswith('.bin') and not os.environ.get('NO_VOX') and not (USE_CONSOLE and vn == 'vox_console.bin'):
            tag_ = vn[4:-4]; vm = json.load(open(f'{SD}/vox_{tag_}.json'))
            bins[f'vox_{tag_}'] = open(f'{SD}/{vn}', 'rb').read(); vm['bin'] = f'vox_{tag_}'; voxs.append(vm)
    # mobile a mensole: mesh a colori per vertice (mensole, pianta, vasi, fumetti)
    prims = [p for p in PRIMS if not (USE_CONSOLE and p.get('grp') in ('lampada', 'credenza'))]
    um = shelf_unit.build(); meta, blob_u = um.pack(); bins['shelf_unit'] = blob_u
    prims.append(dict(t='vmesh', bin='shelf_unit', nv=meta['nv'], ni=meta['ni']))
    print('mesh mensole: vertici', meta['nv'], 'indici', meta['ni'], round(len(blob_u) / 1e3), 'KB', flush=True)
    if USE_CONSOLE:
        console_obj.ASSETS = os.environ['CONSOLE_ASSETS']
        cparts, cimgs = console_obj.build(case_yaw=float(os.environ.get('CASE_YAW', '0')))
        images.update(cimgs); nvt = 0
        for cp in cparts:
            meta, blob_c = cp['mesh'].pack(); bins[f"cm_{cp['name']}"] = blob_c; nvt += meta['nv']      # i blocchi si chiamano cm_*: le texture cobj_* hanno nomi diversi (stesso nome = si sovrascrivono)
            d = dict(t='vmesh', bin=f"cm_{cp['name']}", nv=meta['nv'], ni=meta['ni'])
            if meta.get('uv'): d['uv'] = 1
            if cp.get('map'): d['map'] = cp['map']
            if cp.get('amap'): d['amap'] = cp['amap']; d['atest'] = cp.get('atest', 0.5)
            if cp.get('alpha'): d['alpha'] = cp['alpha']
            prims.append(d)
        print('oggetti console: parti', len(cparts), 'vertici', nvt, flush=True)
    if USE_CONSOLE:       # mensole portaquadri e quadretti (ritagli rettificati dalle foto, stesso insieme di ritagli della console)
        ledges.ASSETS = os.environ['CONSOLE_ASSETS']
        lparts, limgs = ledges.build(); images.update(limgs)
        for lp in lparts:
            meta, blob_l = lp['mesh'].pack(); bins[f"cm_{lp['name']}"] = blob_l
            d = dict(t='vmesh', bin=f"cm_{lp['name']}", nv=meta['nv'], ni=meta['ni'])
            if meta.get('uv'): d['uv'] = 1
            if lp.get('map'): d['map'] = lp['map']
            prims.append(d)
    wparts, wimgs = wall_obj.build(); images.update(wimgs)      # interruttore e presa sulla parete A
    for wp in wparts:
        meta, blob_w = wp['mesh'].pack(); bins[f"cm_{wp['name']}"] = blob_w
        prims.append(dict(t='vmesh', bin=f"cm_{wp['name']}", nv=meta['nv'], ni=meta['ni']))
    if USE_CONSOLE:       # vaso grande, portabottiglie con etichette e ciotola di rame sulla credenza (colori cotti dalle foto registrate)
        credenza_obj.MASKS = os.environ.get('VASE_MASKS', os.environ['CONSOLE_ASSETS'])        # maschere del vaso e ritagli delle etichette stanno con gli altri ritagli
        qparts, qimgs = credenza_obj.build(); images.update(qimgs); nvq = 0
        for qp in qparts:
            meta, blob_q = qp['mesh'].pack(); bins[f"cm_{qp['name']}"] = blob_q; nvq += meta['nv']
            d = dict(t='vmesh', bin=f"cm_{qp['name']}", nv=meta['nv'], ni=meta['ni'])
            if meta.get('uv'): d['uv'] = 1
            if qp.get('map'): d['map'] = qp['map']
            prims.append(d)
        print('oggetti credenza: parti', len(qparts), 'vertici', nvq, flush=True)
    boxes = []
    for b in BOXES:
        d = dict(name=b['name'], min=b['min'], max=b['max'], grp=b['grp'], solid=b['solid'])
        d['color'] = b['color']
        if b.get('round'): d['round'] = b['round']
        d['faces'] = {f: rects[(b['name'], f)] for f in b['faces'] if (b['name'], f) in rects}
        d['flat'] = [f for f in b['flat']] + [f for f in b['faces'] if (b['name'], f) not in rects]
        if b.get('hidden'):   # solo ostacolo per la camminata (es. il vano delle mensole): non si disegna
            d['hidden'] = True; d['faces'] = {}; d['flat'] = []
        if sofa and b['name'].startswith('s_') and not b.get('vis'):   # il divano vero e' il campo di quote: le scatole restano solo come ostacoli (il bracciolo e' una scatola vera)
            d['hidden'] = True; d['faces'] = {}; d['flat'] = []
        boxes.append(d)
    spawn = dict(pos=[1.4, 1.6, 3.9], yaw=float(np.arctan2(-(3.9 - 1.4), -(0 - 3.9))))
    # immagini in un'unica area binaria
    blob = b''; imap = {}
    for name, data in images.items():
        imap[name] = dict(o=len(blob), n=len(data), t='image/jpeg'); blob += data
    for name, data in bins.items():
        imap[name] = dict(o=len(blob), n=len(data), t='application/octet-stream'); blob += data
    man = dict(v=1, images=imap, walls={w: f'wall_{w}' for w in 'TWFA'}, floor='floor', atlas='atlas', atlasSize=[at.shape[1], at.shape[0]],
               boxes=boxes, prims=prims, items=ITEMS, art=art, spawn=spawn)
    if sofa: man['sofa'] = sofa
    if voxs: man['vox'] = voxs
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
