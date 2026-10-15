# Strumenti della stanza a foto (Salotto 3D)

Qui c'è come è stato costruito `salotto/pack/salotto.bin`, il pacchetto della modalità **Foto** e della **camminata**.
Le foto e le scansioni 3D di casa **non** sono nel repo (il repo è pubblico): servono solo a chi rigenera il pacchetto. Nel repo c'è solo il pacchetto **cifrato**.

## Come funziona
1. `sfm/run_sfm_hi.py` — registra le foto (pycolmap, solo CPU): posizione e inclinazione di ogni scatto.
   `sfm/reg_new.py` aggiunge foto nuove al modello già fatto senza muovere quelle vecchie (camera e pose fisse).
2. `reg/calib.py`, `calib2.py`, `frame.py` — allineano il modello alla stanza (parete TV, parete split, pavimento) e ne fissano le misure.
   La parete split sta 30 cm più in dentro del primo piano trovato: `frame.py` ha `XSHIFT = 0.30` e la stanza è lunga **7,10 m** (non 7,4).
3. `reg/scene_def.py` — i mobili come scatole (misure da foto, sovrapposizioni e triangolazioni), le primitive (lampada, vaso a tornio, portabottiglie) e quali facce prendono la foto.
   Le misure scritte nel vecchio sistema si spostano da sole (`DX`).
   Il **tavolino rosso a C** e' lamiera da 4 mm (`c_dorso`, `c_piano`): il montante sta a terra fuori dal bracciolo, il piano si appoggia sopra il bracciolo (4 mm sopra) e il ramo basso
   sta sotto il divano (non si vede, non e' modellato): non aggiunge volume al divano. Il bracciolo e' una scatola smussata con le foto sul fronte (`s_bracciolo`), non parte del campo di quote.
   Attenzione: le foto registrate dopo (`sfm/reg_new.py`) hanno pose meno precise delle prime: per misurare si controlla sempre con due viste.
4. Bake delle texture, ciascuna da più foto con occlusione (`reg/cams_sel.py` esclude le foto scattate dal corridoio). **Lanciarli con `FRAME_EXT=1`**: senza, usano solo le prime foto e non le 12 nuove:
   - `reg/run_walls7.py 400 TAG 0.5 T W F A` — le 4 pareti (400 px/m)
   - `reg/run_floor7.py 350 TAG 0.5` — il pavimento
   - `reg/bake_furniture7.py 0.5 TAG` — le facce dei mobili
   - `reg/paintings.py` — misura i 5 quadri e ne estrae la foto
5. Le scansioni 3D (`.spz`, Scaniverse) danno la forma di ciò che le foto non rendono bene:
   - `scan/spzload.py` legge il file; `scan/photo_align*.py` lo allinea alla stanza massimizzando la correlazione con le foto
   - divano: `scan/sofa_hf.py` → `sofa_hf2.py` → `sofa_hf3.py` ricavano un campo di quote a 2 cm (senza i cuscini, che hanno `cushions.py` / `cushions2.py`);
     `reg/sofa_bake.py` ne ricava la texture a 5 mm dalle foto (occlusione del campo stesso), `reg/sofa_export.py` riempie i buchi e prepara quote e texture
     `scan/sofa_cut.py` toglie dal campo di quote il bracciolo e il piano del tavolino con le rotelle che la scansione aveva incluso (parte sempre dall'originale)
   - oggetti sulla console (versione vecchia, ora non piu' nel pacchetto): `scan/cons_vox.py` li trasforma in voxel da 6 mm; `reg/vox_photo.py` li ricolora con le foto
   - oggetti sulla console in 3D vero (`reg/console_obj.py`): le figure Funko (Art, Pennywise, Mandalorian, Daredevil) sono rilievi fotografici: da una foto frontale si ricava la maschera della sagoma
     (`console/seglib.py` e gli script `console/seg_*.py`, GrabCut con semi a mano; `console/prep_console.py` salva ritagli e maschere in `CONSOLE_ASSETS`, fuori dal repository perche' sono foto di casa), la
     profondita' di ogni punto viene dalla distanza dal bordo (profilo tondeggiante), il colore e' la foto stessa con la maschera alfa (`alphaMap`). La custodia del fumetto ha il frontale rettificato
     dalla foto (omografia sui quattro angoli), pannelli acrilici trasparenti (`alpha`), spigoli chiari e base nera; lampada plissettata, telecamera bianca, ciotola nera con i cioccolatini, basi, pozza di sangue di
     Pennywise e il piano di legno (texture sintetica con le ombre di contatto) sono mesh a colori per vertice o con texture sintetiche. Con `CONSOLE_ASSETS` impostata `build_pack.py` le aggiunge al
     pacchetto (blocchi `cm_*`, texture `cobj_*`) e toglie voxel e vecchia lampada.
   - vaso rosso nel vano del mobile TV: la scansione (splat + mesh) conferma un cilindro semplice; le misure (raggio 5,3 cm, alto 21,5 cm, in piedi a x 6,68 e z 0,30) vengono
     dal contorno nella foto registrata (`reg/vase_profile.py`: diametro a ogni quota, nel piano dell'asse), perche' la scala delle scansioni non e' affidabile; `reg/vase_tex.py` ricava
     la texture intorno al cilindro (colonne = angolo, righe = quota). Il vano e' vero (fondo e divisorio in `scene_def.py`), il vaso e' una `cylt` nel pacchetto.
   - mobile a mensole accanto alla TV (il 'mobile quadrato'): la struttura e' misurata da foto registrate (triangolazioni `tri.py`/`vline.py`/`rayplane.py` e sovrapposizioni): fondo beige sottile (3,4 cm) a x 3,54-3,855,
     pilastro da 3,855 a 4,25 con il pannello grafite davanti (x 3,80-4,415, z 0,24-0,26; in realta' e' inclinato di ~4,6 gradi), quattro mensole in noce trapezoidali (il lato sinistro e' in diagonale; spessore 2,2 cm).
     Mensole, pianta (tradescantia), brocca, vasetti, fumetti e vasi rossi sono una mesh a colori per vertice (`meshlib.py` + `shelf_unit.py`, tipo `vmesh` nel pacchetto); il fondo e il fianco del pilastro
     sono texture sintetiche con le ombre portate di una luce dall'alto a sinistra (`shelf_tex.py`, direzione ricavata dalle ombre nelle foto): le foto dell'interno sbavavano.
   - mensole portaquadri nere e i sei quadretti (`reg/ledges.py`): le posizioni (u lungo la parete TV, altezza del piano) vengono dalla parete cotta e dal confronto con una foto registrata frontale; i quadretti sono
     rettificati dalla foto (`console/prep_posters.py`: angoli del passepartout trovati in automatico dalla cornice nera, due a mano; atlante 3x2), inclinati di 8 gradi all'indietro contro il muro.
     In `build_pack.py` le fasce della parete TV dove c'erano le vecchie foto dei quadretti vengono ricostruite per diffusione (`WALL_EXCL`).
   - oggetti sulla credenza (`reg/credenza_obj.py`): il vaso smaltato e' un solido di rotazione col profilo letto dalle silhouette nelle foto registrate (la scala e' verificata sulle silhouette in quattro foto,
     raggio x 0,93), l'asse (x 0,155, z 1,945) viene da due foto e dal confronto delle silhouette; la texture e' cotta dalle foto con `reg/phototex.py` (si proietta ogni punto con la posa della foto, peso = coseno
     dell'angolo di vista, maschere GrabCut `console/seg_vase.py` per scartare lo sfondo, riflessi puntiformi scartati, buchi riempiti per diffusione). Il portabottiglie nero ha telaio (cx 0,158, cz 0,557, ruotato di
     27,6 gradi, 21,5 x 19,3 x 30,5 cm) e sei bottiglie adattati ai punti letti a mano in tre foto registrate (`console/rackfit.py`, `console/bottlefit.py`, controllo con `console/rackov.py`); le etichette delle tre
     bottiglie davanti sono ritagli rettificati dalla foto frontale, incollati come strisce curve; capsule e anelli del collo a colori per vertice. La ciotola di rame (a x 0,33 z 1,31, da tre raggi) ha un oggetto
     blu-argento dentro. Attenzione: la foto registrata 8ebbe415 ha una posa sbagliata di 10-20 cm in questa zona (il vaso torna perche' e' stato triangolato anche con lei): per misurare sulla credenza si usano
     3039c671, 6d89137e e 4bd3d963 (`console/vaseov.py` e `console/pairs.py` sovrappongono modello e foto).
   - interruttore e presa sulla parete A (`reg/wall_obj.py`): placche a tre moduli (11,7 x 8,2 cm) con gli angoli intersecati col piano della parete in due foto (concordano entro 4 mm). Nella texture della
     parete A le loro fasce sono ricostruite (`WALL_EXCL['A']`): le foto, con pose un po' diverse, le avevano cotte doppie.
   - corridoio dietro l'arco (`reg/corridor_obj.py`): un disimpegno di 2,8 x 1,4 m con la porta di mogano chiusa, il secondo vano buio, le due stampe manga in bianco e nero e il pavimento di marmo.
     Le foto del corridoio dell'utente (verticali, non registrate nel modello) si mettono nel riferimento della stanza con una PnP (`console/corr_pose.py`): angoli dell'arco e tre punti della parete TV letti in una foto
     registrata (b4bfa2ec). Il muro di fondo sta a z = -1,40: il pavimento letto in due foto indipendenti (la PnP e la registrata) lo da' a -1,40 e stampe da 48 x 68 cm; il confronto fotometrico fra foto
     registrate dava -2,15 ma dipende troppo dalle pose relative. L'imbotte dell'arco e' profondo 40 cm (lo dice il bordo posteriore dell'architrave nella foto), non 25.
     `console/corr_prep.py` ricava le texture: stampe rettificate con l'omografia dei quattro angoli (`console/corners_view.py` e `gcrop2.py` per leggerli a mano), foglia della porta, pavimento e colori dell'imbotte
     campionati con la posa; il pavimento che l'arco non lascia vedere si completa a specchio. L'intonaco e' a colori per vertice col gradiente di luce visto nella foto (luce calda dall'alto).
     Nel pacchetto sono prim `vmesh` con `deep: 1`: `real.js` li mostra solo da dentro la stanza, insieme all'imbotte (con `corridor` nel manifesto i piani procedurali di stipiti, architrave e tunnel non si usano piu').
     I ritagli (foglia, stampe, pavimento, imbotte) stanno in `CONSOLE_ASSETS/corr` (foto di casa, fuori dal repository). La fascia sinistra della parete TV (x 0-0,47, a sinistra dell'arco) e' ricostruita per diffusione (`WALL_EXCL`): le foto la cuocevano a chiazze.
6. `reg/build_pack.py TAG_MURI TAG_PAV TAG_FACCE salotto.bin` — toglie i quadri dai muri, riempie i buchi, mette l'ombra sotto i mobili sospesi,
   impacchetta atlante, divano, voxel e primitive e cifra tutto con AES-256-GCM.

I percorsi di lavoro sono scritti nei file (cercare `/tmp/claude-0/s`): vanno adattati. Le scansioni si passano con la variabile `SPZ_FILE`.

## La chiave
Il pacchetto si apre solo con la chiave (43 caratteri). **Non va mai messa nel repo.** Sta in `pack.key` accanto agli script e nel link
`https://…/salotto/#k=<chiave>`: la parte dopo `#` non viene mai inviata al server, l'app la salva nel telefono e la toglie dall'indirizzo.

## Aggiornare il pacchetto
Copiare il nuovo file in `salotto/pack/salotto.bin` e alzare il numero in `PACK_URL` (`?v=`) in `salotto/real.js`: la cache del telefono lo rinnova.
