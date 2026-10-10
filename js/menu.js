(function () {
  "use strict";
  var groups = { giapponese: document.getElementById("giapponese"), cinese: document.getElementById("cinese") };
  var tabs = document.querySelectorAll(".switch button");
  var chipRows = document.querySelectorAll(".chips");
  var q = document.getElementById("q");
  var empty = document.getElementById("empty");
  var bar = document.getElementById("menubar");
  var current = "giapponese";

  function setTradition(g, opts) {
    opts = opts || {};
    current = g;
    document.body.dataset.trad = g;
    tabs.forEach(function (t) { t.setAttribute("aria-selected", String(t.dataset.g === g)); });
    chipRows.forEach(function (r) { r.hidden = r.dataset.for !== g; });
    Object.keys(groups).forEach(function (k) { groups[k].hidden = k !== g; });
    document.querySelector('meta[name="theme-color"]').setAttribute("content", g === "cinese" ? "#b8180f" : "#130a09");
    if (opts.scroll) {
      var head = parseInt(getComputedStyle(document.documentElement).getPropertyValue("--header-h"), 10) || 68;
      var target = groups[g].getBoundingClientRect().top + window.scrollY - head - bar.offsetHeight - 8;
      window.scrollTo({ top: Math.max(0, target), behavior: "auto" });
    }
    spy();
    if (opts.keepHash !== true && history.replaceState) history.replaceState(null, "", "#" + g);
  }

  document.documentElement.style.scrollBehavior = "auto"; // salti diretti, senza scorrimento lungo
  tabs.forEach(function (t) {
    var go = function () { if (q.value) { q.value = ""; filter(); } setTradition(t.dataset.g, { scroll: true }); };
    t.addEventListener("click", go);
    if (window.fastTap) window.fastTap(t, go);
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
    empty.hidden = any || !term;
  }
  var timer;
  q.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(filter, 120); });

  // ---- categoria attiva mentre si scorre
  var links = {};
  document.querySelectorAll(".chips a").forEach(function (a) { links[a.dataset.cat] = a; });
  function spy() {
    var best = null, line = window.innerHeight * 0.35;
    document.querySelectorAll(".group:not([hidden]) .cat:not([hidden])").forEach(function (c) {
      var r = c.getBoundingClientRect();
      if (r.top <= line && r.bottom > line) best = c.id;
    });
    Object.keys(links).forEach(function (k) {
      var on = k === best;
      if (on) links[k].setAttribute("aria-current", "true"); else links[k].removeAttribute("aria-current");
      if (on && links[k].offsetParent && !q.value) {
        var row = links[k].parentElement;
        var x = links[k].offsetLeft - row.clientWidth / 2 + links[k].offsetWidth / 2;
        if (Math.abs(row.scrollLeft - x) > 8) row.scrollTo({ left: x, behavior: "smooth" });
      }
    });
  }
  // i filtri rispondono al primo tocco
  document.querySelectorAll(".chips a").forEach(function (a) {
    if (window.fastTap) window.fastTap(a, function () { location.hash = a.getAttribute("href"); });
  });

  // barra che si nasconde scorrendo verso il basso (solo telefono) e ricerca rapida
  var fab = document.getElementById("fab");
  var lastY = window.scrollY;
  function barState() {
    var y = window.scrollY, small = window.innerWidth < 760;
    if (small && !q.value) {
      if (y > lastY + 6 && y > 320) bar.classList.add("is-tucked");
      else if (y < lastY - 6 || y < 200) bar.classList.remove("is-tucked");
    } else bar.classList.remove("is-tucked");
    if (fab) fab.hidden = !(small && y > 500 && !q.value);
    lastY = y;
  }
  if (fab) {
    var goSearch = function () { q.scrollIntoView({ block: "center" }); setTimeout(function () { q.focus({ preventScroll: true }); }, 150); };
    fab.addEventListener("click", goSearch);
    if (window.fastTap) window.fastTap(fab, goSearch);
  }
  var tick = false;
  window.addEventListener("scroll", function () { if (!tick) { tick = true; requestAnimationFrame(function () { spy(); barState(); tick = false; }); } }, { passive: true });

  // ---- link diretti (menu.html#nigiri, #cinese, ...)
  function fromHash() {
    var id = decodeURIComponent(location.hash.replace("#", ""));
    if (!id) return setTradition("giapponese", { keepHash: true });
    if (groups[id]) return setTradition(id, { keepHash: true });
    var el = document.getElementById(id);
    var g = el && el.dataset.group;
    if (g) {
      setTradition(g, { keepHash: true });
      requestAnimationFrame(function () { el.scrollIntoView(); });
    } else {
      setTradition("giapponese", { keepHash: true });
    }
  }
  window.addEventListener("hashchange", function () { if (!q.value) fromHash(); });
  // le chips cambiano solo l'ancora: nessun salto brusco col tema
  fromHash();
})();
