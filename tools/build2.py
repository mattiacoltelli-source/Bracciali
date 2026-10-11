#!/usr/bin/env python3
"""Genera le pagine del sito (index, menu, prenota, dove-siamo) con il nuovo stile.

Uso:  python3 tools/build2.py
I dati del menu e i contatti vengono da tools/build.py (stessi testi del sito originale).
Il sito pubblicato è fatto solo di file statici.
"""
import json, os, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B

ROOT = B.ROOT
e = B.e
TEL, TEL_VIEW, MAPS, SHOP, DELIVEROO = B.TEL, B.TEL_VIEW, B.MAPS, B.SHOP, B.DELIVEROO

LD = {"@context": "https://schema.org", "@type": "Restaurant", "name": "Ristorante Dong",
      "description": "Fusion restaurant: cucina cinese e giapponese alla carta a San Lazzaro di Savena, Bologna.",
      "servesCuisine": ["Cinese", "Giapponese"], "telephone": TEL,
      "address": {"@type": "PostalAddress", "streetAddress": "via Russo, 4", "postalCode": "40068", "addressLocality": "San Lazzaro di Savena", "addressRegion": "BO", "addressCountry": "IT"},
      "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "opens": o, "closes": c} for o, c in (("12:00", "14:30"), ("19:00", "23:00"))],
      "hasMenu": "menu.html", "image": "assets/img/sala-hero.jpg", "sameAs": [u for _, u in B.SOCIAL]}

ICON = {
    "menu": '<path d="M6 3v8M9 3v8M6 7h3M7.5 11v10M17 3c-2 2-3 5-3 8h3v10"/>',
    "cal": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/>',
    "tel": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    "pin": '<path d="M12 21s7-6 7-11a7 7 0 0 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
}
def svg(k, cls=""):
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[k]}</svg>'

def head(title, desc, extra=""):
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0c0a0a">
<link rel="icon" type="image/png" href="assets/favicon.png">
<link rel="preload" href="assets/fonts2/ShipporiMincho-700.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="css/app.css">
<script>document.documentElement.classList.add("js")</script>
{extra}</head>
"""

def header(page):
    def a(href, label):
        cur = ' aria-current="page"' if href == page else ""
        return f'<a href="{href}"{cur}>{label}</a>'
    return f"""<a class="skip" href="#main">Vai al contenuto</a>
<header class="top" id="top">
  <a href="./" aria-label="Ristorante Dong, home"><img src="assets/img/logo-inverse.png" alt="Dong" width="83" height="44"></a>
  <nav class="nav" aria-label="Principale">{a("menu.html", "Menu")}{a("prenota.html", "Prenota e ordina")}{a("dove-siamo.html", "Dove siamo")}<a href="tel:{TEL}">{TEL_VIEW}</a></nav>
  <a class="btn red" href="prenota.html">Prenota</a>
</header>
"""

def footer(page):
    soc = "".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in B.SOCIAL)
    leg = "".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in B.LEGAL)
    def tab(href, label, icon, cls="", ext=False):
        c = " ".join(x for x in (cls, "on" if href == page else "") if x)
        t = ' target="_blank" rel="noopener"' if ext else ""
        ic = f"<b>{svg(icon)}</b>" if cls == "cta" else svg(icon)
        return f'<a{(" class=" + chr(34) + c + chr(34)) if c else ""} href="{href}"{t}>{ic}{label}</a>'
    return f"""<footer>
  <div class="w">
    <div class="brand"><img class="fseal" src="assets/img/logo-stroke.png" alt="" width="60" height="64"><img src="assets/img/logo-inverse.png" alt="Dong" width="76" height="40"></div>
    <p>Ristorante Dong · Fusion restaurant · Cucina cinese e giapponese a Bologna</p>
    <p><a href="{MAPS}" target="_blank" rel="noopener">via Russo, 4 · 40068 San Lazzaro di Savena (BO)</a> · <a href="tel:{TEL}">{TEL_VIEW}</a></p>
    <div class="soc">{soc}<a href="https://www.ristorantedong.it/lavora-con-noi" target="_blank" rel="noopener">Lavora con noi</a></div>
    <p>Mizuumi SRL · P.IVA 03504171202</p>
    <div class="leg">{leg}</div>
  </div>
