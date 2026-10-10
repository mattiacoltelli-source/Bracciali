(function () {
  "use strict";

  var SITE = window.SITE, PRODUCTS = window.PRODUCTS;
  var plate = document.getElementById("plate");
  var face = plate.querySelector(".plate-face");
  var engraving = document.getElementById("engraving");
  var input = document.getElementById("text");
  var count = document.getElementById("count");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var state = { text: input.value, style: "corsivo" };
  var BASE = { corsivo: 0.78, romano: 0.4, blocco: 0.52 }; // fattore sull'altezza della lastra

  /* ---------- Anteprima incisione ---------- */
  function fit() {
    var avail = face.clientWidth - 8;
    var h = face.clientHeight;
    var size = Math.max(16, h * BASE[state.style]);
    engraving.style.fontSize = size + "px";
    var guard = 60;
    while (engraving.scrollWidth > avail && size > 12 && guard--) {
      size -= 2;
      engraving.style.fontSize = size + "px";
    }
  }

  function render() {
    var t = state.text.trim();
    engraving.textContent = t;
    engraving.classList.toggle("is-empty", !t);
    engraving.dataset.style = state.style;
    plate.setAttribute("aria-label", t ? "Anteprima dell'incisione: " + t : "Anteprima dell'incisione");
    var max = input.maxLength;
    count.textContent = state.text.length + "/" + max;
    count.classList.toggle("is-full", state.text.length >= max);
    fit();
    updateLinks();
  }

  function burn() {
    if (reduceMotion) return;
    plate.classList.remove("is-burning");
    void plate.offsetWidth; // riavvia l'animazione
    plate.classList.add("is-burning");
  }

  input.addEventListener("input", function () { state.text = input.value; render(); });
  document.querySelectorAll('input[name="style"]').forEach(function (r) {
    r.addEventListener("change", function () { state.style = r.value; render(); burn(); });
  });
  document.querySelectorAll(".ideas button").forEach(function (b) {
    b.addEventListener("click", function () {
      state.text = b.dataset.idea; input.value = state.text; render(); burn();
    });
  });
  window.addEventListener("resize", fit);
  if (document.fonts) {
    document.fonts.addEventListener("loadingdone", fit);
    ["56px Allura", "40px Cinzel", "40px Antonio"].forEach(function (f) { document.fonts.load(f).then(fit); });
  }

  /* ---------- Contatti ---------- */
  function waLink(message) {
    return "https://wa.me/" + SITE.whatsapp + "?text=" + encodeURIComponent(message);
  }
  function messageFor(p) {
    var t = state.text.trim();
    var msg = "Ciao! Vorrei il bracciale «" + p.name + "» (" + p.price + " €).";
    if (t) msg += " Testo da incidere: «" + t + "».";
    return msg;
  }
  function updateLinks() {
    document.querySelectorAll("[data-wa]").forEach(function (a) {
      var p = PRODUCTS.find(function (x) { return x.id === a.dataset.wa; });
      a.href = waLink(messageFor(p));
    });
    document.querySelectorAll("[data-mine]").forEach(function (el) {
      var t = state.text.trim();
      el.hidden = !t;
      var q = el.querySelector("q");
      if (q) q.textContent = t;
    });
    var wa = document.getElementById("contact-wa");
    wa.href = waLink("Ciao! Vorrei informazioni sui vostri bracciali incisi.");
    document.getElementById("contact-mail").href = "mailto:" + SITE.email + "?subject=" + encodeURIComponent("Informazioni bracciali");
  }

  /* ---------- Catalogo ---------- */
  function el(tag, cls, html) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function photoSrc(name) { return "assets/products/" + name + ".jpg"; }

  function buildItem(p, index) {
    var item = el("article", "item");
    item.id = p.id;
    item.setAttribute("aria-labelledby", "t-" + p.id);

    var gallery = el("div", "gallery");
    var slip = el("div", "slip");
    var main = new Image();
    main.src = photoSrc(p.photos[0]);
    main.alt = p.alt;
    main.width = 1000; main.height = 1000;
    main.decoding = "async";
    if (index > 0) main.loading = "lazy";
    slip.appendChild(main);
    gallery.appendChild(slip);

    if (p.photos.length > 1) {
      var thumbs = el("div", "thumbs");
      thumbs.setAttribute("role", "group");
      thumbs.setAttribute("aria-label", "Foto di " + p.name);
      p.photos.forEach(function (name, i) {
        var b = el("button", "thumb");
        b.type = "button";
        b.setAttribute("aria-label", "Mostra foto " + (i + 1) + " di " + p.photos.length);
        if (i === 0) b.setAttribute("aria-current", "true");
        var im = new Image();
        im.src = photoSrc(name); im.alt = ""; im.loading = "lazy"; im.width = 128; im.height = 128;
        b.appendChild(im);
        b.addEventListener("click", function () {
          main.style.opacity = "0";
          setTimeout(function () { main.src = photoSrc(name); main.style.opacity = ""; }, 120);
          thumbs.querySelectorAll(".thumb").forEach(function (x) { x.removeAttribute("aria-current"); });
          b.setAttribute("aria-current", "true");
        });
        thumbs.appendChild(b);
      });
      gallery.appendChild(thumbs);
    }

    var info = el("div", "info");
    info.appendChild(el("h3", null, esc(p.name))).id = "t-" + p.id;
    info.appendChild(el("p", "tagline", esc(p.tagline)));
    info.appendChild(el("p", "price", p.price + " €" + (p.id === "coppia" ? "<small>il set di due</small>" : "")));

    var dl = el("dl", "specs");
    p.specs.forEach(function (s) {
      dl.appendChild(el("div", null, "<dt>" + esc(s[0]) + "</dt><dd>" + esc(s[1]) + "</dd>"));
    });
    info.appendChild(dl);

    var mine = el("p", "mine", "Con la tua incisione: <q></q> · <a href=\"#top\">cambia</a>");
    mine.setAttribute("data-mine", "");
    info.appendChild(mine);

    var actions = el("div", "actions");
    var wa = el("a", "btn btn--brass", "Richiedi su WhatsApp");
    wa.target = "_blank"; wa.rel = "noopener"; wa.setAttribute("data-wa", p.id);
    actions.appendChild(wa);
    info.appendChild(actions);

    item.appendChild(gallery);
    item.appendChild(info);
    return item;
  }

  var catalogo = document.getElementById("catalogo");
  PRODUCTS.forEach(function (p, i) { catalogo.appendChild(buildItem(p, i)); });

  document.title = SITE.brand + " – Bracciali incisi in acciaio";
  render();
  // il laser incide il testo una volta all'apertura
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { fit(); burn(); }); else burn();
})();
