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
   - oggetti sulla console: `scan/cons_vox.py` li trasforma in voxel da 6 mm; `reg/vox_photo.py` li ricolora con le foto
6. `reg/build_pack.py TAG_MURI TAG_PAV TAG_FACCE salotto.bin` — toglie i quadri dai muri, riempie i buchi, mette l'ombra sotto i mobili sospesi,
   impacchetta atlante, divano, voxel e primitive e cifra tutto con AES-256-GCM.

I percorsi di lavoro sono scritti nei file (cercare `/tmp/claude-0/s`): vanno adattati. Le scansioni si passano con la variabile `SPZ_FILE`.

## La chiave
Il pacchetto si apre solo con la chiave (43 caratteri). **Non va mai messa nel repo.** Sta in `pack.key` accanto agli script e nel link
`https://…/salotto/#k=<chiave>`: la parte dopo `#` non viene mai inviata al server, l'app la salva nel telefono e la toglie dall'indirizzo.

## Aggiornare il pacchetto
Copiare il nuovo file in `salotto/pack/salotto.bin` e alzare il numero in `PACK_URL` (`?v=`) in `salotto/real.js`: la cache del telefono lo rinnova.