</footer>
<nav class="tabs" aria-label="Azioni rapide">
  {tab("menu.html", "Menu", "menu")}
  {tab("prenota.html", "Prenota", "cal", "cta")}
  {tab("tel:" + TEL, "Chiama", "tel")}
  {tab(MAPS, "Mappa", "pin", ext=True)}
</nav>
<script src="js/app.js" defer></script>
"""

def page_hero(h1, p, extra=""):
    return f'<section class="phero"><div class="w"><span class="rule"></span><h1>{h1}</h1><p class="lead">{p}</p>{extra}</div></section>\n'

def write(name, html):
    with open(os.path.join(ROOT, name), "w", encoding="utf8") as f:
        f.write(html)

# ------------------------------------------------------------ HOME
def page_home():
    main = open(os.path.join(ROOT, "tools", "home_main.html"), encoding="utf8").read().replace("@MAPS@", MAPS)
    ld = f'<script type="application/ld+json">{json.dumps(LD, ensure_ascii=False)}</script>\n'
    return head("Ristorante Dong · Cucina cinese e giapponese a Bologna", "Fusion restaurant: cucina cinese e giapponese alla carta a San Lazzaro di Savena, Bologna. Prenota un tavolo.", ld) \
        + "<body>\n" + header("index.html") + main + "\n" + footer("index.html") + "</body>\n</html>\n"

# ------------------------------------------------------------ MENU
def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")

def page_menu():
    chips, groups = [], []
    for g, label in (("giapponese", "Giapponese"), ("cinese", "Cinese")):
        row, cats = [], []
        for cid, title, intro, dishes in B.MENU[g]:
            row.append(f'<a href="#{cid}" data-cat="{cid}">{e(title)}</a>')
            ph = B.photos_for(cid)
            strip = ""
            if ph:
                figs = "".join(f'<figure><img src="assets/menu/{cid}/{f}" alt="{e(B.caption(f))}" loading="lazy" width="150" height="188"><figcaption>{e(B.caption(f))}</figcaption></figure>' for f in ph)
                strip = f'<div class="mstrip" tabindex="0" aria-label="Foto: {e(title)}">{figs}</div>'
            lis = "".join(f'<li data-s="{e(norm(n + " " + d))}"><h4>{e(n)}</h4>' + (f"<p>{e(d)}</p>" if d else "") + "</li>" for n, d in dishes)
            cats.append(f'<section class="mcat" id="{cid}"><h3>{e(title)}</h3><p class="mi">{e(intro)}</p>{strip}<ul class="dl">{lis}</ul></section>')
        chips.append(f'<div class="chips" data-for="{g}" role="tablist" aria-label="Categorie {label}"{"" if g == "giapponese" else " hidden"}>{"".join(row)}</div>')
        groups.append(f'<div class="mgroup" id="{g}" aria-label="Cucina {g}"{"" if g == "giapponese" else " hidden"}><h2 class="gt">Cucina {g}</h2>{"".join(cats)}</div>')
    body = f"""<main id="main" class="menu">
{page_hero("Il menu", "Due menu alla carta, tutti da scoprire. Scegli la tradizione e scorri le categorie.")}
<div class="w"><div class="search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4-4"/></svg><input id="q" type="search" placeholder="Cerca un piatto o un ingrediente" aria-label="Cerca nel menu" autocomplete="off" enterkeyhint="search"></div></div>
<div class="mbar" id="mbar">
  <div class="w">
    <div class="switch" role="tablist" aria-label="Tradizione"><button type="button" role="tab" aria-selected="true" data-g="giapponese">Giapponese</button><button type="button" role="tab" aria-selected="false" data-g="cinese">Cinese</button></div>
    {"".join(chips)}
  </div>
