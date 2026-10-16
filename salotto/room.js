// Misure del salotto in metri. Le voci segnate "stima" vengono dalle foto, non da un metro:
// da correggere qui quando si misura.
// L = distanza fra la parete split e la parete finestra: dalle foto di dettaglio e dalle due scansioni (in metri veri) viene 7.10,
// non 7.4 (la parete split sta 30 cm più in dentro di quanto si pensava). Se col metro viene 7.4, dimmelo.
export const ROOM = { L: 7.1, W: 4.5, H: 3.0 };

// Ogni parete ha un riferimento locale: u corre lungo la parete, y in alto, N è la normale verso l'interno.
// "s" è la distanza dall'angolo indicato in `corner` (è quello che si legge con il metro).
export const WALLS = {
  T: { name: 'Parete TV', corner: 'angolo split', O: [0, 0, 0], U: [1, 0, 0], N: [0, 0, 1], len: ROOM.L, toU: (s) => s, fromU: (u) => u },
  W: { name: 'Parete finestra', corner: 'angolo TV', O: [ROOM.L, 0, 0], U: [0, 0, 1], N: [-1, 0, 0], len: ROOM.W, toU: (s) => s, fromU: (u) => u },
  F: { name: 'Parete ingresso', corner: 'angolo split', O: [ROOM.L, 0, ROOM.W], U: [-1, 0, 0], N: [0, 0, -1], len: ROOM.L, toU: (s) => ROOM.L - s, fromU: (u) => ROOM.L - u },
  A: { name: 'Parete split', corner: 'angolo ingresso', O: [0, 0, ROOM.W], U: [0, 0, -1], N: [1, 0, 0], len: ROOM.W, toU: (s) => s, fromU: (u) => u },
};

export const OPENINGS = {
  T: [{ s0: 0.46, s1: 1.53, y0: 0, y1: 2.0, kind: 'passage' }], // arco senza porta (altezza: stima)
  W: [{ s0: 0.726, s1: 1.630, y0: 0.925, y1: 2.466, kind: 'window' }], // finestra: bordi esterni delle spalle, letti nella foto frontale
  F: [{ s0: 0.388, s1: 1.624, y0: 0, y1: 2.24, kind: 'door-closed' }], // portone: bordi esterni del coprifilo letti nelle foto registrate
  A: [{ s0: 1.061, s1: 1.947, y0: 0, y1: 2.035, kind: 'door-closed', handle: 'right' }], // porta interna, chiusa (come nella foto frontale): bordi esterni del coprifilo
};

// Quadri già appesi (tutti 75x50). s = centro, y = centro dal pavimento. Posizioni misurate sulle foto registrate (±1 cm).
// `art` sono tre colori per un'immagine segnaposto: le foto vere stanno nel pacchetto cifrato della stanza a foto.
export const PAINTINGS = [
  { id: 'taj', name: 'Taj Mahal', w: 0.5, h: 0.75, wall: 'T', s: 2.548, y: 1.8, art: ['#8ec1e6', '#e6edf1', '#2b7fa5'] },
  { id: 'petra', name: 'Petra', w: 0.5, h: 0.75, wall: 'W', s: 3.019, y: 1.783, art: ['#6d8bb0', '#c9926a', '#a9c9d6'] },
  { id: 'barca', name: 'Barca al tramonto', w: 0.75, h: 0.5, wall: 'W', s: 3.788, y: 1.653, art: ['#2a1a1c', '#d8542a', '#7a2a1a'] },
  { id: 'islanda', name: 'Islanda', w: 0.75, h: 0.5, wall: 'F', s: 3.084, y: 1.856, art: ['#b7bcc2', '#5c6168', '#23272c'] },
  { id: 'sneaker', name: 'Sneaker (sulla credenza)', w: 0.75, h: 0.5, wall: 'A', s: 3.395, y: 1.015, art: ['#f1ece4', '#cc2b2b', '#2a2a2a'] },
];
// Posizioni delle versioni precedenti (stime): chi non ha mai spostato un quadro passa alle misure nuove.
export const OLD_POS = { taj: [2.8, 1.815], petra: [2.99, 1.805], barca: [3.755, 1.68], islanda: [3.805, 1.75], sneaker: [3.3, 1.05] };
