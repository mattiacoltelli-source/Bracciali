#!/usr/bin/env python3
"""Genera le pagine HTML statiche del sito (index, menu, prenota, dove-siamo).

Uso:  python3 tools/build.py
Il menu è scritto qui sotto (MENU) e le foto si leggono da assets/menu/<categoria>/.
Dopo aver modificato i dati basta rilanciare lo script. Il sito pubblicato è fatto solo
di file statici: lo script serve solo a chi vuole aggiornare il menu.
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEL = "+390516255139"
TEL_VIEW = "051 625 5139"
MAPS = "https://maps.app.goo.gl/Y1UoydMFwZTkH6NLA"
SHOP = "https://shop.ristorantedong.it/"
DELIVEROO = "https://deliveroo.it/it/menu/bologna/san-lazzaro/ristorante-dong"
SOCIAL = [
    ("Facebook", "https://www.facebook.com/ristorantedong/"),
    ("Instagram", "https://www.instagram.com/ristorantedong/"),
    ("Tripadvisor", "https://www.tripadvisor.it/Restaurant_Review-g968423-d12347451-Reviews-Dong-San_Lazzaro_di_Savena_Province_of_Bologna_Emilia_Romagna.html"),
]
LEGAL = [
    ("Note legali", "https://www.ristorantedong.it/note-legali"),
    ("Privacy", "https://www.ristorantedong.it/privacy-policy"),
    ("Cookie", "https://www.ristorantedong.it/cookie-policy"),
    ("Condizioni d'uso", "https://www.ristorantedong.it/condizioni-duso"),
]

# ---------------------------------------------------------------- MENU
# (id, titolo, introduzione, [(piatto, descrizione)])
MENU = {
    "giapponese": [
        ("tartare", "Tartare", "Pesce crudo tagliato finemente, con marinature leggere. La tartare Dong si prepara solo nelle nostre cucine.", [
            ("Sake", "Salmone"),
            ("Maguro", "Tonno"),
            ("Bow Bow", "Salmone, branzino e tonno"),
            ("Dong", "Gambero rosso, capesante, pesce bianco, pomodorino, cetriolo, salsa piccante su letto di riso"),
            ("Gambero rosso", "Gambero rosso su letto di bufala"),
            ("Tonno", "Tonno su letto di bufala"),
            ("Salmone", "Salmone su letto di bufala"),
        ]),
        ("chirashi", "Chirashi", "Riso con il pesce disposto sopra, da mangiare con gli occhi prima che con la bocca.", [
            ("Ikyzo", "Filetto di salmone e ikura"),
            ("Misto", "Pesce misto e avocado"),
            ("Sugoi", "Filetti di anguilla e salsa"),
            ("Poke", ""),
        ]),
        ("gio", "Giò", "Bocconcini: perle di tartare o uova avvolte in un sottilissimo carpaccio.", [
            ("Sake", "Tartare avvolta con salmone"),
            ("Maguro", "Tartare avvolta con tonno"),
            ("Ikura", "Uova di salmone avvolte con salmone"),
            ("Tobiko", "Uova di pesce volante avvolte con salmone"),
            ("Gio Maio", "Avvolto con salmone scottato, maio e tobiko"),
            ("Zucchina", "Tartare di gambero cotto avvolta con zucchine"),
            ("Egg", "Uova di quaglia, olio tartufato, salsa ponzu, avvolte con salmone"),
        ]),
        ("hosomaki", "Hosomaki", "Sottili rotolini di alga nori con riso e pesce o verdure.", [
            ("Nidi Tuna", "Cream cheese, avocado, pasta fillo croccante, tartare di tonno"),
            ("Nidi Salmon", "Cream cheese, avocado, pasta fillo croccante, tartare di salmone"),
            ("Fly Tuna", "Hosomaki sake in tempura con tartare di tonno"),
            ("Fly Salmon", "Hosomaki sake in tempura con tartare di salmone"),
            ("Ichigo", "Hosomaki in tempura, cream cheese, salmone, fragola"),
            ("Sake", "Salmone"),
            ("Tekka", "Tonno"),
            ("Hosomaki avocado", ""),
        ]),
        ("uramaki", "Uramaki", "Il riso fuori, l'alga dentro: i nostri rotoli più creativi.", [
            ("Astice", "Astice, avocado, maionese, tobiko, lime"),
            ("Coco Roll", "Cream cheese, avocado, scampi in tempura, polvere di cocco"),
            ("Scampi", "Scampi freschi, mela, salmone, lime"),
            ("Sicily", "Cream cheese, avocado, gambero rosso di Sicilia, sale rosso, pepe"),
            ("Crazy Salmon", "Salmone cotto, salmone, uova di salmone, wakame, salsa teriyaki"),
            ("Spicy Tuna", "Tonno, cream cheese, avocado, piccante, salsa al mango, fiocchi di bonito"),
            ("Spicy Salmon", "Salmone, cream cheese, avocado, piccante, salsa al mango, mandorle"),
            ("Dragon", "Gambero in tempura, maionese, salmone scottato, salsa teriyaki"),
            ("Cream Cheese", "Salmone, cream cheese, avocado"),
            ("California", "Polpa di granchio e gambero cotto, maionese, tobiko, avocado"),
            ("Ebiten", "Gambero in tempura, maionese, patatine, salsa"),
            ("Tonata", "Tonno cotto, cream cheese, lattuga, tobiko"),
            ("Goden", "Salmone cotto, cream cheese, patatine, salsa"),
            ("Vege", "Avocado, pomodoro, insalata, cetriolo"),
            ("Unagi", "Cream cheese, avocado, anguilla, salsa"),
            ("Pink Passion", "Gambero in tempura, maionese, salmone scottato, tartare di gambero rosso"),
            ("Pistacchio Lover", "Pesce misto, granella di pistacchio, tartare di salmone"),
            ("Ricciola", "Ricciola scottata, pesce bianco, insalata, salsa al mango, alga"),
            ("White Ocean", "Salmone scottato, polpa di granchio, avocado, maionese, erba cipollina, tobiko e flambé di zucchero"),
            ("Burratina", "Gambero in tempura, cream cheese, gambero rosso, avocado, granella di pistacchio, burrata"),
            ("Rebecca", "Tonno, avocado, tonno scottato, flambé di zucchero, salsa piccante"),
        ]),
        ("makidark", "Maki Dark", "Il lato scuro del sushi: riso e alga nera, sapori intensi.", [
            ("Uramaki Golden Truffle", "Salmone e olio tartufato"),
            ("Uramaki Salmone", "Salmone, avocado, frutto della passione, salsa mango, pistacchio"),
            ("Uramaki Astice Nero", "Gamberi, astice e avocado"),
            ("Chirashi pesce misto", "Salmone, avocado, ikura, tonno, pesce bianco"),
            ("Hosomaki Nero", "Gambero cotto, polipo, cream cheese, avocado, salsa piccante"),
            ("Hosomaki Speciale", "Salmone, cream cheese, avocado, tobiko, maionese"),
            ("Futomaki", "Gamberi in tempura, astice, avocado"),
            ("Giò Misto", "Avocado, salmone scottato sopra, pesce misto"),
            ("Giò Astice", "Avvolto da avocado"),
        ]),
        ("sashimi", "Sashimi", "Pesce crudo servito semplicemente, perfetto grazie al suo taglio.", [
            ("Sashimi New Style", "Carpaccio di pesce misto scottato con salsa leggermente piccante"),
            ("Sashimi Bufala", "Letto di mozzarella di bufala con sashimi misto, salsa al mango, pistacchio e frutta"),
            ("Sashimi Sake", "Salmone"),
            ("Sashimi Maguro", "Tonno"),
            ("Sashimi Amaebi", "Gambero rosso di Sicilia"),
            ("Sashimi misto", ""),
            ("Sashimi di capesante", ""),
            ("Sashimi di ricciola", ""),
            ("Tataki salmone", "Fettine di salmone con granella di pistacchio"),
            ("Tataki tonno", "Fettine di tonno scottato con granella di pistacchio"),
            ("Carpaccio misto", "Salmone, tonno, branzino"),
        ]),
        ("nigiri", "Nigiri", "Sfere di riso modellate a mano con un filetto di pesce.", [
            ("Sushi Ciku", "Misto"),
            ("Sushi Hot", "Nigiri scottati"),
            ("Buri", "Ricciola"),
            ("Hotategai", "Capesante"),
            ("Amaebi", "Gambero rosso di Sicilia"),
            ("Unagi", "Anguilla"),
            ("Maguro", "Tonno"),
            ("Aburi Sake", "Salmone scottato"),
            ("Sake", "Salmone"),
            ("Eby", "Gambero cotto"),
            ("Suzuki", "Branzino"),
            ("Tai", "Orata"),
            ("Tako", "Polipo"),
        ]),
        ("gunkan", "Gunkan", "Piccole navi di riso avvolte nell'alga e riempite al momento.", [
            ("Ikura", "Uova di salmone"),
            ("Tobiko", "Uova di pesce volante"),
            ("Spicy Salmon", "Tartare di salmone"),
            ("Spicy Tuna", "Tartare di tonno"),
            ("Surimi", "Surimi, maionese, gambero cotto"),
        ]),
        ("onigiri", "Onigiri", "Il triangolo di riso, semplice e simbolico.", [
            ("Sake", "Salmone"),
            ("Maguro", "Tonno"),
            ("Eby", "Gambero"),
        ]),
        ("saudade", "Saudade", "L'incontro tra Giappone e Brasile: sapore vivace, tartare e avocado.", [
            ("Salmone", "Tartare di salmone, avocado, salsa"),
            ("Tonno", "Tartare di tonno, avocado e salsa"),
        ]),
        ("barca", "Japanese Temptation", "Le barche di sushi, per condividere.", [
            ("Sushi Garden", "Sashimi, sushi, maki, 30 pezzi misti"),
            ("Sushi Dong", "Nigiri e uramaki, 18 pezzi"),
            ("Garden Style", "Sashimi (6 pz), nigiri (4 pz), hosomaki nidi (4 pz)"),
            ("Temptation", "Nostra selezione di uramaki misti, 24 pezzi"),
        ]),
    ],
    "cinese": [
        ("freddi", "Antipasti freddi", "Insalate, alghe e edamame per cominciare.", [
            ("Insalata con granchio reale", "Con salsa al sesamo"),
            ("Insalata con salmone scottato", "Con salsa al sesamo"),
            ("Alghe goma wakame", "Marinate, leggermente piccanti, con aceto"),
            ("Edamame", "Baccelli di soia"),
            ("Edamame piccante", "Baccelli di soia con salsa piccante"),
        ]),
        ("caldi", "Antipasti caldi", "Fritti e croccanti, fatti ogni giorno.", [
            ("Involtini Dong con verdure", "Sfoglia di riso o pasta wanton ripiena di verdure, fritta e servita calda e croccante"),
            ("Involtini di gambero", ""),
            ("Pane al latte", "Toast con semi di sesamo e battuta di gambero"),
            ("Fiori di zucca", "Con ripieno di gambero"),
        ]),
        ("ravioli", "Ravioli", "Scrigni di pasta ripiena, simbolo di buona fortuna.", [
            ("Ravioli di astice", ""),
            ("Ravioli al nero di seppia", "Con ripieno di branzino"),
            ("Ravioli di capasanta", ""),
            ("Ravioli di gambero", ""),
            ("Ravioli Xiao Long Bao", "Carne e zenzero"),
            ("Ravioli di carne", ""),
            ("Ravioli di carne alla griglia", ""),
            ("Ravioli Rainbow", "Con ripieno di verdure"),
            ("Baozi", "Pane cinese ripieno di carne"),
            ("Ravioli di zucca", "Con ripieno di pollo, zenzero, erba cipollina"),
            ("Ravioli di spinaci", "Con ripieno di gamberi e spinaci"),
            ("Ravioli di manzo e porri", ""),
            ("Ravioli di scampi", ""),
            ("Ravioli misti", "Ricciola, astice, spinaci, zucca"),
            ("Mini bao alla griglia", "Ripieni di carne"),
            ("Wanton", "Ripieni di gambero e carne con salsa leggermente piccante e sesamo"),
        ]),
        ("primi", "Primi piatti", "Riso, tagliolini, spaghetti e ramen saltati in wok.", [
            ("Tagliolini cinesi", "Saltati con carne e verdurine, oppure con gamberi e verdurine"),
            ("Singapore", "Spaghetti di riso profumati al curry"),
            ("Riso bianco", ""),
            ("Riso Dong", "Riposato per 7 giorni, con una salsa di verdure, carne e gambero"),
            ("Riso Jasmin", "Con carne arrosto alla cha shao, salsa di soia e verdure"),
            ("Riso Yangzhou", "Con gamberi scottati e verdure"),
            ("Riso con verdure miste", ""),
            ("Riso nero Venere", "Saltato in wok con pinoli e carne"),
            ("Soba al tè verde", "Spaghetti di grano saraceno al tè verde, salmone affumicato e bottarga"),
            ("Ramen di pesce", "In brodo, serviti con pesce, uova e verdure"),
            ("Ramen di carne", "In brodo, serviti con carne, uova e verdure"),
            ("Yaki Meshi", "Riso saltato con verdure e gamberi, salsa teriyaki, avvolto da crêpes di uova"),
            ("Spaghetti di soia", "Con gambero, con carne o con verdure"),
            ("Gnocchi di riso", "Saltati con gamberi e verdure"),
            ("Spaghetti di riso", "Con gambero, con carne o con verdure"),
        ]),
        ("carne", "Secondi di carne", "Pollo, anatra, maiale, coniglio e manzo Angus.", [
            ("Ma La Pollo", "Pollo fritto con peperoncino rosso e aromi orientali"),
            ("Pollo fritto", ""),
            ("Pollo al limone", ""),
            ("Pollo al curry", ""),
            ("Pollo Gongbao", "Con peperoncino, verdure e arachidi"),
            ("Pollo in agrodolce", "Con cipolla e peperoni"),
            ("Anatra alla pechinese", "Come nella tradizione. Da ordinare un giorno prima"),
            ("Bocconcini di anatra", "Arrosto"),
            ("Anatra all'arancia", "Con salsa agli agrumi"),
            ("Anatra piccante", "Con cipolla e peperoni"),
            ("Anatra al curry rosso e latte di cocco", ""),
            ("Costine di maiale caramellate", "Con salsa cha shao"),
            ("Costine di maiale Gongting", "Con pinoli e salsa leggermente piccante"),
            ("Bocconcini di coniglio", "Cotti in pentola di terracotta con verdure"),
            ("Bocconcini di Angus Jiang Bao", "Con salsa al pepe nero e verdure"),
            ("Filetto di Angus", "Con zenzero e pepe verde"),
            ("Straccetti di Angus", "Glassati"),
            ("Straccetti di Angus al curry", "Con curry rosso e latte di cocco"),
        ]),
        ("pesce", "Secondi di pesce", "Gamberi, branzino, rombo e granchio, anche in tempura.", [
            ("Gamberi sale e pepe", "Fritti e saltati con sale e pepe di Sichuan"),
            ("Gamberi in nidi di rondine", "Saltati con verdure"),
            ("Gamberi in salsa piccante", "Con cipolla e peperoni"),
            ("Gamberi in agrodolce", ""),
            ("Gamberoni grigliati", ""),
            ("Gamberoni piccanti", ""),
            ("Filetto di branzino", "Stufato con zenzero e cipollotti"),
            ("Branzino in foglia di loto", "Filetto avvolto in foglia di loto"),
            ("Rombo sale e pepe", "Saltato con sale e pepe di Sichuan"),
            ("Rombo con verdure", "Sfilettato"),
            ("Rombo piccante", "Saltato con salsa piccante e verdure"),
            ("Soft shell crab", "Granchio fritto saltato con sale e pepe di Sichuan"),
            ("Filetto di salmone", "Grigliato, servito con salsa agrodolce"),
            ("Tempura di gambero", ""),
        ]),
        ("veg", "Vegetariano", "Verdure e tofu, cucinati in wok o stufati.", [
            ("Xiao Bai Cai", "Verdure cinesi saltate in wok"),
            ("Misto di verdure", "Saltate in wok: zucchine, carote, pak choi, fiori di loto"),
            ("Melanzane cinesi", ""),
            ("Doufu stufato con verdure", "Tofu stufato con verdure"),
            ("Asparagi con fiori di loto", ""),
            ("Ma La Doufu", "Tofu in salsa piccante"),
            ("Cavolfiori cinesi piccanti", ""),
        ]),
    ],
}

# tolgono il suffisso della categoria dal nome del file per ottenere la didascalia
SUFFIX = ["japanese-temptation", "antipasti-freddi", "antipasti-caldi", "primi-piatti", "secondi-piatti-di-carne",
          "secondi-di-carne", "secondi-di-pesce", "secondi-piatti-di-pesce", "vegetariano", "maki-dark", "zuppe",
          "tartare", "chirashi", "gio", "hosomaki", "uramaki", "sashimi", "nigiri", "gunkan", "onigiri",
          "saudade", "ravioli"]
FIXES = {"capasanta": "capesante", "tonnata": "tonnata", "eby": "eby", "ciku": "ciku"}


def caption(fname):
    s = os.path.splitext(fname)[0]
    for suf in SUFFIX:
        if s.endswith("-" + suf) and s != suf:
            s = s[: -(len(suf) + 1)]
            break
    s = s.replace("-", " ")
    s = " ".join(FIXES.get(w, w) for w in s.split())
    return s[:1].upper() + s[1:]


def photos_for(cat):
    d = os.path.join(ROOT, "assets", "menu", cat)
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.endswith(".jpg"))


def e(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- PARTI COMUNI
ICONS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
<symbol id="i-phone" viewBox="0 0 24 24"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
<symbol id="i-arrow" viewBox="0 0 24 24"><path d="M4 12h16M14 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-pin" viewBox="0 0 24 24"><path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="12" cy="9.5" r="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
<symbol id="i-bag" viewBox="0 0 24 24"><path d="M5 8h14l-1 12H6L5 8zM9 8V6a3 3 0 0 1 6 0v2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M16 16l5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
<symbol id="yy" viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="var(--yy-b, #f3ece2)"/><path d="M50 0a50 50 0 0 1 0 100a25 25 0 0 1 0-50a25 25 0 0 0 0-50z" fill="var(--yy-a, #130a09)"/><circle cx="50" cy="25" r="8" fill="var(--yy-b, #f3ece2)"/><circle cx="50" cy="75" r="8" fill="var(--yy-a, #130a09)"/></symbol>
</svg>"""