</div>
<div class="w mbody">
  <p class="note">Per i prezzi e per eventuali allergie o intolleranze rivolgiti al personale in sala, o consulta lo <a href="{SHOP}" target="_blank" rel="noopener">shop online</a>.</p>
  <p class="empty" id="empty" hidden>Nessun piatto trovato. Prova con un altro ingrediente, per esempio «salmone» o «gambero».</p>
  {"".join(groups)}
</div>
</main>
"""
    return head("Menu · Ristorante Dong Bologna", "Il menu del Ristorante Dong: sushi, sashimi, tartare, uramaki e specialità giapponesi; ravioli, primi, anatra, pesce e piatti vegetariani della cucina cinese.") \
        + '<body class="pg-menu">\n' + header("menu.html") + body + footer("menu.html") + '<script src="js/menu.js" defer></script>\n</body>\n</html>\n'

# ------------------------------------------------------------ PRENOTA
def page_prenota():
    body = f"""<main id="main">
{page_hero("Prenota e ordina", "Un tavolo in sala, il cibo a casa tua o da ritirare.")}
<section class="sec bk" aria-labelledby="h-bk" style="padding-top:8px">
  <div class="w">
    <form class="bcard" id="bform" novalidate>
      <h2 id="h-bk">Prenota un tavolo</h2>
      <fieldset><legend><b>1</b>Giorno</legend><div class="opts days" id="days"></div></fieldset>
      <fieldset id="fs-turno" disabled><legend><b>2</b>Turno</legend><div class="opts" id="turni"></div></fieldset>
      <fieldset id="fs-ora" disabled><legend><b>3</b>Orario</legend><div class="opts" id="ore"><span class="hint">Scegli prima giorno e turno.</span></div></fieldset>
      <fieldset><legend><b>4</b>Persone</legend>
        <div class="step"><button type="button" id="minus" aria-label="Una persona in meno">−</button><output id="n" aria-live="polite">2</output><button type="button" id="plus" aria-label="Una persona in più">+</button></div>
        <p class="hint">Per gruppi più grandi o per la sala privata chiamaci.</p></fieldset>
      <fieldset><legend><b>5</b>A nome di</legend><input id="nome" type="text" autocomplete="name" placeholder="Nome e cognome" aria-label="Nome e cognome"></fieldset>
      <p class="sum" id="sum" role="status" aria-live="polite">Scegli giorno, turno e orario.</p>
      <button class="btn red wa" id="send" type="submit" disabled><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 12a8 8 0 0 1-11.8 7L4 20l1.1-4A8 8 0 1 1 20 12z"/><path d="M9 9.5c.3 2 1.800 3.700 4 4.500l1.200-1.200-1.600-.9-.7.600c-.8-.4-1.500-1.100-1.900-1.900l.6-.7-.9-1.600z"/></svg>Invia su WhatsApp</button>
      <a class="btn line" href="tel:{TEL}">{svg("tel")}Preferisci chiamare? {TEL_VIEW}</a>
      <p class="hint">Telefono: martedì – domenica, 10:00 – 18:30. Nei giorni festivi gli orari possono cambiare: chiamaci per conferma.</p>
    </form>
  </div>
