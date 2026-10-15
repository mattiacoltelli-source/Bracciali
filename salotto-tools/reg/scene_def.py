"""Definizione dei mobili (scatole in coordinate stanza: x lungo la parete TV dall'angolo split, y su, z verso l'ingresso).
Misure ricavate dalle foto registrate (viste raddrizzate a griglia metrica + sovrapposizioni); le profondita' sono stime.
faces = facce texturizzate con le foto; flat = facce a tinta unita; le altre non si disegnano (nascoste da muri o altri mobili).
margin = quanto si ingrandisce la scatola quando fa da ostacolo per le texture di muri e pavimento."""
import numpy as np

def B(name, x0, x1, y0, y1, z0, z1, color='#444444', faces=(), flat=(), ppm=200, margin=0.05, grp=None, solid=True, round=0.0):
    return dict(name=name, min=[x0, y0, z0], max=[x1, y1, z1], color=color, faces=list(faces), flat=list(flat), ppm=ppm, margin=margin, grp=grp, solid=solid, round=round)

TV = dict(ppm=300, margin=0.035, grp='tv')
SOFA = dict(ppm=170, margin=0.07, grp='sofa')
FAB = '#3b3d40'

BOXES = [
    # --- parete TV (z = 0) ---
    B('colonna', 3.73, 4.14, 0.99, 2.19, 0.0, 0.30, '#b9b2a4', ['+z', '-x'], ['+y'], **TV),
    B('pensile', 4.14, 4.73, 1.00, 2.25, 0.0, 0.40, '#3c3b3a', ['+z', '+x'], ['+y'], **TV),
    B('cassettone', 4.24, 6.79, 0.34, 0.71, 0.0, 0.42, '#bcb4a6', ['+z', '-x'], ['+y'], **TV),
    B('ripiano', 5.00, 7.25, 0.71, 0.76, 0.0, 0.45, '#4a2f20', [], ['+z', '+y', '+x', '-x'], **TV),
    B('vano_dx', 6.79, 7.25, 0.28, 0.71, 0.0, 0.42, '#4a2f20', ['+z'], ['+x'], **TV),
    B('tv', 5.07, 6.60, 0.79, 1.68, 0.06, 0.12, '#0b0b0d', ['+z'], ['+y', '+x', '-x'], **TV),
    B('soundbar', 5.43, 6.18, 0.76, 0.83, 0.18, 0.30, '#17181a', ['+z'], ['+y', '+x', '-x'], **TV),
    B('speaker', 6.65, 6.94, 0.76, 1.07, 0.05, 0.30, '#141416', ['+z', '-x'], ['+y', '+x'], **TV),
    # --- parete split (x = 0) ---
    B('credenza', 0.0, 0.45, 0.14, 0.78, 0.30, 2.34, '#2f3134', ['+x'], ['+y', '+z', '-z'], ppm=260, margin=0.05, grp='cred'),
    # --- divano e dintorni (a tinta unita con spigoli smussati: dalle foto non si ricavano texture pulite) ---
    B('s_schienale', 4.55, 7.10, 0.46, 0.93, 4.28, 4.50, FAB, [], ['-z', '+y', '+x', '-x'], round=0.06, **SOFA),
    B('s_bracciolo', 4.15, 4.55, 0.08, 0.58, 3.55, 4.50, FAB, [], ['-z', '-x', '+y', '+x'], round=0.06, **SOFA),
    B('s_seduta', 4.55, 7.10, 0.08, 0.46, 3.55, 4.28, FAB, [], ['+y', '-z'], round=0.05, **SOFA),
    B('s_letto', 4.55, 6.20, 0.30, 0.46, 2.75, 3.55, FAB, [], ['-z', '-x', '+y'], round=0.04, **SOFA),
    B('s_chaise', 6.20, 7.10, 0.08, 0.46, 1.88, 3.55, FAB, [], ['-z', '-x', '+y'], round=0.05, **{**SOFA, 'margin': 0.05}),
    B('s_chaise_dorso', 7.00, 7.25, 0.46, 0.80, 1.88, 3.55, FAB, [], ['-x', '-z', '+y'], round=0.05, **{**SOFA, 'margin': 0.02}),
    B('totem', 4.22, 4.52, 0.0, 0.72, 3.25, 3.55, '#6a2a22', [], ['-z', '-x', '+y', '+x'], ppm=200, margin=0.05, grp='sofa', round=0.012),
    # --- consolle dietro la chaise (finestra) ---
    B('consolle', 7.12, 7.40, 0.74, 0.78, 2.80, 4.50, '#3d2a1f', [], ['+y', '-x', '-z'], ppm=200, margin=0.0, grp='cons'),
]
# tavolino con le rotelle (piano e ripiano + 4 gambe)
def _tavolino():
    out = [B('tav_piano', 3.65, 4.10, 0.555, 0.58, 3.65, 4.40, '#3f2a20', [], ['+y', '-z', '-x', '+x'], ppm=200, margin=0.10, grp='tav'),
           B('tav_ripiano', 3.65, 4.10, 0.15, 0.17, 3.65, 4.40, '#3f2a20', [], ['+y'], ppm=200, margin=0.10, grp='tav')]
    for i, (x, z) in enumerate([(3.66, 3.66), (4.07, 3.66), (3.66, 4.37), (4.07, 4.37)]):
        out.append(B(f'tav_gamba{i}', x - 0.015, x + 0.015, 0.0, 0.555, z - 0.015, z + 0.015, '#151517', [], ['+x', '-x', '+z', '-z'], ppm=100, margin=0.10, grp='tav', solid=False))
    return out
BOXES += _tavolino()
# gambe della consolle
for _i, (_x, _z) in enumerate([(7.14, 2.82), (7.37, 2.82), (7.14, 4.47), (7.37, 4.47)]):
    BOXES.append(B(f'cons_gamba{_i}', _x - 0.015, _x + 0.015, 0.0, 0.74, _z - 0.015, _z + 0.015, '#151517', [], ['+x', '-x', '+z', '-z'], ppm=100, margin=0.03, grp='cons', solid=False))

# volumi invisibili: servono solo a non far finire nelle texture di muri e pavimento cose che stanno davanti (lampada, zona dietro divano)
EXTRA_OCC = [
    dict(name='lampada', min=[7.15, 0.80, 4.15], max=[7.40, 1.55, 4.50]),
    dict(name='dietro_divano_W', min=[6.9, 0.0, 1.88], max=[7.4, 0.78, 4.5]),
]
def as_occluders(boxes=BOXES, extra=True):
    out = [dict(min=(np.array(b['min']) - b['margin']).tolist(), max=(np.array(b['max']) + b['margin']).tolist(), name=b['name']) for b in boxes]
    return out + (EXTRA_OCC if extra else [])

# piccoli oggetti (cilindri/coni): lampada nera sulla consolle, nell'angolo
PRIMS = [
    dict(t='cyl', p=[7.27, 0.78, 4.33], r0=0.006, r1=0.006, h=0.40, color='#101012'),
    dict(t='cyl', p=[7.27, 1.18, 4.33], r0=0.060, r1=0.045, h=0.10, color='#141416'),
]