NAV = [("index.html", "Home"), ("menu.html", "Menu"), ("prenota.html", "Prenota e ordina"), ("dove-siamo.html", "Dove siamo")]


def head(title, desc, page, extra=""):
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#130a09">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="assets/img/sala-hero.jpg">
<meta property="og:locale" content="it_IT">
<link rel="icon" href="assets/favicon.png" type="image/png">
<link rel="preload" href="assets/fonts/ShipporiMincho-800.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="css/style.css">
<script>document.documentElement.classList.add('js')</script>
{extra}</head>
"""


def header(page):
    def cur(h):
        return ' aria-current="page"' if h == page else ""

    links = "".join(f'<a href="{h}"{cur(h)}>{t}</a>' for h, t in NAV)
    big = "".join(
        f'<a class="big" href="{h}"{cur(h)}>{t}<svg width="26" height="26" aria-hidden="true"><use href="#i-arrow"/></svg></a>'
        for h, t in NAV
    )
    return f"""<body data-page="{page}">
{ICONS}
<a class="skip" href="#main">Vai al contenuto</a>
<header class="site-header" id="top">
  <a class="logo" href="index.html" aria-label="Ristorante Dong, home"><img src="assets/img/logo-inverse.png" alt="Dong, Fine Asian Flavors" width="100" height="53"></a>
  <nav class="nav" aria-label="Principale">{links}</nav>
  <div class="head-actions">
    <a class="btn btn--oro" href="tel:{TEL}" style="min-height:44px;padding:0 20px"><svg aria-hidden="true"><use href="#i-phone"/></svg><span class="tel-t">Chiama</span></a>
    <button class="menu-btn" type="button" aria-label="Apri il menu di navigazione" aria-expanded="false" aria-controls="mnav">
      <svg class="bars" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h18M3 12h18M3 17h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <svg class="x" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    </button>
  </div>
