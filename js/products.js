/* Catalogo: unica fonte dei prodotti. Per aggiungerne uno basta una nuova voce.
   Foto, descrizioni e prezzi sono di esempio (demo): da sostituire con quelli reali. */
window.SITE = {
  brand: "Menny's Bracelets",
  whatsapp: "390000000000", // numero segnaposto
  email: "ciao@example.com", // email segnaposto
};

window.PRODUCTS = [
  {
    id: "catena",
    name: "Catena Targhetta",
    tagline: "La classica: una targhetta centrale su catena sottile.",
    price: 29,
    photos: ["catena-1", "catena-2", "catena-3"],
    alt: "Bracciale in acciaio a catena con targhetta incisa",
    specs: [
      ["Materiale", "Acciaio inossidabile, catena a maglia groumette da 4 mm."],
      ["Incisione", "Targhetta centrale 3,5 × 0,4 cm: un nome, una data, un luogo o una frase breve. Facoltativa anche sul retro."],
      ["Taglia", "Regolabile, per polsi da 16 a 19 cm."],
    ],
  },
  {
    id: "rigido",
    name: "Cuff Rigido",
    tagline: "Fascia sottile con la frase fuori e un segreto dentro.",
    price: 29,
    photos: ["rigido-1", "rigido-2", "rigido-3"],
    alt: "Bracciale rigido in acciaio con frase incisa",
    specs: [
      ["Materiale", "Acciaio inossidabile, altezza 5 mm. Disponibile argento, oro, nero e rosa."],
      ["Incisione", "Frase o nome sul davanti e un messaggio segreto all'interno, dove lo leggi solo tu."],
      ["Taglia", "Si regola con una leggera pressione: va bene per polso maschile e femminile."],
    ],
  },
  {
    id: "coordinate",
    name: "Coordinate",
    tagline: "Il posto del cuore, inciso come una posizione sulla mappa.",
    price: 29,
    photos: ["coordinate-1", "coordinate-2", "coordinate-3"],
    alt: "Bracciale rigido con coordinate geografiche incise",
    specs: [
      ["Materiale", "Acciaio inossidabile, fascia rigida da 5 mm."],
      ["Incisione", "Ci dici un luogo (una via, una città, un posto speciale) e ne ricaviamo le coordinate. Dentro c'è spazio per un messaggio segreto."],
      ["Taglia", "Regolabile con una semplice pressione, per polsi da 17 a 18 cm."],
    ],
  },
  {
    id: "pietre",
    name: "Pietre Dure",
    tagline: "Ematite e onice nero, con l'inserto inciso al centro.",
    price: 36,
    photos: ["pietre-1", "pietre-2"],
    alt: "Bracciale con pietre dure nere e inserto in acciaio inciso",
    specs: [
      ["Materiale", "Pietre dure (ematite e onice nero) montate su cavo d'acciaio, inserto centrale in acciaio."],
      ["Incisione", "Sull'inserto centrale: un nome, una data, un luogo, una parola o una breve frase."],
      ["Taglia", "Regolabile grazie a una catenina d'acciaio, per polsi da 16 a 20 cm."],
    ],
  },
  {
    id: "cinturino",
    name: "Doppio Giro",
    tagline: "Similpelle intrecciata, chiusura magnetica, inserto in acciaio.",
    price: 31,
    photos: ["cinturino-1", "cinturino-2", "cinturino-3"],
    alt: "Bracciale in similpelle nera intrecciata con inserto in acciaio inciso",
    specs: [
      ["Materiale", "Cinturino intrecciato in similpelle (nessun materiale di origine animale) e inserto in acciaio."],
      ["Incisione", "Sull'inserto centrale: una scritta, un nome, una data, un luogo. Si legge su più lati."],
      ["Taglia", "Lungo 41 cm, fa un doppio giro intorno al polso. Chiusura magnetica, per polsi da 17,5 a 18,5 cm."],
    ],
  },
  {
    id: "coppia",
    name: "Set di Coppia",
    tagline: "Due bracciali che si attirano: il cuore è una calamita.",
    price: 49,
    photos: ["coppia-1", "coppia-2", "coppia-3"],
    alt: "Due bracciali in acciaio di coppia con cuore magnetico",
    specs: [
      ["Materiale", "Due bracciali in acciaio a maglia groumette (7 mm e 5 mm) con cuore magnetico."],
      ["Incisione", "Una targhetta per ciascuno: un nome, una data, un luogo, una parola o una frase breve."],
      ["Taglia", "Regolabili, per polsi da 16 a 19 cm."],
    ],
  },
];
