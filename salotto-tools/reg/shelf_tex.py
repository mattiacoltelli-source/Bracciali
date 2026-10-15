"""Texture del fondo beige e della parete del pilastro (dentro le mensole): colore chiaro del laccato + ombre portate dalle mensole e dagli oggetti,
calcolate con una luce direzionale dall'alto a sinistra e davanti (direzione ricavata dalle ombre nelle foto: il vertice dell'ombra della mensola C cade a y 1,40 sul pilastro).
Niente foto: i bake dalle foto dell'interno delle mensole sbavavano (le pose delle foto ravvicinate non sono abbastanza precise)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
import shelf_unit as SU

LIGHT_TO = np.array([-0.68, 0.545, 0.488]); LIGHT_TO /= np.linalg.norm(LIGHT_TO)      # verso la luce
LIT_PANEL = np.array([148, 138, 130], float)      # RGB del laccato beige al sole (dalle foto)
LIT_FACE = np.array([140, 131, 123], float)
SHADOW = np.array([0.43, 0.31, 0.27])             # moltiplicatore RGB in ombra: bruno scuro (rimbalzo del noce)

def _tri_in_poly(x, z, poly):
    """punti (x,z) dentro un poligono convesso (vertici in ordine, qualunque verso)"""
    n = len(poly); sgn = None; ok = np.ones(x.shape, bool)
    A = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    s = 1.0 if A > 0 else -1.0
    for i in range(n):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % n]
        cr = (bx - ax) * (z - az) - (bz - az) * (x - ax)
        ok &= (s * cr >= 0)
    return ok

def occlusion(P, boards, solids, clouds, steps=120, smax=0.9):
    """P: (N,3) punti; ritorna lo spessore ottico accumulato verso la luce (0 = luce piena)"""
    N = len(P); occ = np.zeros(N)
    ds = smax / steps
    for k in range(1, steps + 1):
        s = k * ds; Q = P + LIGHT_TO[None, :] * s
        for poly, y0, y1 in boards:
            m = (Q[:, 1] >= y0) & (Q[:, 1] <= y1) & _tri_in_poly(Q[:, 0], Q[:, 2], poly)
            occ += m * 6.0 * ds / 0.01 * 0.2
        for (c, r, h) in solids:           # cilindri verticali: c base, raggio r, altezza h
            m = (Q[:, 1] >= c[1]) & (Q[:, 1] <= c[1] + h) & ((Q[:, 0] - c[0]) ** 2 + (Q[:, 2] - c[2]) ** 2 <= r * r)
            occ += m * 6.0 * ds / 0.01 * 0.2
        for (mn, mx, dens) in clouds:      # volumi semi-trasparenti (foglie)
            m = (Q >= np.array(mn)[None, :]).all(1) & (Q <= np.array(mx)[None, :]).all(1)
            occ += m * dens * ds / 0.01 * 0.2
    return occ

def scene_occluders(U=SU.U):
    poly = SU.board_poly(U)
    boards = [(poly, yt - U['th'], yt) for yt in U['ys'].values()] + [(poly, U['base'][0], U['base'][1])]
    yA, yB, yC, yD = (U['ys'][n] for n in 'ABCD')
    solids = [((3.683, yD, 0.110), 0.034, 0.13), ((3.683, yD + 0.13, 0.110), 0.052, 0.094),                  # vaso a tulipano (stelo e coppa)
              ((3.763, yD, 0.150), 0.058, 0.13), ((3.763, yD + 0.13, 0.150), 0.014, 0.05),                    # vaso tondo
              ((3.672, yB, 0.125), 0.048, 0.10), ((3.805, yB, 0.125), 0.033, 0.039),                          # brocca, vasetto
              ((3.635, yC, 0.150), 0.034, 0.048), ((3.775, yC, 0.150), 0.034, 0.048),                         # vasetti dei fumetti
              ((3.745, yA, 0.115), 0.044, 0.094)]                                                              # vaso della pianta
    clouds = [((3.684, yC, 0.055), (3.737, yC + 0.178, 0.17), 3.0), ((3.742, yC, 0.038), (3.855, yC + 0.178, 0.050), 3.0),   # fumetti
              ((3.60, yA + 0.094, 0.02), (3.90, yA + 0.30, 0.21), 0.9), ((3.43, 1.84, 0.12), (3.60, 2.12, 0.30), 0.7),             # chioma e tralci
              ((3.60, yC + 0.048, 0.11), (3.67, yC + 0.12, 0.19), 0.7), ((3.74, yC + 0.048, 0.11), (3.81, yC + 0.10, 0.19), 0.7),
              ((3.77, yB + 0.039, 0.09), (3.84, yB + 0.075, 0.16), 0.7)]
    return boards, solids, clouds

def make_stem(shape):
    """fronte del pilastro: sotto il pannello si vede il gambo beige all'ombra del pannello (colori misurati sulla foto b4bfa2ec): un po' piu' scuro in alto"""
    h, w = shape
    t = (np.arange(h) / max(1, h - 1))[:, None] * np.ones((1, w))        # 0 in alto, 1 in basso
    base = np.array([127, 113, 100], float)
    k = 0.90 + 0.10 * np.clip(t * 3.0, 0, 1) - 0.04 * np.clip(t - 0.8, 0, 1) / 0.2
    img = base[None, None, :] * k[..., None]
    return np.clip(img, 0, 255)[..., ::-1].astype(np.uint8)