</header>
<div class="mobile-nav" id="mnav">
  {big}
  <p class="mn-note">Martedì – Domenica<br>12:00 – 14:30 · 19:00 – 23:00<br>Lunedì chiuso</p>
</div>
"""


def footer():
    soc = "".join(f'<li><a href="{u}" target="_blank" rel="noopener">{n}</a></li>' for n, u in SOCIAL)
    leg = "".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in LEGAL)
    return f"""<footer class="foot">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <img class="fl" src="assets/img/logo-dong.png" alt="" width="64" height="64">
        <h4>Ristorante Dong</h4>
        <p>Fusion restaurant<br>Cucina cinese e giapponese a Bologna</p>
      </div>
      <div>
        <h4>Ti aspettiamo in</h4>
        <p><a href="{MAPS}" target="_blank" rel="noopener">via Russo, 4<br>40068 San Lazzaro di Savena (BO)</a></p>
        <p style="margin-top:12px"><a href="tel:{TEL}">{TEL_VIEW}</a></p>
      </div>
      <div>
        <h4>Orari</h4>
        <p>Martedì – Domenica<br>12:00 – 14:30<br>19:00 – 23:00<br>Lunedì chiuso</p>
      </div>
      <div>
        <h4>Seguici</h4>
        <ul>{soc}</ul>
        <ul style="margin-top:10px"><li><a href="https://www.ristorantedong.it/lavora-con-noi" target="_blank" rel="noopener">Lavora con noi</a></li></ul>
      </div>
    </div>
    <div class="legal">
      <span>Mizuumi SRL · P.IVA 03504171202</span>
      {leg}
    </div>
  </div>
