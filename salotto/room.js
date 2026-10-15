// Misure del salotto in metri. Le voci segnate "stima" vengono dalle foto, non da un metro:
// da correggere qui quando si misura.
export const ROOM = { L: 7.4, W: 4.5, H: 3.0 };

// Ogni parete ha un riferimento locale: u corre lungo la parete, y in alto, N è la normale verso l'interno.
// "s" è la distanza dall'angolo indicato in `corner` (è quello che si legge con il metro).
export const WALLS = {
  T: { name: 'Parete TV', corner: 'angolo split', O: [0, 0, 0], U: [1, 0, 0], N: [0, 0, 1], len: ROOM.L, toU: (s) => s, fromU: (u) => u },
  W: { name: 'Parete finestra', corner: 'angolo TV', O: [ROOM.L, 0, 0], U: [0, 0, 1], N: [-1, 0, 0], len: ROOM.W, toU: (s) => s, fromU: (u) => u },
  F: { name: 'Parete ingresso', corner: 'angolo split', O: [ROOM.L, 0, ROOM.W], U: [-1, 0, 0], N: [0, 0, -1], len: ROOM.L, toU: (s) => ROOM.L - s, fromU: (u) => ROOM.L - u },
  A: { name: 'Parete split', corner: 'angolo ingresso', O: [0, 0, ROOM.W], U: [0, 0, -1], N: [1, 0, 0], len: ROOM.W, toU: (s) => s, fromU: (u) => u },
};

export const OPENINGS = {
  T: [{ s0: 0.76, s1: 1.83, y0: 0, y1: 2.0, kind: 'passage' }], // arco senza porta (altezza: stima)
  W: [{ s0: 0.71, s1: 1.63, y0: 0.95, y1: 2.51, kind: 'window' }],
  F: [{ s0: 1.12, s1: 2.22, y0: 0, y1: 2.1, kind: 'door-closed' }], // portone (larghezza: stima)
  A: [{ s0: 0.96, s1: 1.86, y0: 0, y1: 2.1, kind: 'door-open' }], // porta interna (posizione: stima)
};

// Quadri già appesi (tutti 75x50). s = centro, y = centro dal pavimento. Posizioni misurate sulle foto registrate (±1 cm).
// `art` sono tre colori per un'immagine segnaposto: le foto vere stanno nel pacchetto cifrato della stanza a foto.
export const PAINTINGS = [
  { id: 'taj', name: 'Taj Mahal', w: 0.5, h: 0.75, wall: 'T', s: 2.848, y: 1.8, art: ['#8ec1e6', '#e6edf1', '#2b7fa5'] },
  { id: 'petra', name: 'Petra', w: 0.5, h: 0.75, wall: 'W', s: 3.019, y: 1.783, art: ['#6d8bb0', '#c9926a', '#a9c9d6'] },
  { id: 'barca', name: 'Barca al tramonto', w: 0.75, h: 0.5, wall: 'W', s: 3.788, y: 1.653, art: ['#2a1a1c', '#d8542a', '#7a2a1a'] },
  { id: 'islanda', name: 'Islanda', w: 0.75, h: 0.5, wall: 'F', s: 3.384, y: 1.856, art: ['#b7bcc2', '#5c6168', '#23272c'] },
  { id: 'sneaker', name: 'Sneaker (sulla credenza)', w: 0.75, h: 0.5, wall: 'A', s: 3.395, y: 1.015, art: ['#f1ece4', '#cc2b2b', '#2a2a2a'] },
];
// Posizioni delle versioni precedenti (stime): chi non ha mai spostato un quadro passa alle misure nuove.
export const OLD_POS = { taj: [2.8, 1.815], petra: [2.99, 1.805], barca: [3.755, 1.68], islanda: [3.805, 1.75], sneaker: [3.3, 1.05] };
