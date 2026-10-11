---
name: Ristorante Dong
description: Serata al Dong, da telefono. Nero lacca, bordeaux e oro pennello, foto reali del locale.
colors:
  nero: "#0c0a0a"
  lacca: "#161110"
  bordeaux: "#6f1424"
  bordeaux-2: "#8a1b30"
  rosso-azione: "#c9291f"   # solo bottoni Prenota
  oro: "#c9a45c"
  oro-chiaro: "#e0c487"
  carta: "#f2eadd"
  mute: "#b7aa99"
typography:
  display: "Shippori Mincho 700 (serif), titoli grandi con molto respiro"
  body: "Hanken Grotesk 400-600"
---

# Design

Tema scuro, elegante, pensato per il telefono. Il rosso acceso è riservato all'azione (Prenota); bordeaux e oro costruiscono l'atmosfera. Il pennello dorato del logo compare come filigrana (hero, sezione bordeaux) e nel footer.

## Struttura
- Barra in alto con logo; barra in basso sempre visibile: Menu · Prenota · Chiama · Mappa.
- Menu: indice sempre visibile (Giapponese / Cinese + categorie), un tocco per saltare, la categoria in vista si evidenzia.
- Prenota: giorno, turno, orario, persone, nome → WhatsApp (numero segnaposto in `js/prenota.js`).

## Build
`python3 tools/build2.py` rigenera index, menu, prenota, dove-siamo. I dati del menu stanno in `tools/build.py`, la home in `tools/home_main.html`.