</footer>
<nav class="dock" aria-label="Azioni rapide">
  <a href="tel:{TEL}"><svg aria-hidden="true"><use href="#i-phone"/></svg>Prenota</a>
  <a href="{SHOP}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-bag"/></svg>Ordina</a>
  <a href="{MAPS}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-pin"/></svg>Dove</a>
</nav>
<script src="js/site.js"></script>
"""


def ld_json():
    data = {
        "@context": "https://schema.org",
        "@type": "Restaurant",
        "name": "Ristorante Dong",
        "description": "Fusion restaurant: cucina cinese e giapponese alla carta a San Lazzaro di Savena, Bologna.",
        "servesCuisine": ["Cinese", "Giapponese"],
        "telephone": TEL,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "via Russo, 4",
            "postalCode": "40068",
            "addressLocality": "San Lazzaro di Savena",
            "addressRegion": "BO",
            "addressCountry": "IT",
        },
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "opens": "12:00", "closes": "14:30"},
            {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "opens": "19:00", "closes": "23:00"},
        ],
        "hasMenu": "menu.html",
        "image": "assets/img/sala-hero.jpg",
        "sameAs": [u for _, u in SOCIAL],
    }
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n"


def yy_disc(a="#130a09", b="#f3ece2"):
    return f'<svg viewBox="0 0 100 100" aria-hidden="true" style="--yy-a:{a};--yy-b:{b}"><use href="#yy"/></svg>'


# ---------------------------------------------------------------- HOME
def page_home():
    tiles_src = [
        ("tartare", "tartare-dong-tartare.jpg", "Tartare Dong", "Giapponese", "giapponese"),
        ("uramaki", "uramaki-dragon-uramaki.jpg", "Uramaki Dragon", "Giapponese", "giapponese"),
        ("makidark", "golden-truffle-maki-dark.jpg", "Golden Truffle", "Giapponese", "giapponese"),
        ("sashimi", "sashimi-bufala-sashimi.jpg", "Sashimi bufala", "Giapponese", "giapponese"),
        ("ravioli", "xiao-long-bao-ravioli.jpg", "Xiao Long Bao", "Cinese", "cinese"),
        ("primi", "riso-dong-primi-piatti.jpg", "Riso Dong", "Cinese", "cinese"),
        ("carne", "anatra-agli-agrumi-secondi-piatti-di-carne.jpg", "Anatra agli agrumi", "Cinese", "cinese"),
        ("pesce", "soft-shell-crab-secondi-di-pesce.jpg", "Soft shell crab", "Cinese", "cinese"),
    ]
    tiles = "".join(
        f'<a class="tile" data-t="{t}" href="menu.html#{c}"><img src="assets/menu/{c}/{f}" alt="{e(n)}" loading="lazy" width="450" height="562">'
        f'<span class="tn"><b>{e(n)}</b><small>{lab}</small></span></a>'
        for c, f, n, lab, t in tiles_src
    )
    atm = "".join(
        f'<figure class="rv"><img src="assets/img/sala-{n}.jpg" alt="{e(a)}" loading="lazy" width="900" height="1125"></figure>'
        for n, a in [(1, "La sala del ristorante con la parete rossa"), (2, "Divanetti in pelle nera e rami dipinti sulla parete"), (3, "Ravioli neri al vapore in cestello di bambù"), (4, "Il barman prepara un cocktail"), (6, "Nigiri su foglia e piatto laccato"), (8, "Sashimi di tonno su foglia di bambù")]
    )
    body = f"""<main id="main">
