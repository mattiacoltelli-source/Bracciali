"""Definizione dei mobili (scatole in coordinate stanza: x lungo la parete TV dall'angolo split, y su, z verso l'ingresso).
Misure ricavate dalle foto registrate (viste raddrizzate a griglia metrica + sovrapposizioni); le profondita' sono stime.
faces = facce texturizzate con le foto; flat = facce a tinta unita; le altre non si disegnano (nascoste da muri o altri mobili).
margin = quanto si ingrandisce la scatola quando fa da ostacolo per le texture di muri e pavimento."""
import numpy as np

DX = 0.30   # le misure qui sotto sono nel vecchio sistema (x dal vecchio piano A): la parete A vera sta a x = 0.30 del vecchio sistema
def B(name, x0, x1, y0, y1, z0, z1, color='#444444', faces=(), flat=(), ppm=200, margin=0.05, grp=None, solid=True, round=0.0, vis=False, hidden=False):
    x0, x1 = x0 - DX, x1 - DX
    return dict(name=name, min=[x0, y0, z0], max=[x1, y1, z1], color=color, faces=list(faces), flat=list(flat), ppm=ppm, margin=margin, grp=grp, solid=solid, round=round, vis=vis, hidden=hidden)

TV = dict(ppm=300, margin=0.035, grp='tv')
SOFA = dict(ppm=170, margin=0.07, grp='sofa')
FAB = '#3b3d40'

