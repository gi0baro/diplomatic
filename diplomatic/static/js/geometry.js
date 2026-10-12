/* Order geometry for the board: where a line starts and stops, where its head sits.
 *
 * Extracted from the mockup (docs/design/template.html, `layoutOrder`). Pure functions over points in map
 * units ([x, y] arrays); no DOM. Glyphs are screen-constant, so every distance below is a GAP value in glyph
 * units multiplied by `kg` (map units per glyph unit at the current zoom, from ViewBox.relayout()).
 *
 * One global: Geometry.
 */
(function (global) {
  'use strict';

  // distances in glyph units (x kg = map units): where lines stop around units and inside heads
  var GAP = { start: 15, startDis: 18, end: 14, head: 5, rhead: 14, knob: 5, oct: 20 };

  // the point at distance d from p towards q
  function along(p, q, d) {
    var dx = q[0] - p[0], dy = q[1] - p[1], L = Math.hypot(dx, dy) || 1;
    return [p[0] + dx / L * d, p[1] + dy / L * d];
  }

  // unit vector from p to q
  function dirOf(p, q) {
    var dx = q[0] - p[0], dy = q[1] - p[1], L = Math.hypot(dx, dy) || 1;
    return [dx / L, dy / L];
  }

  // the point at distance d from p, backwards along the unit vector u
  function back(p, u, d) {
    return [p[0] - u[0] * d, p[1] - u[1] * d];
  }

  function pt(p) {
    return p[0].toFixed(1) + ',' + p[1].toFixed(1);
  }

  // Catmull-Rom through the points (the convoy path through the convoying fleets), as cubic Beziers
  function catmull(points) {
    var P = [points[0]].concat(points, [points[points.length - 1]]);
    var d = 'M' + pt(P[1]);
    for (var i = 1; i < P.length - 2; i++) {
      var a = P[i - 1], b = P[i], c = P[i + 1], e = P[i + 2];
      d += ' C' + pt([b[0] + (c[0] - a[0]) / 6, b[1] + (c[1] - a[1]) / 6]) +
        ' ' + pt([c[0] - (e[0] - b[0]) / 6, c[1] - (e[1] - b[1]) / 6]) +
        ' ' + pt(c);
    }
    return d;
  }

  // quadratic curve from start to end, bent sideways by k (support orders)
  function curve(start, end, k) {
    if (k === undefined) k = 0.16;
    var ctrl = [(start[0] + end[0]) / 2 + (end[1] - start[1]) * k, (start[1] + end[1]) / 2 - (end[0] - start[0]) * k];
    return 'M' + pt(start) + 'Q' + pt(ctrl) + ' ' + pt(end);
  }

  function shifted(p, on, kg, disOffset) {
    return on ? [p[0] + disOffset[0] * kg, p[1] + disOffset[1] * kg] : p;
  }

  function headOf(tip, u) {
    return { x: tip[0], y: tip[1], angle: Math.atan2(u[1], u[0]) * 180 / Math.PI };
  }

  /* Path data and head placement of one order.
   *
   * geo: { t: 'm',  p: [from, ...via, to], d }   move / convoy (d: the moving unit is dislodged)
   *      { t: 'sm', s: supporter, m: midpoint of the supported move, d }
   *      { t: 'sh', s: supporter, e: supported unit, d }
   *      { t: 'r',  s: dislodged unit, e: destination, d }   (d defaults to 1: a retreat starts at a dislodged unit)
   * kg: map units per glyph unit; disOffset: the dislodged offset [x, y] in glyph units.
   * Returns { d: path data, head: { x, y, angle (degrees) } | null }.
   */
  function layout(geo, kg, disOffset) {
    var k = kg || 1, dis = disOffset || [0, 0], d, tip = null, u = null;
    if (geo.t === 'm') {
      var p = geo.p.slice();
      p[0] = shifted(p[0], !!geo.d, k, dis);
      var s = along(p[0], p[1], GAP.start * k);
      tip = along(p[p.length - 1], p[p.length - 2], GAP.end * k);
      u = dirOf(p.length > 2 ? p[p.length - 2] : s, tip);
      var end = back(tip, u, GAP.head * k);
      d = p.length > 2 ? catmull([s].concat(p.slice(1, -1), [end])) : 'M' + pt(s) + 'L' + pt(end);
    } else if (geo.t === 'sm') {
      var s0 = shifted(geo.s, !!geo.d, k, dis);
      d = curve(along(s0, geo.m, GAP.start * k), along(geo.m, s0, GAP.knob * k));
    } else if (geo.t === 'sh') {
      var h0 = shifted(geo.s, !!geo.d, k, dis);
      d = curve(along(h0, geo.e, GAP.start * k), along(geo.e, h0, GAP.oct * k));
    } else if (geo.t === 'r') {
      var on = geo.d === undefined ? true : !!geo.d;
      var r0 = shifted(geo.s, on, k, dis);
      var rs = along(r0, geo.e, (on ? GAP.startDis : GAP.start) * k);
      tip = along(geo.e, r0, GAP.end * k);
      u = dirOf(rs, tip);
      d = 'M' + pt(rs) + 'L' + pt(back(tip, u, GAP.rhead * k));
    } else {
      return { d: '', head: null };
    }
    return { d: d, head: tip ? headOf(tip, u) : null };
  }

  global.Geometry = {
    GAP: GAP,
    along: along,
    dirOf: dirOf,
    back: back,
    pt: pt,
    catmull: catmull,
    curve: curve,
    layout: layout
  };
})(window);