<section class="hero">
  <img src="assets/img/sala-hero.jpg" alt="La sala del ristorante: parete rossa con il calligramma Dong e tavoli in lacca nera" fetchpriority="high" width="1800" height="1200">
  <div class="hero-in">
    <h1><span>Due cucine.</span><span class="l2">Un solo tavolo.</span></h1>
    <p class="lede">Cucina cinese e giapponese alla carta, a San Lazzaro di Savena, Bologna. Ingredienti freschi e selezionati, in un ambiente moderno e minimale ispirato alla filosofia orientale.</p>
    <div class="btn-row">
      <a class="btn btn--oro" href="tel:{TEL}"><svg aria-hidden="true"><use href="#i-phone"/></svg>Prenota un tavolo</a>
      <a class="btn btn--line" href="menu.html">Guarda il menu</a>
    </div>
    <p class="status" id="status" data-state="">Martedì – Domenica · 12:00 – 14:30 · 19:00 – 23:00</p>
  </div>
</section>

<section class="yy-wrap" aria-label="Le due tradizioni">
  <div class="trad trad--cinese">
    <h2>Tradizione cinese</h2>
    <p>Un viaggio lungo la Via della Seta alla ricerca dello Yin e Yang, pilastri della religione e della filosofia cinese che la fanno da padrone anche in cucina.</p>
    <p>I cibi nascono da una <strong>continua ricerca di equilibrio tra gli opposti</strong>: tra i sapori, tra piatti caldi e freddi. Una pietanza cinese deve soddisfare il palato e al contempo la vista e l'olfatto, per regalare un vero viaggio sensoriale in Oriente.</p>
    <a class="go" href="menu.html#cinese">Scopri i piatti cinesi <svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
    <div class="ph"><img src="assets/img/tradizione-cinese.jpg" alt="Piatti della cucina cinese" loading="lazy" width="1400" height="1050"></div>
  </div>
  <div class="trad trad--giapponese">
    <h2>Tradizione giapponese</h2>
    <p>La cucina giapponese è prima di tutto vista, bellezza: pensata per essere assaggiata con gli occhi, gioco estetico di forme e colori.</p>
    <p>Per i nostri chef i coltelli sono strumenti quasi sacri. Il pesce crudo viene servito <strong>perfetto semplicemente grazie al suo taglio</strong>, con ingredienti manipolati il meno possibile per preservare la purezza dei sapori.</p>
    <a class="go" href="menu.html#giapponese">Scopri i piatti giapponesi <svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
    <div class="ph"><img src="assets/img/tradizione-giapponese.jpg" alt="Sushi e piatti della cucina giapponese" loading="lazy" width="1400" height="1050"></div>
  </div>
  <div class="yy" id="yy" aria-hidden="true">{yy_disc("#130a09", "#b8180f")}</div>