def make_plate(shape):
    """fronte del pannello scuro: grigio grafite con il gradiente verticale misurato nelle foto di fronte e1 (74 in alto, 33 in basso) e un po' piu' chiaro a destra;
    i riflessi delle luci (visti dalle foto a destra) dipendono dal punto di vista e non si dipingono"""
    h, w = shape
    t = 1.0 - (np.arange(h) / max(1, h - 1))[:, None] * np.ones((1, w))      # 1 in alto, 0 in basso
    xx = (np.arange(w) / max(1, w - 1))[None, :] * np.ones((h, 1))
    b = 33 + 41 * np.clip(t, 0, 1) ** 0.8 + 7 * (xx - 0.5)
    img = np.stack([b * 1.0, b * 1.0, b * 1.04], -1)
    return np.clip(img, 0, 255)[..., ::-1].astype(np.uint8)

def make_face(kind, shape, U=SU.U, bounds=None):
    if kind == 'pilastro_z': return make_stem(shape)
    if kind == 'plate': return make_plate(shape)
    """kind: 'dorso' (faccia +z, z = 0,034) o 'pilastro_x' (faccia -x a x = 3,855); shape = (h, w) in texel; bounds = (min, max) della scatola nel sistema nuovo"""
    (x0, y0, z0), (x1, y1, z1) = bounds
    h, w = shape; Hh = y1 - y0
    boards, solids, clouds = scene_occluders(U)
    ii = (np.arange(h) + 0.5) / h * Hh; jj = (np.arange(w) + 0.5) / w
    YY = (y1 - ii)[:, None] * np.ones((1, w))
    if kind == 'dorso':
        XX = (x0 + jj * (x1 - x0))[None, :] * np.ones((h, 1)); ZZ = np.full((h, w), z1 + 0.002)
        lit = LIT_PANEL
    else:                                     # pilastro, faccia -x: origine (x0, y0, z0), il verso destro e' +z
        XX = np.full((h, w), x0 - 0.002); ZZ = (z0 + jj * (z1 - z0))[None, :] * np.ones((h, 1))
        lit = LIT_FACE
    P = np.stack([XX, YY, ZZ], -1).reshape(-1, 3)
    occ = occlusion(P, boards, solids, clouds).reshape(h, w)
    sh = 1.0 - np.exp(-occ)                  # 0 = luce, 1 = ombra piena
    sh = cv2.GaussianBlur(sh.astype(np.float32), (0, 0), sigmaX=2.2, sigmaY=2.2)
    sh = np.clip(sh, 0, 1)
    # leggera variazione di luce: piu' chiaro in alto (le luci a binario sono sul soffitto), un poco piu' scuro ai bordi bassi
    grad = 1.04 - 0.10 * (1 - np.clip((YY - y0) / Hh, 0, 1))
    rgb = lit[None, None, :] * grad[..., None] * (1 - sh[..., None]) + (lit[None, None, :] * grad[..., None] * SHADOW[None, None, :]) * sh[..., None]
    rgb = np.clip(rgb, 0, 255)
    return rgb[..., ::-1].astype(np.uint8)    # BGR per cv2

if __name__ == '__main__':
    import scene_def as S
    out = {}
    for b in S.BOXES:
        if b['name'] == 'dorso': out['dorso'] = (b['min'], b['max'])
        if b['name'] == 'pilastro': out['pilastro'] = (b['min'], b['max'])
    # i box in scene_def sono nel sistema 'vecchio' meno DX gia' tolto: coincide col nuovo
    for name, shape, kind in (('dorso', (380, 95), 'dorso'), ('pilastro', (461, 71), 'pilastro_x')):
        img = make_face(kind, shape, bounds=out[name])
        cv2.imwrite(f'/tmp/claude-0/s/shelf/synth_{name}.png', img); print(name, img.shape)
