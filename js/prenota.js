(function () {
  "use strict";
  var H = window.DongHours;
  var d = document.getElementById("d");
  var out = document.getElementById("verdict");
  var radios = document.querySelectorAll('input[name="t"]');
  if (!d || !H) return;

  // oggi, nell'ora di Roma, come valore minimo del selettore
  function todayISO() {
    var p = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Rome", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    return p;
  }
  d.min = todayISO();
  d.value = d.min;

  function turno() {
    for (var i = 0; i < radios.length; i++) if (radios[i].checked) return radios[i].value;
    return "pranzo";
  }

  function update() {
    if (!d.value) { out.removeAttribute("data-ok"); out.textContent = "Scegli un giorno."; return; }
    var parts = d.value.split("-").map(Number);
    var date = new Date(parts[0], parts[1] - 1, parts[2]);
    var dow = date.getDay();
    var nome = H.DAYS[dow];
    var t = turno();
    var slot = H.SLOTS[t === "pranzo" ? 0 : 1];
    if (dow === 1) {
      out.dataset.ok = "no";
      out.innerHTML = "Il <strong>lunedì siamo chiusi</strong>. Scegli un altro giorno: da martedì a domenica ti aspettiamo.";
      return;
    }
    out.dataset.ok = "yes";
    out.innerHTML = "<strong>Siamo aperti</strong> " + (t === "pranzo" ? "a pranzo" : "a cena") + " di " + nome +
      ", dalle " + H.hm(slot[0]) + " alle " + H.hm(slot[1]) + ". Chiamaci dalle 10:00 alle 18:30 per riservare il tavolo.";
  }

  d.addEventListener("input", update);
  d.addEventListener("change", update);
  radios.forEach(function (r) { r.addEventListener("change", update); });
  update();
})();