</section>

<section class="sec" aria-labelledby="h-menu">
  <div class="wrap menu-strip-head rv">
    <div>
      <h2 class="sec-title" id="h-menu">Un assaggio<br>del menu</h2>
      <p class="sec-intro">Dalle tartare ai ravioli, dal sushi all'anatra alla pechinese: due menu alla carta, tutti da scoprire.</p>
    </div>
    <a class="btn btn--line" href="menu.html">Tutto il menu</a>
  </div>
  <div class="strip" tabindex="0" aria-label="Piatti del menu, scorri di lato">{tiles}</div>
</section>

<section class="sec" aria-labelledby="h-atm" style="background:var(--lacca-2)">
  <div class="wrap atm">
    <div class="atm-text rv">
      <h2 class="sec-title" id="h-atm">Atmosfere<br>orientali.</h2>
      <div class="atm-points" style="margin-top:34px">
        <div><h3>Ingredienti freschi e selezionati</h3><p>Un'esperienza culinaria stimolante sia per gli occhi che per il palato, con le ricette originali della tradizione orientale.</p></div>
        <div><h3>Design moderno e sofisticato</h3><p>È di scena nell'arredamento, nei suoni e sui tavoli del ristorante, con dettagli intimi e minimali.</p></div>
        <div><h3>Tè e cocktail</h3><p>Puoi assaporare l'originale tè cinese o ordinare uno dei cocktail ideati dai nostri barman come accompagnamento a ogni piatto.</p></div>
      </div>
    </div>
    <div class="atm-grid">{atm}</div>
  </div>
</section>

<section class="sec acts" aria-labelledby="h-act">
  <div class="wrap">
    <h2 class="sec-title rv" id="h-act">Vivi l'esperienza Dong</h2>
    <div style="margin-top:44px" class="rv">
      <a class="act" href="tel:{TEL}"><div><h3>Prenota un tavolo</h3><p>Chiamaci dal martedì alla domenica, dalle 10:00 alle 18:30. Anche per la sala privata: compleanni, lauree o una serata tra amici.</p></div><span class="ar"><svg aria-hidden="true"><use href="#i-arrow"/></svg></span></a>
      <a class="act" href="{SHOP}" target="_blank" rel="noopener"><div><h3>Ordina da asporto</h3><p>Scegli i piatti sul nostro shop e ritira in negozio all'orario che indichi nelle note.</p></div><span class="ar"><svg aria-hidden="true"><use href="#i-arrow"/></svg></span></a>
      <a class="act" href="{DELIVEROO}" target="_blank" rel="noopener"><div><h3>Consegna a casa</h3><p>Le nostre specialità a domicilio, con Deliveroo.</p></div><span class="ar"><svg aria-hidden="true"><use href="#i-arrow"/></svg></span></a>
    </div>
  </div>
</section>

<section class="sec" aria-labelledby="h-dove">
  <div class="wrap where">
    <div class="rv">
      <h2 class="sec-title" id="h-dove">Dove siamo</h2>
      <p class="addr" style="margin-top:22px"><a href="{MAPS}" target="_blank" rel="noopener">via Russo, 4<br>San Lazzaro di Savena (BO)</a></p>
      <dl class="hours">
        <div><dt>Martedì – Domenica</dt><dd>12:00 – 14:30 · 19:00 – 23:00</dd></div>
        <div><dt>Lunedì</dt><dd>Chiuso</dd></div>
        <div><dt>Ordini e prenotazioni</dt><dd>Martedì – Domenica, 10:00 – 18:30</dd></div>
      </dl>
      <div class="btn-row" style="margin-top:28px"><a class="btn btn--oro" href="{MAPS}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-pin"/></svg>Indicazioni</a><a class="btn btn--line" href="tel:{TEL}">{TEL_VIEW}</a></div>
    </div>
    <a class="map rv" href="{MAPS}" target="_blank" rel="noopener" aria-label="Apri la mappa"><img src="assets/img/mappa.jpg" alt="Mappa: Ristorante Dong, via Russo 4, San Lazzaro di Savena" loading="lazy" width="1200" height="900"><span><svg aria-hidden="true"><use href="#i-pin"/></svg>Apri la mappa</span></a>
  </div>
