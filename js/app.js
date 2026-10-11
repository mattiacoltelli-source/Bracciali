(function(){
  "use strict";
  var $ = function(s, r){ return (r || document).querySelector(s); };
  // orari reali: martedì–domenica 12:00–14:30 e 19:00–23:00, lunedì chiuso (ora di Roma)
  var SLOTS = [[720, 870], [1140, 1380]], DAYS = ["domenica","lunedì","martedì","mercoledì","giovedì","venerdì","sabato"];
  function rome(){
    try {
      var p = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Rome", weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(new Date()), o = {};
      p.forEach(function(x){ o[x.type] = x.value; });
      return { d: { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }[o.weekday], m: (+o.hour % 24) * 60 + +o.minute };
    } catch (e) { var n = new Date(); return { d: n.getDay(), m: n.getHours() * 60 + n.getMinutes() }; }
  }
  var hm = function(m){ return Math.floor(m / 60) + ":" + (m % 60 < 10 ? "0" : "") + (m % 60); };
  function status(){
    var t = rome(), el = $("#status"); if (!el) return;
    var open = t.d !== 1 && SLOTS.find(function(s){ return t.m >= s[0] && t.m < s[1]; }), txt;
    if (open) txt = "Aperto ora · fino alle " + hm(open[1]);
    else {
      var next = null;
      for (var k = 0; k < 8 && !next; k++) {
        var d = (t.d + k) % 7; if (d === 1) continue;
        var s = SLOTS.find(function(s){ return k > 0 || s[0] > t.m; });
        if (s) next = { k: k, d: d, m: s[0] };
      }
      txt = "Chiuso · riapre " + (next.k === 0 ? "oggi" : next.k === 1 ? "domani" : DAYS[next.d]) + " alle " + hm(next.m);
    }
    el.classList.toggle("off", !open); el.lastElementChild.textContent = txt;
    var want = t.d === 1 ? "1" : t.m < 1000 ? "2" : "2b";
    document.querySelectorAll("#hours tr").forEach(function(r){ r.classList.toggle("today", r.getAttribute("data-d") === want || (want === "2b" && !document.querySelector("#hours tr[data-d=\"2b\"]") && r.getAttribute("data-d") === "2")); });
  }
  status(); setInterval(status, 60000);
  var top = $("#top"), onS = function(){ top.classList.toggle("solid", scrollY > 40); }; onS(); addEventListener("scroll", onS, { passive: true });
  var rv = document.querySelectorAll(".rv");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function(es){ es.forEach(function(e){ if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }); }, { rootMargin: "0px 0px -8% 0px" });
    rv.forEach(function(n){ io.observe(n); });
  } else rv.forEach(function(n){ n.classList.add("in"); });
  window.Dong = { rome: rome };
})();