BOXES = [
    # --- parete TV (z = 0) ---
    B('colonna', 3.73, 4.14, 0.99, 2.19, 0.0, 0.18, '#b9b2a4', ['+z', '-x'], ['+y'], **TV),
    B('pensile', 4.14, 4.755, 1.00, 2.27, 0.0, 0.25, '#3c3b3a', ['+z', '+x'], ['+y'], **TV),
    B('cassettone', 4.24, 6.79, 0.34, 0.71, 0.0, 0.40, '#bcb4a6', ['+z', '-x'], ['+y', '+x'], **TV),
    B('ripiano', 5.00, 7.25, 0.71, 0.76, 0.0, 0.35, '#4a2f20', [], ['+z', '+y', '+x', '-x'], **TV),
    # vano a destra del mobile TV: a sinistra il vano aperto con il vaso rosso (fondo in noce a 34 cm; in fondo la parete, scura), poi un divisorio e un secondo vano buio, fianco destro in noce.
    # Facce a tinta unita con i colori misurati sulla foto 50f7be75 (le foto del vano da piu' angoli sbavano: il vano e' una rientranza, non un piano)
    B('vano_pav', 6.79, 7.25, 0.274, 0.341, 0.0, 0.40, '#33190d', [], ['+y', '+z', '+x'], **TV),
    B('vano_div', 7.06, 7.08, 0.341, 0.71, 0.0, 0.40, '#44291e', [], ['+z'], solid=False, **TV),          # il bordo davanti del divisorio, in noce
    B('vano_sx', 7.055, 7.06, 0.341, 0.71, 0.0, 0.40, '#403630', [], ['-x'], ppm=100, margin=0.0, grp='tv', solid=False),   # la sua faccia verso il vaso: scura come il fondo
    B('vano_dx', 7.08, 7.25, 0.341, 0.71, 0.0, 0.40, '#44291e', [], ['+z', '+x'], **TV),
    B('vano_buio', 7.10, 7.23, 0.345, 0.66, 0.40, 0.402, '#251410', [], ['+z'], ppm=100, margin=0.0, grp='tv', solid=False),
    B('tv', 5.07, 6.60, 0.79, 1.68, 0.06, 0.12, '#0b0b0d', ['+z'], ['+y', '+x', '-x'], **TV),
    B('soundbar', 5.43, 6.18, 0.76, 0.83, 0.18, 0.30, '#17181a', ['+z'], ['+y', '+x', '-x'], **TV),
    B('speaker', 6.59, 6.845, 0.76, 1.07, 0.115, 0.27, '#141416', ['+z', '-x'], ['+y', '+x'], **TV),   # misure rifinite sui bordi delle foto (fitbox): largo 25,5 cm, profondo 15,5 cm
    # --- parete split (x = 0) ---
    B('credenza', 0.30, 0.72, 0.216, 0.772, 0.375, 2.245, '#2f3134', ['+x', '+z'], ['+y', '-z'], ppm=260, margin=0.03, grp='cred'),
    B('cred_piano', 0.30, 0.745, 0.772, 0.801, 0.345, 2.275, '#2a2c2f', [], ['+y', '+x', '+z', '-z'], ppm=100, margin=0.0, grp='cred'),
    B('cred_gamba1', 0.46, 0.68, 0.0, 0.216, 1.856, 1.886, '#141416', [], ['+z', '-z', '+x', '-x'], ppm=100, margin=0.0, grp='cred', solid=False),
    B('cred_gamba2', 0.46, 0.68, 0.0, 0.216, 0.687, 0.717, '#141416', [], ['+z', '-z', '+x', '-x'], ppm=100, margin=0.0, grp='cred', solid=False),
    # --- divano e dintorni (nuovo sistema, misure dalle foto di dettaglio: sedute a 40 cm, poggiatesta a 97 cm, schienale lungo 1.8 m) ---
    B('s_schienale', 4.61 + DX, 6.79 + DX, 0.38, 0.97, 4.08, 4.50, FAB, [], ['-z', '+y', '+x', '-x'], round=0.06, **SOFA),
    B('s_bracciolo', 4.19 + DX, 4.61 + DX, 0.075, 0.632, 3.38, 4.38, FAB, ['-z', '-x', '+y', '+x'], ['+z'], round=0.04, vis=True, ppm=300, margin=0.03, grp='sofa'),
    B('s_zoccolo', 4.205 + DX, 4.595 + DX, 0.0, 0.075, 3.395, 4.365, '#111113', [], ['-z', '-x', '+x'], ppm=100, margin=0.0, grp='sofa', solid=False, vis=True),
    B('s_seduta', 4.61 + DX, 6.12 + DX, 0.08, 0.40, 3.55, 4.20, FAB, [], ['+y', '-z'], round=0.05, **SOFA),
    B('s_letto', 4.61 + DX, 6.12 + DX, 0.26, 0.41, 2.70, 3.58, FAB, [], ['-z', '-x', '+y'], round=0.04, **SOFA),
    B('s_chaise', 6.08 + DX, 7.00 + DX, 0.08, 0.40, 1.97, 4.20, FAB, [], ['-z', '-x', '+y'], round=0.05, **{**SOFA, 'margin': 0.05}),
    B('s_chaise_dorso', 6.95 + DX, 7.08 + DX, 0.34, 0.72, 2.00, 4.20, FAB, [], ['-x', '-z', '+y'], round=0.05, **{**SOFA, 'margin': 0.02}),
    # tavolino rosso a C (lamiera da 4 mm): montante a terra fuori dal bracciolo (faccia esterna a x 4.16), piano alto appoggiato sopra il bracciolo,
    # ramo basso sotto il divano (non si vede). Non aggiunge volume al divano: il piano sta appoggiato sul bracciolo (4 mm sopra).
    B('c_dorso', 4.156 + DX, 4.160 + DX, 0.0, 0.64, 3.54, 3.85, '#4a1511', ['-x'], ['-z', '+z', '+x'], ppm=300, margin=0.0, grp='cdue'),
    B('c_piano', 4.156 + DX, 4.59 + DX, 0.636, 0.640, 3.54, 3.85, '#47251f', [], ['+y', '-z', '+z', '+x', '-x'], ppm=200, margin=0.0, grp='cdue'),
    # --- consolle dietro la chaise (finestra) ---
    B('consolle', 6.86 + DX, 7.08 + DX, 0.748, 0.776, 2.76, 4.50, '#46372b', [], ['+y', '-x', '-z'], ppm=200, margin=0.0, grp='cons'),
]
# tavolino con le rotelle (piano e ripiano + 4 gambe); coordinate del sistema stanza (x0, x1, z0, z1 del piano)
TAV = dict(x0=3.34, x1=4.10, z0=3.86, z1=4.25)
def _tavolino(x0=TAV['x0'], x1=TAV['x1'], z0=TAV['z0'], z1=TAV['z1']):
    out = [B('tav_piano', x0 + DX, x1 + DX, 0.555, 0.58, z0, z1, '#3f2a20', [], ['+y', '-z', '-x', '+x'], ppm=200, margin=0.10, grp='tav'),
           B('tav_ripiano', x0 + DX, x1 + DX, 0.24, 0.26, z0, z1, '#3f2a20', [], ['+y'], ppm=200, margin=0.10, grp='tav')]
    for i, (x, z) in enumerate([(x0 + 0.015, z0 + 0.015), (x1 - 0.015, z0 + 0.015), (x0 + 0.015, z1 - 0.015), (x1 - 0.015, z1 - 0.015)]):
        out.append(B(f'tav_gamba{i}', x - 0.015 + DX, x + 0.015 + DX, 0.0, 0.555, z - 0.015, z + 0.015, '#151517', [], ['+x', '-x', '+z', '-z'], ppm=100, margin=0.10, grp='tav', solid=False))
    return out
BOXES += _tavolino()
# gambe della consolle
for _i, (_x, _z) in enumerate([(7.19, 2.79), (7.35, 2.79), (7.19, 4.47), (7.35, 4.47)]):
    BOXES.append(B(f'cons_gamba{_i}', _x - 0.015, _x + 0.015, 0.0, 0.748, _z - 0.015, _z + 0.015, '#151517', [], ['+x', '-x', '+z', '-z'], ppm=100, margin=0.03, grp='cons', solid=False))

