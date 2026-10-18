// Countdowns outside the game page (lobby cards, dashboard): every [data-deadline] element, an ISO 8601 instant,
// shows the time left as `2d 4h`, `4h 12m` or `12m 05s`, and `due` once past. The game page's clock (#clock-box)
// is ticked by play.js and skipped here. Elements are collected on load, after every htmx swap and after an htmx
// history restore; one interval updates them all.
(function () {
  'use strict';

  var els = [];

  function format(ms) {
    if (ms <= 0) return 'due';
    var t = Math.floor(ms / 1000);
    var d = Math.floor(t / 86400), h = Math.floor(t / 3600) % 24, m = Math.floor(t / 60) % 60, s = t % 60;
    if (d) return d + 'd ' + h + 'h';
    if (h) return h + 'h ' + m + 'm';
    return m + 'm ' + (s < 10 ? '0' : '') + s + 's';
  }

  function tick() {
    var now = Date.now();
    els.forEach(function (el) {
      var at = Date.parse(el.dataset.deadline);
      if (!isNaN(at)) el.textContent = format(at - now);
    });
  }

  function collect() {
    els = Array.prototype.slice.call(document.querySelectorAll('[data-deadline]:not(#clock-box)'));
    tick();
  }

  document.addEventListener('DOMContentLoaded', function () {
    collect();
    document.body.addEventListener('htmx:afterSwap', collect);
    document.body.addEventListener('htmx:historyRestore', collect);
    setInterval(tick, 1000);
  });
})();
