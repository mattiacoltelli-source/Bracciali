# Strumenti della stanza a foto (Salotto 3D)

Qui c'è come è stato costruito `salotto/pack/salotto.bin`, il pacchetto della modalità **Foto** e della **camminata**.
Le foto di casa **non** sono nel repo (il repo è pubblico): servono solo a chi rigenera il pacchetto. Nel repo c'è solo il pacchetto **cifrato**.

## Come funziona
1. `sfm/run_sfm_hi.py` — registra le foto (pycolmap, solo CPU): posizione e inclinazione di ogni scatto.
2. `reg/calib.py`, `calib2.py`, `frame.py` — allineano il modello alla stanza (parete TV, angolo split, pavimento) e ne fissano le misure vere (7,4 × 4,5 × 3 m).
3. `reg/scene_def.py` — i mobili come scatole (misure ricavate dalle foto) e quali facce prendono la foto.
4. Bake delle texture, ciascuna da più foto con occlusione:
   - `reg/run_walls3.py 300 TAG 0.5 T W F A` — le 4 pareti (300 px/m)
   - `reg/run_floor3.py 300 TAG 0.5` — il pavimento
   - `reg/bake_furniture.py 0.75 TAG` — le facce dei mobili
   - `reg/paintings.py` — misura i 5 quadri e ne estrae la foto
5. `reg/build_pack.py TAG_MURI TAG_PAV TAG_FACCE salotto.bin` — toglie i quadri dai muri, riempie i buchi, impacchetta l'atlante e cifra tutto con AES-256-GCM.

I percorsi di lavoro sono scritti nei file (cercare `/tmp/claude-0/s`): vanno adattati.

## La chiave
Il pacchetto si apre solo con la chiave (43 caratteri). **Non va mai messa nel repo.** Sta in `pack.key` accanto agli script e nel link
`https://…/salotto/#k=<chiave>`: la parte dopo `#` non viene mai inviata al server, l'app la salva nel telefono e la toglie dall'indirizzo.

## Aggiornare il pacchetto
Copiare il nuovo file in `salotto/pack/salotto.bin` e alzare il numero in `PACK_URL` (`?v=`) in `salotto/real.js`: la cache del telefono lo rinnova.