# volumi invisibili: servono solo a non far finire nelle texture di muri e pavimento cose che stanno davanti (lampada, zona dietro divano)
EXTRA_OCC = [
    dict(name='oggetti_console', min=[7.14, 0.78, 2.70], max=[7.40, 1.34, 4.50]),   # nel vecchio sistema (DX viene tolto sotto)
    dict(name='dietro_divano_W', min=[6.9, 0.0, 1.88], max=[7.4, 0.78, 4.5]),
    dict(name='vaso', min=[0.34, 0.78, 1.78], max=[0.68, 1.27, 2.14]),
    dict(name='vaso_rosso', min=[6.92, 0.34, 0.235], max=[7.06, 0.57, 0.365]),
    dict(name='portabottiglie', min=[0.34, 0.78, 0.40], max=[0.62, 1.15, 0.80]),
    dict(name='ciotola', min=[0.40, 0.78, 1.17], max=[0.66, 0.90, 1.40]),
]
for _e in EXTRA_OCC: _e['min'][0] -= DX; _e['max'][0] -= DX
def as_occluders(boxes=BOXES, extra=True):
    out = [dict(min=(np.array(b['min']) - b['margin']).tolist(), max=(np.array(b['max']) + b['margin']).tolist(), name=b['name']) for b in boxes]
    return out + (EXTRA_OCC if extra else [])

# piccoli oggetti (cilindri/coni): lampada nera sulla consolle, nell'angolo
PRIMS = []
# lampada nera sulla console (misure dalla scansione, sistema stanza)
PRIMS += [
    dict(t='cyl', p=[7.00, 0.776, 4.405], r0=0.006, r1=0.006, h=0.275, color='#101012'),
    dict(t='cyl', p=[7.00, 1.05, 4.405], r0=0.062, r1=0.046, h=0.095, color='#141416'),
]
# vaso sulla credenza (tornio: [raggio, quota relativa, colore] dalla scansione e dalle foto)
PRIMS += [dict(t='lathe', p=[0.143, 0.80, 1.937], prof=[[0.062, 0.0, "#312d24"], [0.085, 0.01, "#27241a"], [0.112, 0.028, "#4e483a"], [0.126, 0.05, "#807c69"], [0.128, 0.07, "#78694f"], [0.123, 0.09, "#766244"], [0.118, 0.11, "#978f75"], [0.108, 0.13, "#a49f8a"], [0.09, 0.15, "#a39c88"], [0.075, 0.17, "#948868"], [0.06, 0.19, "#7a694f"], [0.051, 0.21, "#8e8363"], [0.048, 0.235, "#7f6c49"], [0.049, 0.26, "#735e41"], [0.054, 0.285, "#594328"], [0.068, 0.305, "#86744c"], [0.068, 0.305, "#86744c"], [0.087, 0.325, "#8a7a55"], [0.104, 0.345, "#928360"], [0.113, 0.365, "#9a8c69"], [0.113, 0.375, "#9a8c69"]], seg=28)]
# vaso rosso nel vano del mobile TV: cilindro (raggio 5,3 cm, alto 21,5 cm) in piedi sul fondo del vano; la texture 'vase_t' e' la foto intorno al cilindro (vase_tex.py)
PRIMS += [dict(t='cylt', p=[6.682, 0.341, 0.30], r=0.053, h=0.215, map='vase_t', inner='#2a0509', rim='#d9aba6')]
# portabottiglie nero con tre bottiglie sulla credenza
_rk = dict(x0=0.05, x1=0.23, z0=0.41, z1=0.69, y0=0.80, y1=1.09, w=0.006)
for _x in (_rk['x0'] + 0.006, _rk['x1'] - 0.006):
    for _z in (_rk['z0'] + 0.006, _rk['z1'] - 0.006):
        PRIMS.append(dict(t='box', min=[_x - 0.006, _rk['y0'], _z - 0.006], max=[_x + 0.006, _rk['y1'], _z + 0.006], color='#121214'))
for _y in (_rk['y0'], _rk['y1'] - 0.012):
    for _x in (_rk['x0'] + 0.006, _rk['x1'] - 0.006):
        PRIMS.append(dict(t='box', min=[_x - 0.006, _y, _rk['z0']], max=[_x + 0.006, _y + 0.012, _rk['z1']], color='#121214'))
    for _z in (_rk['z0'] + 0.006, _rk['z1'] - 0.006):
        PRIMS.append(dict(t='box', min=[_rk['x0'], _y, _z - 0.006], max=[_rk['x1'], _y + 0.012, _z + 0.006], color='#121214'))
for _y, _lz in ((0.848, 0.575), (0.945, 0.59), (1.042, 0.565)):
    PRIMS.append(dict(t='hcyl', p=[0.14, _y, 0.55], r=0.036, len=0.27, axis='z', color='#16211b'))
    PRIMS.append(dict(t='hcyl', p=[0.14, _y, _lz], r=0.0368, len=0.075, axis='z', color='#d9cfb4'))

# cuscini del divano: scatole smussate orientate, ricavate dalla scansione 3D (nel sistema stanza). q = quaternione (x, y, z, w); size = spessore, lunghezza, larghezza
import json as _json, os as _os
_f = '/tmp/claude-0/s/sofa/cushion_items.json'
ITEMS = _json.load(open(_f)) if _os.path.exists(_f) else []

