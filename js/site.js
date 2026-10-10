(function () {
  "use strict";
  var TZ = "Europe/Rome";
  var SLOTS = [[12 * 60, 14 * 60 + 30], [19 * 60, 23 * 60]]; // pranzo, cena (minuti)
  var DAYS = ["domenica", "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"];

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function hm(m) { return pad(Math.floor(m / 60)) + ":" + pad(m % 60); }

  // giorno della settimana (0 = domenica) e minuti, nell'ora di Roma
  function nowRome() {
    var p = new Intl.DateTimeFormat("en-GB", { timeZone: TZ, weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(new Date());
    var o = {};
    p.forEach(function (x) { o[x.type] = x.value; });
    var map = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
    return { dow: map[o.weekday], min: (parseInt(o.hour, 10) % 24) * 60 + parseInt(o.minute, 10) };
  }

  // stato di apertura: { open: bool, text: string }
  function statusAt(dow, min) {
    if (dow !== 1) {
      for (var i = 0; i < SLOTS.length; i++) {
        if (min >= SLOTS[i][0] && min < SLOTS[i][1]) return { open: true, text: "Aperto ora · fino alle " + hm(SLOTS[i][1]) };
      }
      for (var j = 0; j < SLOTS.length; j++) {
        if (min < SLOTS[j][0]) return { open: false, text: "Chiuso ora · riapre oggi alle " + hm(SLOTS[j][0]) };
      }
    }
    // prossimo giorno di apertura
    var next = (dow + 1) % 7;
    if (next === 1) next = 2;
    var when = next === (dow + 1) % 7 ? "domani" : DAYS[next];
    return { open: false, text: "Chiuso ora · riapre " + when + " alle " + hm(SLOTS[0][0]) };
  }

  window.DongHours = { SLOTS: SLOTS, DAYS: DAYS, hm: hm, nowRome: nowRome, statusAt: statusAt };

  // ---- stato apertura nell'intestazione della pagina
  var st = document.getElementById("status");
  if (st) {
    try {
      var n = nowRome(), s = statusAt(n.dow, n.min);
      st.dataset.state = s.open ? "open" : "closed";
      st.textContent = s.text;
    } catch (e) { /* resta il testo statico */ }
  }

  // ---- intestazione: sfondo pieno dopo lo scroll
  var header = document.querySelector(".site-header");
  function onScroll() { header.classList.toggle("is-solid", window.scrollY > 40); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // ---- menu mobile
  var btn = document.querySelector(".menu-btn");
  var mnav = document.getElementById("mnav");
  function setNav(open) {
    header.classList.toggle("is-open", open);
    mnav.classList.toggle("is-open", open);
    btn.setAttribute("aria-expanded", String(open));
    btn.setAttribute("aria-label", open ? "Chiudi il menu di navigazione" : "Apri il menu di navigazione");
    document.body.style.overflow = open ? "hidden" : "";
  }
  btn.addEventListener("click", function () { setNav(!mnav.classList.contains("is-open")); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setNav(false); });
  window.addEventListener("resize", function () { if (window.innerWidth >= 900) setNav(false); });

  // ---- il disco yin-yang gira con lo scroll
  var yy = document.getElementById("yy");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (yy && !reduce) {
    var ticking = false;
    var upd = function () {
      var r = yy.parentElement.getBoundingClientRect();
      var prog = (window.innerHeight - r.top) / (window.innerHeight + r.height);
      yy.style.setProperty("--rot", Math.round(prog * 540) + "deg");
      ticking = false;
    };
    window.addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(upd); } }, { passive: true });
    upd();
  }

  // ---- rivelazione morbida delle sezioni
  var rv = document.querySelectorAll(".rv");
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    rv.forEach(function (el) { io.observe(el); });
  } else {
    rv.forEach(function (el) { el.classList.add("in"); });
  }
})();
