(function () {
  var stage = document.querySelector('.stage');
  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var prev = document.querySelector('.controls .prev');
  var next = document.querySelector('.controls .next');
  var count = document.querySelector('.controls .count');
  var bar = document.querySelector('.progress span');
  var total = slides.length;
  var cur = 0;

  slides.forEach(function (s, i) {
    var pg = s.querySelector('.pg');
    if (pg) pg.textContent = (i + 1) + ' / ' + total;
    s.setAttribute('aria-label', '第 ' + (i + 1) + ' 頁，共 ' + total + ' 頁');
  });

  function fit() {
    var w = window.innerWidth, h = window.innerHeight - 56;
    var k = Math.min(w / 1280, h / 720);
    stage.style.transform = 'scale(' + k + ')';
  }

  function show(i) {
    cur = Math.max(0, Math.min(total - 1, i));
    slides.forEach(function (s, j) { s.classList.toggle('active', j === cur); });
    count.textContent = (cur + 1) + ' / ' + total;
    bar.style.width = ((cur + 1) / total * 100) + '%';
    prev.disabled = cur === 0;
    next.disabled = cur === total - 1;
    var name = 'slide-' + (cur + 1);
    if (location.hash !== '#' + name) {
      try { history.replaceState(null, '', '#' + name); } catch (e) { /* 部分環境不允許 */ }
    }
  }
  window.__show = show;  // 給檢查程式使用

  function fromHash() {
    var m = /^#slide-(\d+)$/.exec(location.hash || '');
    return m ? parseInt(m[1], 10) - 1 : 0;
  }

  prev.addEventListener('click', function () { show(cur - 1); });
  next.addEventListener('click', function () { show(cur + 1); });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'ArrowRight' || ev.key === 'PageDown' || ev.key === ' ') { ev.preventDefault(); show(cur + 1); }
    if (ev.key === 'ArrowLeft' || ev.key === 'PageUp') { ev.preventDefault(); show(cur - 1); }
    if (ev.key === 'Home') show(0);
    if (ev.key === 'End') show(total - 1);
  });
  var x0 = null;
  document.addEventListener('touchstart', function (ev) { x0 = ev.touches[0].clientX; }, { passive: true });
  document.addEventListener('touchend', function (ev) {
    if (x0 === null) return;
    var dx = ev.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) show(cur + (dx < 0 ? 1 : -1));
    x0 = null;
  });
  window.addEventListener('hashchange', function () { show(fromHash()); });
  window.addEventListener('resize', fit);
  fit();
  show(fromHash());
})();
