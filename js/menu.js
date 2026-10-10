(function () {
  "use strict";
  var groups = { giapponese: document.getElementById("giapponese"), cinese: document.getElementById("cinese") };
  var tabs = document.querySelectorAll(".switch button");
  var chipRows = document.querySelectorAll(".chips");
  var q = document.getElementById("q");
  var empty = document.getElementById("empty");
  var bar = document.getElementById("menubar");
  var fab = document.getElementById("fab");
  var root = document.documentElement;
  var current = "giapponese";
  var lockUntil = 0;      // dopo un salto, lo scroll-spy aspetta
  var userTouched = 0;    // ultimo gesto dell'utente (annulla le correzioni automatiche)
  var chipsTouched = 0;   // ultimo gesto sulla riga dei filtri

  root.style.scrollBehavior = "auto"; // salti diretti, senza scorrimenti lunghi

  function headH() { return parseInt(getComputedStyle(root).getPropertyValue("--header-h"), 10) || 68; }
  function barH() { return bar.hidden ? 0 : bar.offsetHeight; }
  function offsetTop() { return headH() + barH() + 12; }
  function syncBarVar() { root.style.setProperty("--bar-h", barH() + "px"); }

  // ---- tradizione (giapponese / cinese)
  function setTradition(g, opts) {
    opts = opts || {};
    current = g;
    document.body.dataset.trad = g;
    tabs.forEach(function (t) { t.setAttribute("aria-selected", String(t.dataset.g === g)); });
    chipRows.forEach(function (r) { r.hidden = r.dataset.for !== g; });
    Object.keys(groups).forEach(function (k) { groups[k].hidden = k !== g; });
    document.querySelector('meta[name="theme-color"]').setAttribute("content", g === "cinese" ? "#b8180f" : "#130a09");
    syncBarVar();
    chipRows.forEach(fades);
    if (opts.scroll) {
      var y = groups[g].getBoundingClientRect().top + window.scrollY - offsetTop();
      window.scrollTo(0, Math.max(0, y));
    }
    spy(true);
    if (!opts.keepHash && history.replaceState) history.replaceState(null, "", "#" + g);
  }

  tabs.forEach(function (t) {
    t.addEventListener("click", function () {
      if (q.value) { q.value = ""; filter(); }
      setTradition(t.dataset.g, { scroll: true });
    });
  });

  // ---- filtri (categorie): salto + evidenziazione
  var links = {};
  document.querySelectorAll(".chips a").forEach(function (a) { links[a.dataset.cat] = a; });

  function centerChip(id) {
    var a = links[id];
    if (!a || !a.offsetParent || Date.now() - chipsTouched < 1500) return;
    var row = a.parentElement;
    var x = a.offsetLeft - (row.clientWidth - a.offsetWidth) / 2;
    row.scrollTo({ left: Math.max(0, x), behavior: "smooth" });
  }

  var activeId = null;
  function setActive(id) {
    if (id === activeId) return;
    activeId = id;
    Object.keys(links).forEach(function (k) {
      if (k === id) links[k].setAttribute("aria-current", "true"); else links[k].removeAttribute("aria-current");
    });
    if (id) centerChip(id);
  }

  function visibleCats() {
    return Array.prototype.slice.call(document.querySelectorAll(".group:not([hidden]) .cat:not([hidden])"));
  }

  function spy(force) {
    if (!force && Date.now() < lockUntil) return;
    if (q.value) { setActive(null); return; }
    var cats = visibleCats();
    if (!cats.length) return;
    var line = offsetTop() + 8, best = cats[0].id;
    for (var i = 0; i < cats.length; i++) {
      if (cats[i].getBoundingClientRect().top <= line) best = cats[i].id; else break;
    }
    setActive(best);
  }

  function jumpTo(id) {
    var el = document.getElementById(id);
    if (!el) return;
    lockUntil = Date.now() + 900;
    setActive(id);
    var stamp = Date.now();
    userTouched = 0;
    var go = function () {
      if (userTouched > stamp) return; // l'utente ha ripreso a scorrere
      var y = el.getBoundingClientRect().top + window.scrollY - offsetTop();
      if (Math.abs(el.getBoundingClientRect().top - offsetTop()) > 3) window.scrollTo(0, Math.max(0, y));
    };
    go();
    setTimeout(go, 150);  // corregge eventuali spostamenti dovuti alle immagini che si caricano
    setTimeout(go, 500);
    if (history.replaceState) history.replaceState(null, "", "#" + id);
  }

  Object.keys(links).forEach(function (id) {
    links[id].addEventListener("click", function (e) { e.preventDefault(); jumpTo(id); });
  });
  document.querySelectorAll(".chips").forEach(function (r) {
    r.addEventListener("touchstart", function () { chipsTouched = Date.now(); }, { passive: true });
    r.addEventListener("wheel", function () { chipsTouched = Date.now(); }, { passive: true });
  });
  function fades(r) {
    r.classList.toggle("has-left", r.scrollLeft > 6);
    r.classList.toggle("at-end", r.scrollLeft + r.clientWidth >= r.scrollWidth - 6);
  }
  document.querySelectorAll(".chips").forEach(function (r) {
    r.addEventListener("scroll", function () { fades(r); }, { passive: true });
    fades(r);
  });
  window.addEventListener("resize", function () { chipRows.forEach(fades); });
  ["touchstart", "wheel", "keydown"].forEach(function (ev) {
    window.addEventListener(ev, function () { userTouched = Date.now(); }, { passive: true });
  });

  // ---- ricerca
  function norm(s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function filter() {
    var term = norm(q.value.trim());
    var any = false;
    document.querySelectorAll(".cat").forEach(function (cat) {
      var shown = 0;
      cat.querySelectorAll(".dishes li").forEach(function (li) {
        var match = !term || norm(li.textContent).indexOf(term) !== -1 || norm(cat.querySelector("h2").textContent).indexOf(term) !== -1;
        li.hidden = !match;
        if (match) shown++;
      });
      cat.hidden = shown === 0;
      var strip = cat.querySelector(".cat-strip");
      if (strip) strip.hidden = !!term;
      if (shown) any = true;
    });
    bar.hidden = !!term;
    if (term) {
      groups.giapponese.hidden = false; groups.cinese.hidden = false;
    } else {
      setTradition(current, { keepHash: true });
    }
    syncBarVar();
    empty.hidden = any || !term;
    if (fab) fab.hidden = !!term || window.scrollY < 500 || window.innerWidth >= 900;
  }
  var timer;
  q.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(filter, 120); });

  // ---- pulsante lente (telefono)
  if (fab) {
    fab.addEventListener("click", function () {
      q.scrollIntoView({ block: "center" });
      setTimeout(function () { q.focus({ preventScroll: true }); }, 150);
    });
  }

  // ---- scroll
  var tick = false;
  window.addEventListener("scroll", function () {
    if (tick) return;
    tick = true;
    requestAnimationFrame(function () {
      spy();
      if (fab) fab.hidden = !(window.innerWidth < 760 && window.scrollY > 500 && !q.value);
      tick = false;
    });
  }, { passive: true });
  window.addEventListener("resize", function () { syncBarVar(); spy(true); });

  // ---- link diretti (menu.html#nigiri, #cinese, ...)
  function fromHash() {
    var id = decodeURIComponent(location.hash.replace("#", ""));
    if (!id) { setTradition("giapponese", { keepHash: true }); return; }
    if (groups[id]) { setTradition(id, { keepHash: true }); return; }
    var el = document.getElementById(id);
    var g = el && el.dataset.group;
    if (g) {
      setTradition(g, { keepHash: true });
      requestAnimationFrame(function () { jumpTo(id); });
    } else {
      setTradition("giapponese", { keepHash: true });
    }
  }
  window.addEventListener("hashchange", function () { if (!q.value && Date.now() > lockUntil) fromHash(); });
  fromHash();
  syncBarVar();
})();
