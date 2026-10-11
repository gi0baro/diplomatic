/* Zoom and pan on an SVG's viewBox, plus the per-zoom relayout of screen-constant glyphs.
 *
 * Extracted from the mockup (docs/design/template.html, "zoom & pan on the viewBox" and `relayout`).
 * The map size is read from the svg's own viewBox attribute. Min zoom 1x (the whole map), max opts.maxZoom,
 * the view clamped to the map; wheel zooms at the cursor, drag pans.
 *
 * relayout() writes on the svg, as CSS custom properties:
 *   --u  = map units per screen px right now (1 / ppu);
 *   --kf = opts.pxPerUnitRef x --u   (font groups: one reference unit at the 1440x900 reference);
 *   --kg = opts.glyphScale x --kf    (glyph groups: units, rings, heads, diamonds...).
 * opts.onChange(zoomLevel) runs after every change (zoom, pan, reset, resize), zoomLevel = map width / view width.
 *
 * A drag never turns into a click: the click that ends a drag is swallowed (capture phase), and the pointer is
 * only captured once the drag has started, so plain clicks keep their real target.
 *
 * One global: ViewBox.
 */
(function (global) {
  'use strict';

  var DRAG_THRESHOLD = 3;   // px before a press becomes a pan

  function attach(svg, opts) {
    opts = Object.assign({ maxZoom: 5, pxPerUnitRef: 0.8215, glyphScale: 1, onChange: null }, opts || {});
    var base = (svg.getAttribute('viewBox') || '0 0 1300 1000').trim().split(/[\s,]+/).map(Number);
    var X0 = base[0], Y0 = base[1], W = base[2], H = base[3];
    var vb = base.slice();
    var pan = null, swallowClick = false;

    var ctl = {
      svg: svg,
      kg: 1,
      width: W,
      height: H,
      get viewBox() { return vb.slice(); },
      get zoomLevel() { return W / vb[2]; },

      set: function (box) {
        var w = Math.min(W, Math.max(W / opts.maxZoom, box[2]));
        var h = w * H / W;
        var x = Math.min(X0 + W - w, Math.max(X0, box[0]));
        var y = Math.min(Y0 + H - h, Math.max(Y0, box[1]));
        vb = [x, y, w, h];
        svg.setAttribute('viewBox', vb.map(function (v) { return +v.toFixed(3); }).join(' '));
        changed();
      },

      zoom: function (k, cx, cy) {
        if (cx === undefined) cx = vb[0] + vb[2] / 2;
        if (cy === undefined) cy = vb[1] + vb[3] / 2;
        var w = Math.min(W, Math.max(W / opts.maxZoom, vb[2] * k));
        k = w / vb[2];
        ctl.set([cx - (cx - vb[0]) * k, cy - (cy - vb[1]) * k, w]);
      },

      zoomIn: function () { ctl.zoom(1 / 1.3); },
      zoomOut: function () { ctl.zoom(1.3); },
      reset: function () { ctl.set([X0, Y0, W]); },

      toSvg: function (clientX, clientY) {
        var m = svg.getScreenCTM();
        if (!m) return { x: clientX, y: clientY };
        return new DOMPoint(clientX, clientY).matrixTransform(m.inverse());
      },

      relayout: function () {
        var m = svg.getScreenCTM();
        var ppu = m ? Math.hypot(m.a, m.b) : 0;     // screen px per map unit right now
        if (!ppu) return ctl.kg;                     // not laid out (hidden): keep the last values
        var u = 1 / ppu, kf = opts.pxPerUnitRef * u, kg = opts.glyphScale * kf;
        svg.style.setProperty('--u', u.toFixed(4));
        svg.style.setProperty('--kf', kf.toFixed(4));
        svg.style.setProperty('--kg', kg.toFixed(4));
        ctl.kg = kg;
        return kg;
      }
    };

    function changed() {
      ctl.relayout();
      if (opts.onChange) opts.onChange(ctl.zoomLevel);
    }

    svg.addEventListener('wheel', function (e) {
      e.preventDefault();
      var m = ctl.toSvg(e.clientX, e.clientY);
      ctl.zoom(e.deltaY > 0 ? 1.15 : 1 / 1.15, m.x, m.y);
    }, { passive: false });

    svg.addEventListener('pointerdown', function (e) {
      if (e.button !== 0) return;
      swallowClick = false;
      pan = { id: e.pointerId, x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, active: false };
    });

    svg.addEventListener('pointermove', function (e) {
      if (!pan || e.pointerId !== pan.id) return;
      if (!pan.active) {
        if (Math.hypot(e.clientX - pan.x0, e.clientY - pan.y0) < DRAG_THRESHOLD) return;
        pan.active = true;
        try { svg.setPointerCapture(e.pointerId); } catch (err) { /* pointer already gone */ }
        svg.classList.add('dragging');
      }
      var m = svg.getScreenCTM(), s = m ? Math.hypot(m.a, m.b) : 1;
      ctl.set([vb[0] - (e.clientX - pan.x) / s, vb[1] - (e.clientY - pan.y) / s, vb[2]]);
      pan.x = e.clientX;
      pan.y = e.clientY;
    });

    function endPan(e) {
      if (!pan || e.pointerId !== pan.id) return;
      if (pan.active) {
        swallowClick = e.type === 'pointerup';
        if (svg.hasPointerCapture && svg.hasPointerCapture(e.pointerId)) svg.releasePointerCapture(e.pointerId);
        svg.classList.remove('dragging');
      }
      pan = null;
    }
    svg.addEventListener('pointerup', endPan);
    svg.addEventListener('pointercancel', endPan);
    svg.addEventListener('lostpointercapture', function () {
      if (pan && pan.active) { svg.classList.remove('dragging'); pan = null; }
    });

    // the click that ends a drag is not a click on a province
    svg.addEventListener('click', function (e) {
      if (!swallowClick) return;
      swallowClick = false;
      e.stopPropagation();
      e.preventDefault();
    }, true);

    // the board's box can change without a window resize (side panels): follow the svg itself
    if (typeof ResizeObserver === 'function') {
      new ResizeObserver(changed).observe(svg);
    } else {
      global.addEventListener('resize', changed);
    }

    return ctl;
  }

  global.ViewBox = { attach: attach };
})(window);
