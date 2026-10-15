// The game page: the phase bar, phase navigation and the engine's boot. Order entry, the sidebar, the popover,
// zoom and the keys are static/js/board-ui.js (Alpine components on the engine's DOM events).
// Loaded after the engine bundle (gapp, Steps); runs on DOMContentLoaded, once games/play.haml has registered
// the strings and the routes (gapp.net.routes) and set the page constants:
//   PLAYER        the player's country, or null
//   PRE, ACTIVE, OVER   game stage
//   PLAYER_ACTIVE the player has orders in the open phase
//   PLAYER_READY  the initial value of gapp.game.ready (the engine owns it from there: setReady, game:players)
//   FULL          the player gets the virtual "next" step (their pending orders) on top of the phases
(function () {
  'use strict';

  var TYPE_CLASS = { diplomacy: 'text-signal/80', retreats: 'text-warn', builds: 'text-ok', pre: 'text-fog-400' };

  function getJSON(url) {
    return fetch(url, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
      .then(function (r) {
        if (!r.ok) throw new Error(r.status + ' ' + url);
        return r.json();
      });
  }

  function $(s) { return document.querySelector(s); }

  document.addEventListener('DOMContentLoaded', function () {
    var PLAYER = window.PLAYER;
    var PRE = window.PRE;
    var ACTIVE = window.ACTIVE;
    var OVER = window.OVER;
    var PLAYER_ACTIVE = window.PLAYER_ACTIVE;
    var PLAYER_READY = window.PLAYER_READY;
    var FULL = window.FULL;
    var TYPES = Steps.TYPES;
    var routes = gapp.net.routes;
    var svg = document.getElementById('map');
    var shaper = new Steps(gapp, getJSON);

    var steps = [];      // raw steps for ux.stepChange: pre-game, every phase, the virtual next step
    var view = 0;        // index of the displayed step
    var current = 0;     // index of the step of the phase being played (>= current is CURRENT)
    var busy = false;
    var moving = null;
    var refreshing = false;
    var mapData = null;
    var clockTimer = null;

    // ---- phase bar ----
    // a step draws the orders of the phase before it, so it is named after that phase; the pre-game step is the
    // page's own (no year), the first phase has none before it (its own season and year, as pre-game), "next" is
    // the open phase itself
    function phaseName(d) {
      var season = d.type === PHASE_TYPES.builds ? T.get('season.winter') : SEASONS.translate(d.season);
      return season + ' ' + d.year;
    }

    function phaseLabel(d) {
      return { name: phaseName(d), type: PHASE_TYPES.translate(d.type), kind: TYPES[d.type] };
    }

    function label(step) {
      var pregame = T.get('phase_type.pregame');
      if (step.type === 'pre') return { name: '\u2014', type: pregame, kind: 'pre' };
      var prev = step.type === 'next' ? null : step.prev();
      if (prev && prev.type === 'pre') return { name: phaseName(step.data || {}), type: pregame, kind: 'pre' };
      return phaseLabel((prev || step).data || {});
    }

    function renderBar() {
      var step = steps[view];
      if (!step) return;
      var past = view < current;
      var l = label(step);
      var type = $('#phase-type');
      document.body.classList.toggle('past', past);
      $('#phase-name').textContent = l.name;
      type.textContent = l.type || '\u00a0';
      Object.keys(TYPE_CLASS).forEach(function (k) { type.classList.remove(TYPE_CLASS[k]); });
      type.classList.add(TYPE_CLASS[l.kind] || 'text-fog-400');
      var next = step.type === 'next';
      $('#badge-cur').classList.toggle('hidden', past || next);
      $('#badge-next').classList.toggle('hidden', !next);
      $('#badge-past').classList.toggle('hidden', !past);
      $('#behind').textContent = String(current - view);
      document.querySelectorAll('button[data-nav="first"], button[data-nav="prev"]').forEach(function (b) {
        b.disabled = view === 0;
      });
      document.querySelectorAll('button[data-nav="next"], button[data-nav="last"]').forEach(function (b) {
        b.disabled = view === steps.length - 1;
      });
    }

    // what the engine passes on with game:step (the sidebar's view of the displayed step)
    function info(i) {
      var s = steps[i];
      // a step shows the board as its phase opened: resolved when the previous phase was processed
      var resolvedAt = s && s.type !== 'pre' && s.type !== 'next' && s.data ? s.data.created_at : null;
      return { index: i, current: current, count: steps.length, label: label(s), resolvedAt: resolvedAt || null };
    }

    // ---- navigation (the Vue board's controlTime: every phase is known, orders load on demand) ----
    function go(where) {
      if (!gapp.launched || busy || refreshing || !steps.length) return;
      var targets = { first: 0, prev: view - 1, next: view + 1, last: steps.length - 1 };
      var i = targets[where];
      if (i === undefined) return;
      i = Math.max(0, Math.min(steps.length - 1, i));
      if (i === view) return;
      busy = true;
      moving = shaper.ensureOrders(steps[i])
        .then(function () {
          view = i;
          gapp.ux.stepChange(steps[i], info(i));
          renderBar();
        })
        .catch(function (err) { console.error(err); })
        .then(function () { busy = false; moving = null; });
    }

    // ---- engine wiring: menus and alerts are DOM events (board-ui.js); the step callback (the engine
    // asking for the virtual next step when the player acts) navigates to it ----
    gapp.init(null, null, null, null, null);
    gapp.bindings(null, null, null, null, null, null, null, null, function () { go('last'); });

    // ---- deadline: ticks the clock partial's countdown and bar from its data-deadline and data-span
    function pad(n) { return (n < 10 ? '0' : '') + n; }

    function startClock() {
      if (clockTimer !== null) {
        clearInterval(clockTimer);
        clockTimer = null;
      }
      var box = document.getElementById('clock-box');
      var clock = $('#clock');
      var bar = $('#clock-bar');
      if (!ACTIVE || !box || !box.dataset.deadline || !clock || !bar) return;
      var deadline = new Date(box.dataset.deadline).getTime();
      if (isNaN(deadline)) return;
      var span = Math.max(1, (Number(box.dataset.span) || 0) * 60);
      function tick() {
        var left = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
        var d = Math.floor(left / 86400), h = Math.floor(left / 3600) % 24, m = Math.floor(left / 60) % 60;
        clock.textContent = d ? d + 'd ' + pad(h) + ':' + pad(m) : pad(h) + ':' + pad(m) + ':' + pad(left % 60);
        var pct = Math.max(0, Math.min(100, Math.round(100 * left / span)));
        bar.style.height = pct + '%';
        bar.parentNode.title = pct + ' % of the phase time left';
        if (!left && clockTimer !== null) {
          clearInterval(clockTimer);
          clockTimer = null;
        }
      }
      tick();
      if (deadline > Date.now()) clockTimer = setInterval(tick, 1000);
    }

    function boot() {
      var gameData = null;
      startClock();
      // a finished game has no phase rows left: its steps come from the history snapshot
      Promise.all([getJSON(routes.map), getJSON(routes.game), getJSON(OVER ? routes.history : routes.phases)])
        .then(function (res) {
          mapData = res[0];
          gameData = res[1];
          if (OVER) {
            // every step carries its orders; the final position is current and shown
            steps = shaper.link(shaper.buildHistory(mapData, gameData, (res[2] && res[2].phases) || []));
            current = steps.length - 1;
            view = current;
            return null;
          }
          var phases = (res[2] && res[2].data) || [];
          var withNext = FULL && phases.length > 0;
          steps = shaper.link(shaper.build(mapData, gameData, phases, PLAYER, withNext));
          current = withNext ? steps.length - 2 : steps.length - 1;
          view = current;
          // the orders that led to the phase being played
          return shaper.ensureOrders(steps[current]);
        })
        .then(function () {
          // no orders to fetch for spectators, before the game starts or once it is over
          if (PLAYER === null || !ACTIVE) return [];
          return getJSON(routes.orders).then(function (r) { return (r && r.data) || []; });
        })
        .then(function (orders) {
          orders = orders.map(function (o) { return Object.assign({}, o, { _changed: false }); });
          var last = steps[steps.length - 1];
          if (last.type === 'next') last.orders[PLAYER] = orders;
          // open on the last processed state ("what happened"), unless the player is already ready or has
          // touched an order this phase (seeded rows have updated_at == created_at until the player saves)
          var touched = orders.some(function (o) { return o.updated_at !== o.created_at; });
          if (last.type === 'next' && (PLAYER_READY || touched)) view = steps.length - 1;
          gapp.ux.stepChange(steps[view], info(view));
          gapp.launch(mapData, gameData, PLAYER, ACTIVE, PRE, OVER, PLAYER_READY, orders, function () {
            // first paint without glides or fades
            requestAnimationFrame(function () {
              requestAnimationFrame(function () { svg.classList.remove('instant'); });
            });
          });
          renderBar();
        })
        .catch(function (err) { console.error(err); });
    }

    // ---- a processed phase, in place ----
    function toast(detail) {
      document.dispatchEvent(new CustomEvent('board:alert', { detail: detail }));
    }

    function playerFlags(players) {
      var me = (players || []).filter(function (p) { return PLAYER !== null && p.country === PLAYER; })[0];
      PLAYER_ACTIVE = !!(me && me.is_active);
      PLAYER_READY = !!(me && me.is_ready);
      FULL = ACTIVE && PLAYER !== null && PLAYER_ACTIVE;
    }

    function refresh() {
      if (!gapp.launched || OVER || !ACTIVE || !steps.length) return;
      var id = steps[current] && steps[current].id;
      if (!id) return;
      refreshing = true;
      var clock = Promise.resolve().then(function () {
        if (window.htmx) return htmx.ajax('GET', routes.clock, { target: '#clock-box', swap: 'outerHTML' });
      });
      return Promise.all([
        getJSON(routes.phase.replace(':ID:', id)),
        getJSON(routes.phase_next + '?last_id=' + encodeURIComponent(id)),
        getJSON(routes.game),
        getJSON(routes.orders),
        clock,
        moving || Promise.resolve()
      ]).then(function (res) {
        var rowN = res[0], rowN1 = res[1], gameData = res[2];
        var orders = (res[3] && Array.isArray(res[3].data)) ? res[3].data : [];
        if (!rowN1 || rowN1.id === id) throw new Error('no phase after ' + id);
        orders = orders.map(function (o) { return Object.assign({}, o, { _changed: false }); });
        playerFlags(gameData.players);

        var oldCurrent = current;
        steps[oldCurrent].isLast = false;
        steps.splice(oldCurrent + 1);    // the old NEXT, if any
        var last = shaper.buildGameStep(mapData, rowN1, rowN.orders || {}, true);
        steps.push(last);
        if (FULL) {
          var next = shaper.buildNextGameStep(PLAYER, last);
          next.orders[PLAYER] = orders;
          steps.push(next);
        }
        shaper.link(steps);

        var lost = gapp.refresh(gameData, orders, PLAYER_READY, FULL);
        current = oldCurrent + 1;
        if (view >= oldCurrent) view = current;
        gapp.ux.stepChange(steps[view], info(view));
        renderBar();
        startClock();

        var box = document.getElementById('clock-box');
        var resolved = box ? box.dataset.resolved : '';
        var due = box ? box.dataset.due : '';
        var was = label(last), now = phaseLabel(rowN1);
        toast({
          kind: 'phase', key: 'phase', autoDismiss: 8, tone: TYPE_CLASS[now.kind] || '',
          title: 'TURN RESOLVED' + (resolved ? ' \u00b7 ' + resolved : ''),
          message: was.name + ' ' + was.type + ' resolved \u00b7 ' + now.name + ' ' + now.type + ' is open' +
            (due ? ', orders due ' + due : ', no deadline')
        });
        if (lost > 0) {
          toast({
            message: lost + (lost === 1 ? ' order change was' : ' order changes were') +
              ' not saved before the turn resolved.',
            dismissable: true
          });
        }
      }).catch(function (err) { console.error(err); })
        .then(function () { refreshing = false; });
    }

    document.addEventListener('game:state', function (e) {
      if (e.detail === 'processed') refresh();
    });

    // ---- input (the engine refuses clicks while the player is ready) ----
    svg.addEventListener('click', function (e) {
      if (!gapp.launched) return;
      var g = e.target.closest('[data-province]');
      if (!g) return;
      gapp.act.click(gapp.env.ids[g.getAttribute('data-province')], { x: e.clientX, y: e.clientY });
    });

    document.querySelectorAll('[data-nav]').forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.preventDefault();
        go(b.getAttribute('data-nav'));
      });
    });
    // the phase keys (board-ui.js) ask for navigation
    document.addEventListener('board:nav', function (e) {
      if (e.detail && e.detail.where) go(e.detail.where);
    });

    boot();
  });
})();
