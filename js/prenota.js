(function(){
  "use strict";
  // Numero WhatsApp del ristorante: SEGNAPOSTO, da sostituire con quello reale (formato internazionale, senza + né spazi).
  var WA_NUMBER = "390516255139";
  var $ = function(s){ return document.querySelector(s); };
  var SHIFTS = { pranzo: { label: "Pranzo", sub: "12:00 – 14:30", from: 720, to: 840 }, cena: { label: "Cena", sub: "19:00 – 23:00", from: 1140, to: 1350 } };
  var MESI = ["gen","feb","mar","apr","mag","giu","lug","ago","set","ott","nov","dic"], GG = ["dom","lun","mar","mer","gio","ven","sab"], GGL = ["domenica","lunedì","martedì","mercoledì","giovedì","venerdì","sabato"];
  var st = { day: null, shift: null, time: null, n: 2 };
  var days = $("#days"), turni = $("#turni"), ore = $("#ore"), sum = $("#sum"), send = $("#send");
  var now = window.Dong ? window.Dong.rome() : { d: new Date().getDay(), m: 0 };
  var hm = function(m){ return Math.floor(m / 60) + ":" + (m % 60 ? "30" : "00"); };
  function btn(html, pressed, dis, fn){ var b = document.createElement("button"); b.type = "button"; b.className = "opt"; b.innerHTML = html; b.setAttribute("aria-pressed", String(!!pressed)); b.disabled = !!dis; b.addEventListener("click", fn); return b; }
  function today(){ var t = new Date(), s = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Rome" }).format(t).split("-"); return new Date(+s[0], +s[1] - 1, +s[2]); }
  function renderDays(){
    days.innerHTML = ""; var t0 = today();
    for (var i = 0; i < 21; i++) {
      var d = new Date(t0.getFullYear(), t0.getMonth(), t0.getDate() + i), wd = d.getDay(), closed = wd === 1;
      var lab = i === 0 ? "oggi" : i === 1 ? "domani" : GG[wd];
      (function(d, closed){ days.appendChild(btn("<small>" + lab + "</small>" + d.getDate() + " " + MESI[d.getMonth()], st.day && +st.day === +d, closed, function(){ st.day = d; st.shift = null; st.time = null; draw(); })); })(d, closed);
    }
  }
  function renderShifts(){
    turni.innerHTML = ""; $("#fs-turno").disabled = !st.day;
    if (!st.day) return;
    var isToday = +st.day === +today();
    Object.keys(SHIFTS).forEach(function(k){
      var s = SHIFTS[k], past = isToday && now.m >= s.to + 30;
      turni.appendChild(btn("<small>" + s.sub + "</small>" + s.label, st.shift === k, past, function(){ st.shift = k; st.time = null; draw(); }));
    });
  }
  function renderTimes(){
    ore.innerHTML = ""; $("#fs-ora").disabled = !st.shift;
    if (!st.shift) { ore.innerHTML = '<span class="hint">Scegli prima giorno e turno.</span>'; return; }
    var s = SHIFTS[st.shift], isToday = +st.day === +today();
    for (var m = s.from; m <= s.to; m += 30) {
      (function(m){ ore.appendChild(btn(hm(m), st.time === m, isToday && m <= now.m + 30, function(){ st.time = m; draw(); })); })(m);
    }
  }
  function summary(){
    if (!st.day || !st.shift || st.time == null) return "Scegli giorno, turno e orario.";
    return "Tavolo per " + st.n + (st.n === 1 ? " persona" : " persone") + ", " + GGL[st.day.getDay()] + " " + st.day.getDate() + " " + MESI[st.day.getMonth()] + " alle " + hm(st.time) + ".";
  }
  function draw(){
    renderDays(); renderShifts(); renderTimes();
    $("#n").textContent = st.n; sum.textContent = summary();
    send.disabled = !(st.day && st.shift && st.time != null && $("#nome").value.trim());
    var sel = days.querySelector('[aria-pressed="true"]'); if (sel && !draw.s) { draw.s = 1; }
  }
  $("#minus").addEventListener("click", function(){ st.n = Math.max(1, st.n - 1); draw(); });
  $("#plus").addEventListener("click", function(){ st.n = Math.min(12, st.n + 1); draw(); });
  $("#nome").addEventListener("input", draw);
  $("#bform").addEventListener("submit", function(e){
    e.preventDefault(); if (send.disabled) return;
    var msg = "Buongiorno, vorrei prenotare un tavolo per " + st.n + (st.n === 1 ? " persona" : " persone") + " per " + GGL[st.day.getDay()] + " " + st.day.getDate() + " " + MESI[st.day.getMonth()] + " alle " + hm(st.time) + ". A nome " + $("#nome").value.trim() + ". Grazie!";
    window.open("https://wa.me/" + WA_NUMBER + "?text=" + encodeURIComponent(msg), "_blank", "noopener");
  });
  draw();
})();
