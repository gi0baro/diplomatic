/* Floating panels over the board: clamping, dragging, resizing, placement.
 *
 * Extracted from the mockup (docs/design/template.html, "floating panels"), with the mock state taken out:
 * positions and sizes are passed in and handed back through callbacks, the caller keeps them (for the session).
 * Positions are [left, top] in px relative to the container (the panel's offset parent by default).
 *
 * One global: Floating.
 */
(function (global) {
  'use strict';

  function containerOf(el) {
    return el.offsetParent || el.parentElement || document.body;
  }

  // [x, y] kept inside the container, margin px from every edge
  function clamp(el, pos, container, margin) {
    if (margin === undefined) margin = 4;
    container = container || containerOf(el);
    var maxX = container.clientWidth - el.offsetWidth - margin;
    var maxY = container.clientHeight - el.offsetHeight - margin;
    return [Math.max(margin, Math.min(maxX, pos[0])), Math.max(margin, Math.min(maxY, pos[1]))];
  }

  function moveTo(el, pos) {
    el.style.left = pos[0] + 'px';
    el.style.top = pos[1] + 'px';
  }

  // pointer drag with capture on the handle; cleans up on up and cancel
  function track(handle, e, move) {
    var done = function () {
      handle.removeEventListener('pointermove', move);
      handle.removeEventListener('pointerup', done);
      handle.removeEventListener('pointercancel', done);
      if (handle.hasPointerCapture && handle.hasPointerCapture(e.pointerId)) handle.releasePointerCapture(e.pointerId);
    };
    handle.setPointerCapture(e.pointerId);
    handle.addEventListener('pointermove', move);
    handle.addEventListener('pointerup', done);
    handle.addEventListener('pointercancel', done);
    e.preventDefault();
  }

  function handlesOf(el, selector) {
    if (!selector) return [el];
    var list = Array.prototype.slice.call(el.querySelectorAll(selector));
    if (el.matches && el.matches(selector)) list.unshift(el);
    return list;
  }

  /* Drag el by its handles (selector, inside el). onMove([x, y]) receives the clamped position; without it
   * the position is applied directly. Presses on buttons and form fields are not drags. */
  function draggable(el, handleSelector, onMove) {
    handlesOf(el, handleSelector).forEach(function (h) {
      h.addEventListener('pointerdown', function (e) {
        if (e.button !== 0 || e.target.closest('button, input, textarea, select, a')) return;
        var container = containerOf(el);
        var r = el.getBoundingClientRect(), dx = e.clientX - r.left, dy = e.clientY - r.top;
        track(h, e, function (ev) {
          var br = container.getBoundingClientRect();
          var pos = clamp(el, [ev.clientX - br.left - dx, ev.clientY - br.top - dy], container);
          if (onMove) onMove(pos); else moveTo(el, pos);
        });
      });
    });
  }

  /* Resize el from its top edge (n), right edge (e) and top-right corner (ne); the bottom-left corner stays
   * put. handles: { n, e, ne } selectors inside el; limits: { minW, minH }.
   * onResize([w, h], [x, y]) receives the new size and position; without it they are applied directly. */
  function resizable(el, handles, limits, onResize) {
    handles = handles || {};
    limits = Object.assign({ minW: 200, minH: 120 }, limits || {});
    Object.keys(handles).forEach(function (dir) {
      if (!handles[dir]) return;
      handlesOf(el, handles[dir]).forEach(function (h) {
        h.addEventListener('pointerdown', function (e) {
          if (e.button !== 0) return;
          var container = containerOf(el);
          var br = container.getBoundingClientRect(), r = el.getBoundingClientRect();
          var x0 = e.clientX, y0 = e.clientY, left = r.left - br.left, bottom = r.bottom - br.top, w0 = r.width, h0 = r.height;
          track(h, e, function (ev) {
            var w = dir.indexOf('e') >= 0
              ? Math.max(limits.minW, Math.min(container.clientWidth - left - 4, w0 + ev.clientX - x0)) : w0;
            var hh = dir.indexOf('n') >= 0
              ? Math.max(limits.minH, Math.min(bottom - 4, h0 - (ev.clientY - y0))) : h0;
            var size = [w, hh], pos = [left, bottom - hh];
            if (onResize) onResize(size, pos);
            else { el.style.width = w + 'px'; el.style.height = hh + 'px'; moveTo(el, pos); }
          });
        });
      });
    });
  }

  /* Apply a remembered state ({ pos, size }, either may be missing) or the defaults ({ pos, size }; pos may be
   * a function (el, container) -> [x, y], evaluated after sizing). Size is capped to the container, position
   * clamped into it. Returns the position applied. */
  function place(el, state, container, defaults) {
    state = state || {};
    defaults = defaults || {};
    container = container || containerOf(el);
    var size = state.size || defaults.size;
    if (size) {
      el.style.width = Math.min(size[0], container.clientWidth - 8) + 'px';
      el.style.height = Math.min(size[1], container.clientHeight - 8) + 'px';
    }
    var pos = state.pos;
    if (!pos) pos = typeof defaults.pos === 'function' ? defaults.pos(el, container) : defaults.pos;
    pos = clamp(el, pos || [4, 4], container);
    moveTo(el, pos);
    return pos;
  }

  global.Floating = { clamp: clamp, draggable: draggable, resizable: resizable, place: place };
})(window);
