/* Board chrome: the game page's Alpine components (orders, powers, legend, popover, alerts) and its keybindings.
 *
 * The engine (game.js, `gapp`) knows nothing about the page: it dispatches DOM events on `document` and the
 * components below listen; the components call back into the engine (`gapp.act.uxEvent`, `gapp.game.*`).
 * Events heard here (detail shapes in ux.coffee / game.coffee / main.coffee):
 *   board:launched, game:step, orders:changed, orders:saving, orders:saved, orders:error, game:ready,
 *   game:players (socket), board:menu, board:menu-close, board:alert, board:zoom, board:legend.
 * Events sent from here: board:nav {where} (the page navigates), board:legend (L), chat:toggle on window (C).
 *
 * Loaded from the page head before the (deferred) Alpine, so the alpine:init listener is in place in time.
 * Components may start before or after the engine launches: each one pulls the current state on init.
 *
 * One global: BoardUI.
 */
(function (global) {
  'use strict';

  function on(name, fn) {
    document.addEventListener(name, function (e) { fn(e.detail, e); });
  }
  function emit(name, detail) {
    document.dispatchEvent(new CustomEvent(name, { detail: detail }));
  }
  function app() { return global.gapp || null; }
  function launched() { return !!(global.gapp && global.gapp.launched); }

  // the board:launched detail ({player, power, players, scsToWin, canOrder, ready, pre, over}), kept for late starters
  var S = { launch: null };
  on('board:launched', function (d) { S.launch = d || null; });

  function lastStep() {
    var g = app();
    return g && g.ux ? g.ux.lastStep : null;
  }

  function reasonText(r) {
    if (r === null || r === undefined) return '';
    if (Array.isArray(r)) return r.map(reasonText).join(', ');
    if (typeof r === 'object') return Object.keys(r).map(function (k) { return reasonText(r[k]); }).join(', ');
    return String(r);
  }

  // ISO timestamp (UTC when it carries no offset) -> "14 OCT 23:00" in local time
  var MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
  function formatStamp(iso) {
    if (!iso) return '';
    var s = String(iso).replace(' ', 'T');
    if (!/[Zz]|[+-]\d\d:?\d\d$/.test(s)) s += 'Z';
    var d = new Date(s);
    if (isNaN(d.getTime())) return '';
    var pad = function (n) { return (n < 10 ? '0' : '') + n; };
    return d.getDate() + ' ' + MONTHS[d.getMonth()] + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  }

  // ---------------------------------------------------------------- orders panel

  function orders() {
    return {
      rows: [],
      editable: false,      // the player's pending orders, not ready
      isNext: false,        // the virtual next step is displayed (pending orders)
      isCurrent: true,      // not a history view
      resolvedAt: '',       // when the viewed step's phase was resolved (none for pre-game and NEXT)
      saving: false,
      errors: [],           // [{territory, code, reason}] from the last save
      ready: false,
      readyBusy: false,
      canOrder: false,
      player: null,
      subtitle: '',

      init: function () {
        var self = this;
        on('board:launched', function (d) { self.launch(d); });
        on('game:step', function (d) { self.step(d); });
        on('orders:changed', function (d) { self.load(d); });
        on('orders:saving', function () { self.saving = true; });
        on('orders:saved', function () { self.saving = false; self.errors = []; });
        on('orders:error', function (errs) { self.saving = false; self.errors = self.errorList(errs); });
        on('game:ready', function (r) { self.ready = !!r; self.readyBusy = false; });
        if (S.launch) this.launch(S.launch);
        if (lastStep()) this.step(lastStep());
        if (launched()) this.load(app().game.ordersState());
      },

      launch: function (d) {
        this.errors = [];
        this.canOrder = !!d.canOrder;
        this.ready = !!d.ready;
        this.player = d.player || null;
        if (lastStep()) this.step(lastStep());
      },

      step: function (d) {
        var l = d.label || {};
        this.isCurrent = d.isCurrent !== false;
        this.resolvedAt = formatStamp(d.resolvedAt);
        this.subtitle = [l.name, l.type, this.player].filter(function (x) { return !!x && x !== '\u00a0'; }).join(' \u00b7 ');
      },

      load: function (d) {
        this.rows = d.orders || [];
        this.editable = !!d.editable;
        this.isNext = !!(d.phase && d.phase.isNext);
        this.saving = !!d.saving;
        this.ready = !!d.ready;
      },

      errorList: function (errs) {
        var env = app() ? app().env : { codes: {}, names: {} };
        return Object.keys(errs || {}).map(function (t) {
          return { territory: t, code: env.codes[t] || env.names[t] || t, reason: reasonText(errs[t]) };
        });
      },

      // one source of truth: the header state derives from the rows' pending flags
      get unsaved() { return this.rows.some(function (o) { return o.pending; }); },
      get status() {
        if (this.saving) return 'saving';
        if (this.errors.length) return 'error';
        if (this.unsaved) return 'unsaved';
        return 'saved';
      },
      // one element driven by text and classes: x-show toggles show on a frame and hide on a microtask,
      // so four x-shows on a state that can flip twice in a frame could leave two of them visible
      get statusStyle() {
        return {
          unsaved: { label: 'UNSAVED', text: 'text-warn', dot: 'bg-warn shadow-[0_0_6px_#ffb347]' },
          saving: { label: 'SAVING', text: 'text-signal', dot: 'bg-signal animate-pulse' },
          saved: { label: 'SAVED', text: 'text-ok', dot: 'bg-ok' },
          error: { label: 'NOT SAVED', text: 'text-alert', dot: 'bg-alert shadow-[0_0_6px_#ff4d4d]' }
        }[this.status];
      },
      get showControls() { return this.canOrder && this.isCurrent; },

      // the row's unit glyph: solid in the owner's colour, a dashed outline for a build
      glyph: function (o) {
        if (o.type === 'build_army' || o.type === 'build_fleet') {
          return { fill: 'none', stroke: 'var(--c)', width: 1.6, dash: '3 2' };
        }
        return { fill: 'var(--c)', stroke: '#05080c', width: 2, dash: null };
      },
      removable: function (o) { return this.editable && o.type !== 'hold'; },

      remove: function (o) {
        if (launched()) app().game.resetOrder(o.territory);
      },
      save: function () {
        if (launched()) app().game.saveNow();
      },
      toggleReady: function () {
        if (!launched() || !this.canOrder || this.readyBusy) return;
        var self = this;
        this.readyBusy = true;
        app().game.setReady(!this.ready).then(function () { self.readyBusy = false; });
      }
    };
  }

  // ---------------------------------------------------------------- powers table

  function powers() {
    return {
      players: [],          // {country, name, ready, active, state}
      sc: {},
      troops: {},
      me: null,
      target: 0,
      isCurrent: true,
      over: false,          // game over: each power's result (GameRole.State) in place of ready

      init: function () {
        var self = this;
        on('board:launched', function (d) { self.setup(d); });
        on('game:step', function (d) { self.setStep(d); });
        on('game:players', function (d) { self.update(d || {}); });
        on('game:ready', function (r) { if (self.me) self.update({ country: self.me, is_ready: !!r }); });
        if (S.launch) this.setup(S.launch);
        if (lastStep()) this.setStep(lastStep());
      },

      setup: function (d) {
        this.me = d.player || null;
        this.target = d.scsToWin || 0;
        this.over = !!d.over;
        this.players = (d.players || []).map(function (p) {
          return {
            country: p.country, name: p.name || null, ready: !!p.is_ready, active: !!p.is_active,
            state: p.state === undefined ? null : p.state
          };
        });
      },

      setStep: function (d) {
        this.sc = d.supplyCenters || {};
        this.troops = d.troops || {};
        this.isCurrent = d.isCurrent !== false;
      },

      update: function (d) {
        if (!d.country) return;
        var p = this.players.filter(function (x) { return x.country === d.country; })[0];
        if (!p) {
          p = { country: d.country, name: null, ready: false, active: false, state: null };
          this.players.push(p);
        }
        if (d.is_ready !== undefined) p.ready = !!d.is_ready;
        if (d.is_active !== undefined) p.active = !!d.is_active;
      },

      get rows() {
        var self = this, g = app();
        var key = function (c) { return g && g.env ? g.env.countryKey(c) : String(c).toLowerCase(); };
        return this.players.map(function (p) {
          var t = self.troops[p.country] || {};
          return {
            country: p.country,
            name: p.name,
            key: key(p.country),
            sc: self.sc[p.country] || 0,
            units: (t.armies || 0) + (t.fleets || 0),
            ready: p.ready,
            active: p.active,
            state: p.state,
            me: p.country === self.me
          };
        }).sort(function (a, b) {
          return (b.sc - a.sc) || (b.units - a.units) || (a.country < b.country ? -1 : 1);
        });
      },

      // n/m READY among the powers playing this phase (all of them before the game starts)
      get readyCaption() {
        var active = this.players.filter(function (p) { return p.active; });
        var base = active.length ? active : this.players;
        var n = base.filter(function (p) { return p.ready; }).length;
        return n + '/' + base.length + ' READY';
      }
    };
  }

  // ---------------------------------------------------------------- legend

  function legend() {
    return {
      open: true,
      init: function () {
        var self = this;
        on('board:legend', function () { self.toggle(); });
      },
      toggle: function () { this.open = !this.open; }
    };
  }

  // ---------------------------------------------------------------- province popover

  function popover() {
    return {
      open: false,
      m: {},                // the board:menu detail
      current: false,       // the order type the territory has now (hasMove / hasBuild)
      order: '',            // its text
      dragged: null,        // position once dragged, kept for the session

      init: function () {
        var self = this, el = this.$el;
        on('board:menu', function (d) {
          self.m = d || {};
          self.current = self.m.current || false;
          self.refresh();
          self.open = true;
          self.$nextTick(function () { self.place(); });
        });
        on('board:menu-close', function (d) {
          if (!d || !self.m || d.type === self.m.type) self.open = false;
        });
        on('board:launched', function () { self.open = false; });
        on('orders:changed', function () { if (self.open) self.refresh(); });
        if (global.Floating) {
          Floating.draggable(el, '[data-drag]', function (pos) {
            self.dragged = pos;
            el.style.left = pos[0] + 'px';
            el.style.top = pos[1] + 'px';
          });
        }
        global.addEventListener('resize', function () { if (self.open) self.place(); });
        // order keys, live only while the popover is open; runs after the global handler (registered
        // at load), so a key that one consumed (defaultPrevented) is left alone
        document.addEventListener('keydown', function (e) {
          if (!self.open || e.defaultPrevented || inert(e)) return;
          var k = e.key && e.key.length === 1 ? e.key.toLowerCase() : '';
          var keys = self.keyActions();
          if (!k || !Object.prototype.hasOwnProperty.call(keys, k)) return;
          e.preventDefault();
          if (e.repeat || !keys[k]) return;    // null: that button is disabled
          self.act(keys[k]);
        });
      },

      // default: top-right of the board, by the sidebar, 12 px margins
      place: function () {
        var self = this;
        if (!global.Floating) return;
        // just switched from display:none: not laid out yet on the first open, measure on the next frame
        if (!this.$el.offsetWidth) { requestAnimationFrame(function () { if (self.open) self.place(); }); return; }
        Floating.place(this.$el, { pos: this.dragged }, null, {
          pos: function (el, c) { return [c.clientWidth - el.offsetWidth - 12, 12]; }
        });
      },

      // the unit the order is for: the menu's territory, the selected unit while choosing a coast
      subject: function () {
        var g = app();
        if (this.m.type === 'coast' && g) return g.act.active;
        return this.m.territory;
      },

      refresh: function () {
        var g = app(), t = this.subject();
        if (!g || t === null || t === undefined) { this.order = ''; return; }
        if (this.m.type !== 'coast') this.current = g.game.hasMove(t) || g.game.hasBuild(t) || false;
        var row = g.game.orders[t];
        this.order = row ? g.game.orderText(row) : '';
      },

      is: function (type) { return this.m.type === type; },
      isOn: function (action) {
        if (action === 'hold') return this.m.type === 'territory' && !this.current;
        return this.current === action;
      },
      get detail() {
        var m = this.m, bits = [m.code];
        if (m.country) bits.push(m.country);
        if (m.unit) bits.push(m.unit);
        if (m.dislodged) bits.push('dislodged');
        return bits.filter(function (x) { return !!x; }).join(' \u00b7 ');
      },
      get coastTitle() {
        var g = app(), t = this.m.territory;
        return 'Coast of ' + (this.m.name || (g && t ? g.env.names[t] : '') || '');
      },

      // the open section's keys: key -> action, null while that button is :disabled (same conditions)
      keyActions: function () {
        var m = this.m, k = {};
        if (m.type === 'territory') {
          k = { h: 'hold', m: 'move', s: 'support_move', d: 'support_hold', v: m.canConvoy ? 'convoy' : null };
        } else if (m.type === 'build') {
          k = { a: m.canBuild ? 'build_army' : null, f: m.canBuildFleet ? 'build_fleet' : null,
                d: m.canDisband ? 'disband' : null };
        } else if (m.type === 'retreat') {
          k = { m: 'retreat', d: 'disband' };
        } else if (m.type === 'coast') {
          var ck = this.coastKeys();
          Object.keys(ck).forEach(function (c) { k[ck[c]] = 'coast:' + c; });
        }
        return k;
      },
      // coast chooser: each coast name's first letter, lowercase; a letter already taken by an earlier
      // coast (or a global key) moves on to the name's next letter, e.g. North, Nord -> n, o
      coastKeys: function () {
        var used = {}, out = {};
        (this.m.coasts || []).forEach(function (c) {
          var s = String(c).toLowerCase().replace(/[^a-z]/g, '');
          for (var i = 0; i < s.length; i++) {
            if (!used[s[i]] && !KEYS[s[i]]) { used[s[i]] = true; out[c] = s[i]; return; }
          }
        });
        return out;
      },
      coastKey: function (c) { return this.coastKeys()[c] || ''; },

      act: function (action) {
        if (launched()) app().act.uxEvent(action);
      },
      close: function () {
        if (launched() && app().act.current !== 'none') app().act.uxEvent('close');
        else this.open = false;
      }
    };
  }

  // ---------------------------------------------------------------- toasts

  function alerts() {
    return {
      items: [],
      seq: 0,
      init: function () {
        var self = this;
        on('board:alert', function (d) { self.push(d || {}); });
        // the engine's own game:players listener runs first (registered at load): its players are up to date here
        on('game:players', function (d) { self.ready(d || {}); });
      },
      // autoDismiss: seconds; the same key (default: the message) again updates the item and restarts its timer
      // instead of stacking
      push: function (d) {
        var self = this, item = null, key = d.key || d.message;
        var fields = {
          kind: d.kind || 'alert', message: d.message, country: d.country || null, power: d.power || null,
          count: d.count || '', title: d.title || '', tone: d.tone || ''
        };
        this.items.forEach(function (i) { if (i.key === key) item = i; });
        if (item) {
          Object.assign(item, fields);
        } else {
          this.items.push(Object.assign({ id: ++this.seq, key: key, dismissable: d.dismissable !== false, timer: null }, fields));
          if (this.items.length > 5) this.items.shift();
          item = this.items[this.items.length - 1];
        }
        if (item.timer) clearTimeout(item.timer);
        if (d.autoDismiss) {
          var id = item.id;
          item.timer = setTimeout(function () { self.dismiss(id); }, d.autoDismiss * 1000);
        }
      },
      dismiss: function (id) {
        this.items = this.items.filter(function (i) { return i.id !== id; });
      },
      // another power just got ready: "X is ready · n of m ready", counted as the powers header does (the powers
      // playing this phase); the player's own ready and un-readies are not announced
      ready: function (d) {
        var g = app();
        if (d.is_ready !== true || !d.country || !g || !g.game || d.country === g.game.country) return;
        var players = g.game.players || [];
        var active = players.filter(function (p) { return p.is_active; });
        var base = active.length ? active : players;
        var n = base.filter(function (p) { return p.is_ready; }).length;
        this.push({
          kind: 'ready', key: 'ready:' + d.country, message: d.country + ' is ready', country: d.country,
          power: g.env.countryKey(d.country), count: n + ' of ' + base.length + ' ready', autoDismiss: 4
        });
      }
    };
  }

  document.addEventListener('alpine:init', function () {
    global.Alpine.data('orders', orders);
    global.Alpine.data('powers', powers);
    global.Alpine.data('legend', legend);
    global.Alpine.data('popover', popover);
    global.Alpine.data('alerts', alerts);
  });

  // ---------------------------------------------------------------- zoom, navigation, keys

  function zoom(action) {
    var g = app(), v = g && g.screen ? g.screen.view : null;
    if (!v) return;
    if (action === 'in') v.zoomIn();
    else if (action === 'out') v.zoomOut();
    else v.reset();
  }

  function nav(where) { emit('board:nav', { where: where }); }

  function toggleReady() {
    var st = lastStep();
    if (!launched() || !S.launch || !S.launch.canOrder) return;
    if (st && st.isCurrent === false) return;
    app().game.setReady(!app().game.ready);
  }

  // Esc: closes the open menu, or drops the order being built (the engine's 'close' does both)
  function escape() {
    if (launched() && app().act.current !== 'none') app().act.uxEvent('close');
  }

  var KEYS = {
    ArrowLeft: function () { nav('prev'); },
    ArrowRight: function () { nav('next'); },
    Home: function () { nav('first'); },
    End: function () { nav('last'); },
    '+': function () { zoom('in'); },
    '=': function () { zoom('in'); },
    '-': function () { zoom('out'); },
    '0': function () { zoom('reset'); },
    c: function () { global.dispatchEvent(new CustomEvent('chat:toggle')); },
    l: function () { emit('board:legend'); },
    r: toggleReady,
    Escape: escape
  };
  var NO_REPEAT = { c: true, l: true, r: true, Escape: true };

  // keys are off with a modifier held or while a text field has focus
  function inert(e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return true;
    var a = document.activeElement;
    return !!(a && (a.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)));
  }

  document.addEventListener('keydown', function (e) {
    if (inert(e)) return;
    var k = e.key && e.key.length === 1 ? e.key.toLowerCase() : e.key;
    var fn = KEYS[k];
    if (!fn) return;
    e.preventDefault();
    if (e.repeat && NO_REPEAT[k]) return;
    fn();
  });

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-z]').forEach(function (b) {
      b.addEventListener('click', function () { zoom(b.getAttribute('data-z')); });
    });
    var lvl = document.getElementById('zoomlvl');
    on('board:zoom', function (d) {
      if (lvl && d) lvl.textContent = d.level.toFixed(1) + '\u00d7';
    });
  });

  global.BoardUI = { zoom: zoom, nav: nav, toggleReady: toggleReady, escape: escape };
})(window);