</section>
<figure class="band"><img src="assets/img/prenota.jpg" alt="Un tavolo apparecchiato al Ristorante Dong" loading="lazy" width="1000" height="500"></figure>
<section class="sec" aria-labelledby="h-way">
  <div class="w">
    <div class="rv"><span class="rule"></span><h2 id="h-way">Come ordinare</h2></div>
    <div class="way">
      <article class="rv"><h3>In sala</h3><p>Il nostro staff è a tua disposizione per illustrarti ogni portata e per consigliarti tra le specialità delle due cucine. Puoi anche riservare una <strong>sala privata</strong> per compleanni, lauree o una serata con gli amici.</p><div class="ctas"><a class="btn red" href="tel:{TEL}">{svg("tel")}{TEL_VIEW}</a></div></article>
      <article class="rv"><h3>Asporto</h3><p>Chiama il {TEL_VIEW} dal martedì alla domenica, dalle 10:00 alle 18:30, oppure scegli i piatti sul nostro shop e indica nelle note l'orario del ritiro: il tuo ordine ti aspetta pronto nel locale. Il pagamento si può fare online con PayPal o carta di credito o debito, oppure al ritiro.</p><div class="ctas"><a class="btn line" href="{SHOP}" target="_blank" rel="noopener">Apri lo shop</a><a class="btn line" href="tel:{TEL}">Chiama</a></div></article>
      <article class="rv"><h3>Consegna a domicilio</h3><p>Compila il tuo ordine e inviacelo tramite Deliveroo: faremo arrivare le nostre specialità alla destinazione che hai inserito.</p><div class="ctas"><a class="btn line" href="{DELIVEROO}" target="_blank" rel="noopener">Ordina su Deliveroo</a></div></article>
    </div>
  </div>
</section>
</main>
"""
    return head("Prenota e ordina · Ristorante Dong Bologna", "Prenota un tavolo al Ristorante Dong, ordina da asporto sullo shop o fatti consegnare a casa con Deliveroo. Martedì – Domenica.") \
        + '<body class="pg-book">\n' + header("prenota.html") + body + footer("prenota.html") + '<script src="js/prenota.js" defer></script>\n</body>\n</html>\n'

# ------------------------------------------------------------ DOVE SIAMO
def page_dove():
    body = f"""<main id="main">
{page_hero("Dove siamo", "A San Lazzaro di Savena, alle porte di Bologna.")}
<section class="sec where" style="padding-top:8px">
  <div class="w">
    <span class="status" id="status" role="status"><i></i><span>Martedì – Domenica · 12:00 – 14:30 · 19:00 – 23:00</span></span>
    <div class="grid">
      <div>
        <p class="addr"><a href="{MAPS}" target="_blank" rel="noopener">via Russo, 4<br>40068 San Lazzaro di Savena (BO)</a></p>
        <table class="hours" id="hours" aria-label="Orari">
          <tr data-d="2"><td>Pranzo</td><td>Martedì – Domenica<br>12:00 – 14:30</td></tr>
          <tr data-d="2b"><td>Cena</td><td>Martedì – Domenica<br>19:00 – 23:00</td></tr>
          <tr data-d="1"><td>Lunedì</td><td>Chiuso</td></tr>
          <tr><td>Telefono</td><td><a href="tel:{TEL}">{TEL_VIEW}</a><br>10:00 – 18:30</td></tr>
        </table>
        <p class="lead" style="font-size:.92rem">Nei giorni festivi gli orari possono variare: chiamaci per conferma.</p>
      </div>
      <div style="display:grid;gap:14px">
        <a class="map" href="{MAPS}" target="_blank" rel="noopener" aria-label="Apri la mappa"><img src="assets/img/mappa.jpg" alt="Mappa: Ristorante Dong, via Russo 4, San Lazzaro di Savena" width="830" height="316"><span>Apri la mappa</span></a>
        <div class="ctas"><a class="btn red" href="{MAPS}" target="_blank" rel="noopener">{svg("pin")}Indicazioni</a><a class="btn line" href="tel:{TEL}">{svg("tel")}Chiama</a></div>
      </div>
    </div>
  </div>
</section>
</main>
"""
    return head("Dove siamo e contatti · Ristorante Dong Bologna", "Ristorante Dong si trova in via Russo 4, a San Lazzaro di Savena (Bologna). Orari, telefono e indicazioni.") \
        + "<body>\n" + header("dove-siamo.html") + body + footer("dove-siamo.html") + "</body>\n</html>\n"

if __name__ == "__main__":
    write("index.html", page_home()); write("menu.html", page_menu()); write("prenota.html", page_prenota()); write("dove-siamo.html", page_dove())
    print("ok")