</section>
</main>
"""
    desc = "Ristorante Dong, fusion restaurant a San Lazzaro di Savena (Bologna): cucina cinese e giapponese alla carta. Sfoglia il menu, prenota un tavolo o ordina da asporto."
    return head("Ristorante Dong · Cucina cinese e giapponese a Bologna", desc, "index.html", ld_json()) + header("index.html") + body + footer() + "</body>\n</html>\n"


# ---------------------------------------------------------------- MENU
def render_menu():
    chips = {"giapponese": [], "cinese": []}
    groups = []
    for g in ("giapponese", "cinese"):
        cats = []
        for cid, title, intro, dishes in MENU[g]:
            chips[g].append(f'<a href="#{cid}" data-cat="{cid}">{e(title)}</a>')
            ph = photos_for(cid)
            strip = ""
            if ph:
                figs = "".join(
                    f'<figure><img src="assets/menu/{cid}/{f}" alt="{e(caption(f))}" loading="lazy" width="520" height="650"><figcaption>{e(caption(f))}</figcaption></figure>'
                    for f in ph
                )
                strip = f'<div class="cat-strip" tabindex="0" aria-label="Foto: {e(title)}">{figs}</div>'
            lis = "".join(
                f'<li><h4>{e(n)}</h4>' + (f"<p>{e(d)}</p>" if d else "") + "</li>" for n, d in dishes
            )
            cats.append(
                f'<section class="cat" id="{cid}" data-group="{g}"><div class="cat-head"><h2>{e(title)}</h2><p>{e(intro)}</p></div>{strip}<ul class="dishes">{lis}</ul></section>'
            )
        label = "Cucina giapponese" if g == "giapponese" else "Cucina cinese"
        groups.append(f'<div class="group" id="{g}" data-group="{g}" aria-label="{label}">{"".join(cats)}</div>')
    return chips, "".join(groups)


def page_menu():
    chips, groups = render_menu()
    chips_html = "".join(
        f'<div class="chips" data-for="{g}" aria-label="Categorie {g}">{"".join(chips[g])}</div>' for g in ("giapponese", "cinese")
    )
    body = f"""<main id="main">
<section class="page-hero">
  <img class="bgmark" src="assets/img/logo-stroke.png" alt="" width="520" height="520">
  <div class="wrap">
    <h1>Il menu</h1>
    <p>Due cucine alla carta: giapponese e cinese. Cambia tradizione con l'interruttore, o cerca un piatto per nome o ingrediente.</p>
  </div>
</section>
<div class="wrap menu-search"><div class="search"><svg aria-hidden="true"><use href="#i-search"/></svg><input id="q" type="search" placeholder="Cerca un piatto o un ingrediente" aria-label="Cerca nel menu" autocomplete="off" enterkeyhint="search"></div></div>
<div class="menu-bar" id="menubar">
  <div class="wrap menu-bar-in">
    <div class="switch" role="tablist" aria-label="Tradizione">
      <button type="button" role="tab" id="tab-giapponese" aria-selected="true" aria-controls="giapponese" data-g="giapponese"><svg class="yy-i" viewBox="0 0 100 100" aria-hidden="true" style="--yy-a:#130a09;--yy-b:#b8180f"><use href="#yy"/></svg>Giapponese</button>
      <button type="button" role="tab" id="tab-cinese" aria-selected="false" aria-controls="cinese" data-g="cinese"><svg class="yy-i" viewBox="0 0 100 100" aria-hidden="true" style="--yy-a:#130a09;--yy-b:#b8180f"><use href="#yy"/></svg>Cinese</button>
    </div>
    {chips_html}
  </div>
</div>
<div class="wrap">
  <p class="menu-note">Per i prezzi e per eventuali allergie o intolleranze rivolgiti al personale in sala, o consulta lo <a href="{SHOP}" target="_blank" rel="noopener">shop online</a>.</p>
  <p class="empty" id="empty" hidden>Nessun piatto trovato. Prova con un altro ingrediente, per esempio «salmone» o «gambero».</p>
  {groups}
</div>
</main>
"""
    desc = "Il menu del Ristorante Dong: sushi, sashimi, tartare, uramaki e specialità giapponesi; ravioli, primi, anatra, pesce e piatti vegetariani della cucina cinese."
    return head("Menu · Ristorante Dong Bologna", desc, "menu.html") + header("menu.html") + body + footer() + '<script src="js/menu.js"></script>\n</body>\n</html>\n'


# ---------------------------------------------------------------- PRENOTA
def page_prenota():
    body = f"""<main id="main">
<section class="page-hero">
  <img class="bgmark" src="assets/img/logo-stroke.png" alt="" width="520" height="520">
  <div class="wrap">
    <h1>Prenota<br>e ordina</h1>
    <p>Un tavolo in sala, il cibo a casa tua o da ritirare: scegli come vivere la cucina del Dong.</p>
  </div>
</section>

<section class="sec" style="padding-top:20px">
  <div class="wrap book">
    <div class="book-card rv">
      <h2>Quando vuoi venire?</h2>
      <p style="color:var(--carta-soft)">Scegli giorno e turno: ti diciamo se siamo aperti. Per prenotare serve una telefonata.</p>
      <div class="field"><label for="d">Giorno</label><input id="d" type="date"></div>
      <fieldset class="field"><legend>Turno</legend>
        <div class="turni"><label><input type="radio" name="t" value="pranzo" checked><span>Pranzo</span></label><label><input type="radio" name="t" value="cena"><span>Cena</span></label></div>
      </fieldset>
      <div class="verdict" id="verdict" role="status" aria-live="polite">Scegli un giorno.</div>
      <a class="btn btn--oro" href="tel:{TEL}"><svg aria-hidden="true"><use href="#i-phone"/></svg>Chiama per prenotare</a>
    </div>
    <div class="rv">
      <a class="tel-big" href="tel:{TEL}">{TEL_VIEW}</a>
      <dl class="hours" style="margin-top:24px">
        <div><dt>Telefono</dt><dd>Martedì – Domenica, 10:00 – 18:30</dd></div>
        <div><dt>Pranzo</dt><dd>12:00 – 14:30</dd></div>
        <div><dt>Cena</dt><dd>19:00 – 23:00</dd></div>
        <div><dt>Lunedì</dt><dd>Chiuso</dd></div>
      </dl>
      <p style="margin-top:20px;color:var(--carta-soft)">Nei giorni festivi gli orari possono cambiare: chiamaci per conferma.</p>
    </div>
  </div>
