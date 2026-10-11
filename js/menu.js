(function(){
  "use strict";
  var $ = function(s, r){ return (r || document).querySelector(s); }, $$ = function(s, r){ return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var bar = $("#mbar"), q = $("#q"), empty = $("#empty"), root = document.documentElement;
  var groups = { giapponese: $("#giapponese"), cinese: $("#cinese") }, tabs = $$(".switch button"), rows = $$(".chips");
  var cur = "giapponese", lock = 0;
  root.style.scrollBehavior = "auto";

  function offset(){ return bar.offsetHeight + 8; }
  function norm(s){ return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function setActive(id){
    var row = rows.filter(function(r){ return !r.hidden; })[0]; if (!row) return;
    $$("a", row).forEach(function(a){
      var on = a.dataset.cat === id; a.classList.toggle("on", on);
      if (on) { var l = a.offsetLeft - (row.clientWidth - a.offsetWidth) / 2; row.scrollTo({ left: Math.max(0, l), behavior: "auto" }); }
    });
  }
  function setGroup(g){
    cur = g;
    tabs.forEach(function(t){ t.setAttribute("aria-selected", String(t.dataset.g === g)); });
    rows.forEach(function(r){ r.hidden = r.dataset.for !== g; });
    Object.keys(groups).forEach(function(k){ groups[k].hidden = k !== g; });
  }
  function goTo(el){
    var y = el.getBoundingClientRect().top + scrollY - offset();
    window.scrollTo(0, Math.max(0, y));
  }
  // un solo tocco: salta subito alla categoria
  rows.forEach(function(r){ r.addEventListener("click", function(e){
    var a = e.target.closest("a[data-cat]"); if (!a) return; e.preventDefault();
    var el = document.getElementById(a.dataset.cat); if (!el) return;
    lock = Date.now() + 500; setActive(a.dataset.cat); goTo(el);
    if (history.replaceState) history.replaceState(null, "", "#" + a.dataset.cat);
  }); });
  tabs.forEach(function(t){ t.addEventListener("click", function(){
    if (t.dataset.g === cur) return;
    setGroup(t.dataset.g); lock = Date.now() + 500;
    var g = groups[cur], first = $(".mcat", g); goTo(g); setActive(first && first.id);
  }); });
  // la categoria evidenziata segue quello che stai guardando
  var tick = false;
  function spy(){
    tick = false; if (document.body.classList.contains("searching")) return;
    if (Date.now() < lock) { setTimeout(spy, lock - Date.now() + 30); return; }
    var y = offset() + 24, id = null;
    $$(".mcat", groups[cur]).forEach(function(s){ if (s.getBoundingClientRect().top <= y) id = s.id; });
    if (!id) { var f = $(".mcat", groups[cur]); id = f && f.id; }
    if (id) setActive(id);
  }
  addEventListener("scroll", function(){ if (!tick) { tick = true; requestAnimationFrame(spy); } }, { passive: true });
  // ricerca su tutto il menu
  q.addEventListener("input", function(){
    var v = norm(q.value.trim()), any = false;
    document.body.classList.toggle("searching", !!v);
    $$(".mcat").forEach(function(c){
      var n = 0;
      $$(".dl li", c).forEach(function(li){ var m = !v || li.dataset.s.indexOf(v) > -1; li.hidden = !m; if (m) n++; });
      c.hidden = !!v && n === 0; if (n) any = true;
    });
    $$(".mgroup").forEach(function(g){ g.hidden = v ? false : g.id !== cur; });
    empty.hidden = !v || any;
    if (!v) { lock = 0; requestAnimationFrame(spy); }
  });
  // apertura da link con #categoria
  var h = location.hash.slice(1), el = h && document.getElementById(h);
  if (el && el.classList.contains("mcat")) { var g = el.parentNode.id; setGroup(g); setTimeout(function(){ setActive(h); goTo(el); }, 60); }
  else setActive($(".mcat", groups[cur]).id);
})();
