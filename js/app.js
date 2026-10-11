(function(){
  "use strict";
  var $ = function(s, r){ return (r || document).querySelector(s); };
  // orari reali: martedì–domenica 12:00–14:30 e 19:00–23:00, lunedì chiuso (ora di Roma)
  var SLOTS = [[720, 870], [1140, 1380]], DAYS = ["domenica","lunedì","martedì","mercoledì","giovedì","venerdì","sabato"];
  function rome(){
    try {
      var p = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Rome", weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(new Date()), o = {};
      p.forEach(function(x){ o[x.type] = x.value; });
      var wd = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }[o.weekday];
      return { d: wd, m: (+o.hour % 24) * 60 + +o.minute };
    } catch (e) { var n = new Date(); return { d: n.getDay(), m: n.getHours() * 60 + n.getMinutes() }; }
  }
  var hm = function(m){ return Math.floor(m / 60) + ":" + (m % 60 < 10 ? "0" : "") + (m % 60); };
  function status(){
    var t = rome(), el = $("#status"); if (!el) return;
    var open = t.d !== 1 && SLOTS.find(function(s){ return t.m >= s[0] && t.m < s[1]; });
    var txt;
    if (open) txt = "Aperto ora · fino alle " + hm(open[1]);
    else {
      var next = null;
      for (var k = 0; k < 7 && !next; k++) {
        var d = (t.d + k) % 7; if (d === 1) continue;
        var s = SLOTS.find(function(s){ return k > 0 || s[0] > t.m; });
        if (s) next = { k: k, d: d, m: s[0] };
      }
      txt = "Chiuso · riapre " + (next.k === 0 ? "oggi" : next.k === 1 ? "domani" : DAYS[next.d]) + " alle " + hm(next.m);
    }
    el.classList.toggle("off", !open); el.lastElementChild.textContent = txt;
    var row = document.querySelector('#hours tr[data-d="' + (t.d === 1 ? 1 : 2) + '"]'); if (row) row.classList.add("today");
  }
  status(); setInterval(status, 60000);
  // barra in alto: si scurisce scorrendo
  var top = $("#top"), onS = function(){ top.classList.toggle("solid", scrollY > 40); }; onS(); addEventListener("scroll", onS, { passive: true });
  // comparsa morbida
  var rv = document.querySelectorAll(".rv");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function(es){ es.forEach(function(e){ if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }); }, { rootMargin: "0px 0px -8% 0px" });
    rv.forEach(function(n){ io.observe(n); });
  } else rv.forEach(function(n){ n.classList.add("in"); });
  // anteprima: le altre pagine arrivano nel passo successivo
  var toast = function(t){ var el = $("#toast"); el.textContent = t; el.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(function(){ el.hidden = true; }, 2200); };
  if (/^https:/.test(location.protocol) && !/ristorantedong\.it$/.test(location.hostname) && document.documentElement.hasAttribute("data-preview")) {
    document.addEventListener("click", function(e){ var a = e.target.closest("a[data-next]"); if (a) { e.preventDefault(); toast("Questa pagina arriva nel passo successivo"); } });
  }
})();