</section>

<figure class="photo-band"><img src="assets/img/prenota.jpg" alt="Un tavolo apparecchiato al Ristorante Dong" loading="lazy" width="1400" height="613"></figure>

<section class="sec" style="background:var(--lacca-2)" aria-labelledby="h-way">
  <div class="wrap">
    <h2 class="sec-title rv" id="h-way">Come ordinare</h2>
    <div class="way" style="margin-top:44px">
      <article class="rv"><h3>In sala</h3><p>Il nostro staff è a tua disposizione per illustrarti ogni portata e per consigliarti tra le specialità delle due cucine. Puoi anche riservare una <strong>sala privata</strong> per compleanni, lauree o una serata con gli amici.</p><div class="btn-row"><a class="btn btn--oro" href="tel:{TEL}"><svg aria-hidden="true"><use href="#i-phone"/></svg>{TEL_VIEW}</a></div></article>
      <article class="rv"><h3>Asporto</h3><p>Chiama il {TEL_VIEW} dal martedì alla domenica, dalle 10:00 alle 18:30, oppure scegli i piatti sul nostro shop e indica nelle note l'orario del ritiro: il tuo ordine ti aspetta pronto nel locale. Il pagamento si può fare online con PayPal o carta di credito o debito, oppure al ritiro.</p><div class="btn-row"><a class="btn btn--oro" href="{SHOP}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-bag"/></svg>Apri lo shop</a><a class="btn btn--line" href="tel:{TEL}">Chiama</a></div></article>
      <article class="rv"><h3>Consegna a domicilio</h3><p>Compila il tuo ordine e inviacelo tramite Deliveroo: faremo arrivare le nostre specialità alla destinazione che hai inserito.</p><div class="btn-row"><a class="btn btn--oro" href="{DELIVEROO}" target="_blank" rel="noopener">Ordina su Deliveroo</a></div></article>
    </div>
  </div>
</section>
</main>
"""
    desc = "Prenota un tavolo al Ristorante Dong, ordina da asporto sullo shop o fatti consegnare a casa con Deliveroo. Martedì – Domenica."
    return head("Prenota e ordina · Ristorante Dong Bologna", desc, "prenota.html") + header("prenota.html") + body + footer() + '<script src="js/prenota.js"></script>\n</body>\n</html>\n'


# ---------------------------------------------------------------- DOVE SIAMO
def page_dove():
    soc_btns = "".join(f'<a class="btn btn--line" href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in SOCIAL)
    body = f"""<main id="main">
<section class="page-hero">
  <img class="bgmark" src="assets/img/logo-stroke.png" alt="" width="520" height="520">
  <div class="wrap">
    <h1>Dove siamo</h1>
    <p>A San Lazzaro di Savena, alle porte di Bologna.</p>
  </div>
</section>
<section class="sec" style="padding-top:24px">
  <div class="wrap where">
    <div class="rv">
      <p class="addr"><a href="{MAPS}" target="_blank" rel="noopener">via Russo, 4<br>40068 San Lazzaro di Savena (BO)</a></p>
      <p class="status" id="status" data-state="" style="margin-top:22px">Martedì – Domenica</p>
      <dl class="hours">
        <div><dt>Pranzo</dt><dd>Martedì – Domenica, 12:00 – 14:30</dd></div>
        <div><dt>Cena</dt><dd>Martedì – Domenica, 19:00 – 23:00</dd></div>
        <div><dt>Lunedì</dt><dd>Chiuso</dd></div>
        <div><dt>Telefono</dt><dd><a href="tel:{TEL}">{TEL_VIEW}</a> · Martedì – Domenica, 10:00 – 18:30</dd></div>
      </dl>
      <div class="btn-row" style="margin-top:28px"><a class="btn btn--oro" href="{MAPS}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-pin"/></svg>Indicazioni</a><a class="btn btn--line" href="tel:{TEL}"><svg aria-hidden="true"><use href="#i-phone"/></svg>Chiama</a></div>
      <p style="margin-top:22px;color:var(--carta-soft)">Nei giorni festivi gli orari possono variare: chiamaci per conferma.</p>
    </div>
    <a class="map rv" href="{MAPS}" target="_blank" rel="noopener" aria-label="Apri la mappa"><img src="assets/img/mappa.jpg" alt="Mappa: Ristorante Dong, via Russo 4, San Lazzaro di Savena" loading="lazy" width="1200" height="900"><span><svg aria-hidden="true"><use href="#i-pin"/></svg>Apri la mappa</span></a>
  </div>
</section>
<section class="sec acts" aria-labelledby="h-c">
  <div class="wrap">
    <h2 class="sec-title rv" id="h-c">Seguici</h2>
    <div class="btn-row rv" style="margin-top:28px">{soc_btns}<a class="btn btn--line" href="https://www.ristorantedong.it/lavora-con-noi" target="_blank" rel="noopener">Lavora con noi</a></div>
  </div>
</section>
</main>
"""
    desc = "Ristorante Dong si trova in via Russo 4, a San Lazzaro di Savena (Bologna). Orari, telefono e indicazioni."
    return head("Dove siamo e contatti · Ristorante Dong Bologna", desc, "dove-siamo.html") + header("dove-siamo.html") + body + footer() + "</body>\n</html>\n"


def main():
    pages = {"index.html": page_home(), "menu.html": page_menu(), "prenota.html": page_prenota(), "dove-siamo.html": page_dove()}
    for name, content in pages.items():
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(content)
        print("scritto", name, len(content))


if __name__ == "__main__":
    main()
