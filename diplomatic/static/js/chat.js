/* The in-game chat: Alpine component "chat" on #chat (templates/games/_chat.haml).
 *
 * Rooms come from the API (General plus one DM room per other power, as the game's press type allows), messages
 * arrive live as document `game:chat` events (dispatched by the engine's socket; event.detail is the ChatMessage
 * row) and are sent with a POST. The box floats in #board through Floating (static/js/floating.js): dragged by its
 * header, resized from the top edge, the right edge and the top-right corner; position and size live in the
 * component's state for the session. `chat:toggle` on window collapses / expands it (the C key).
 *
 * Registration: Alpine (deferred, earlier in the head) starts in a microtask right after its own script runs, so by
 * the time this deferred script runs `alpine:init` has already fired and the initial tree walk is done. The markup
 * therefore carries the component in `data-x-data`, which Alpine ignores; once `chat` is registered here the
 * attribute becomes `x-data` (inside Alpine.mutateDom, so the mutation observer does not see it) and the element
 * is initialised with Alpine.initTree. If this script ever runs before Alpine, the same happens from `alpine:init`,
 * before Alpine's own walk, which then picks the element up. No globals besides the Alpine registration.
 */
(function () {
  'use strict';

  var PAGE = 25;          // messages per page (api.chat_messages)
  var BOX_W = 340;        // default width
  var MIN_H = 260;        // default height floor; the default is half the board's height
  var EDGE = 12;          // default distance from the board's left and bottom edges
  var LOADERS = 4;        // concurrent page-1 fetches at boot

  // the board's country key (controllers/games.py country_key, Environment.countryKey)
  function countryKey(name) {
    return String(name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  }

  function short(name, n) {
    return String(name).replace(/\s+/g, ' ').trim().slice(0, n).trim().toUpperCase();
  }

  // datetimes are serialised as ISO 8601 with an offset; a naive one is UTC
  function parseTime(value) {
    if (!value) return null;
    var s = String(value).replace(' ', 'T');
    if (!/(Z|[+-]\d\d:?\d\d)$/i.test(s)) s += 'Z';
    var d = new Date(s);
    return isNaN(d.getTime()) ? null : d;
  }

  function pad(n) {
    return (n < 10 ? '0' : '') + n;
  }

  // fetch JSON; resolves { ok, status, data } for any HTTP status, rejects on network errors only
  function request(url, opts) {
    opts = opts || {};
    var init = { method: opts.method || 'GET', credentials: 'same-origin', headers: { Accept: 'application/json' } };
    if (opts.body !== undefined) {
      init.headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(opts.body);
    }
    return fetch(url, init).then(function (r) {
      return r.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { data = null; }
        //: the login guard answers with { error } rather than a failing status
        var ok = r.ok && !(data && data.error);
        return { ok: ok, status: r.status, data: data };
      });
    });
  }

  function getJSON(url) {
    return request(url).then(function (res) {
      if (!res.ok) throw new Error(res.status + ' ' + url);
      return res.data;
    });
  }

  function describeError(res) {
    var err = res && res.data && res.data.error;
    if (res && res.status === 403) return 'You are not a member of this room.';
    if (err && typeof err === 'object') {
      var parts = Object.keys(err).map(function (k) {
        return (k === 'message' ? '' : k + ': ') + err[k];
      });
      if (parts.length) return parts.join(' · ');
    }
    if (typeof err === 'string') return err;
    return 'Not sent (' + (res ? res.status : 'error') + ').';
  }

  function factory(cfg) {
    // per instance, not reactive
    var playerId = Number(cfg.playerId);
    var loads = {};        // room id -> in-flight page fetch
    var readBusy = {};     // room id -> a PUT reading is in flight
    var readDirty = {};    // room id -> the mark moved while it was in flight
    var unknownTried = {}; // room ids that already triggered a rooms refetch
    var pending = [];      // socket rows received before boot finished
    var reloading = null;  // in-flight rooms refetch
    var listeners = [];
    var observer = null;

    return {
      // ---- state ----
      rooms: [],        // [{ id, type, general, name, country, key, label, title, members, me, messages,
                        //    loaded, loading, page, more, unread }], Global first
      readings: {},     // room id -> ChatReading row { id, room, member, message }
      players: {},      // GameRole id -> { country, name }
      active: null,     // id of the room shown
      collapsed: false,
      pos: null,        // [left, top] in the board, once dragged or resized
      size: null,       // [width, height], once resized
      draft: '',
      sending: false,
      error: '',        // composer error (send)
      loadError: '',
      ready: false,     // boot done
      none: false,      // no rooms (press disabled): the box is hidden

      // ---- lifecycle ----
      init: function () {
        var self = this;
        var el = this.$root;
        var board = this.board();

        this.listen(document, 'game:chat', function (e) { self.receive(e.detail); });
        this.listen(window, 'chat:toggle', function () { self.toggle(); });
        if (window.ResizeObserver && board) {
          observer = new ResizeObserver(function () { self.place(); });
          observer.observe(board);
        } else {
          this.listen(window, 'resize', function () { self.place(); });
        }

        if (window.Floating) {
          Floating.draggable(el, '[data-drag]', function (pos) {
            self.pos = pos;
            self.place();
          });
          Floating.resizable(el, { n: '[data-resize="n"]', e: '[data-resize="e"]', ne: '[data-resize="ne"]' },
            { minW: 300, minH: 200 }, function (size, pos) {
              self.size = size;
              self.pos = pos;
              self.place();
            });
        }
        // x-cloak goes in a microtask; a frame callback runs after it and before the first paint
        requestAnimationFrame(function () { self.place(); });

        this.boot();
      },

      destroy: function () {
        listeners.forEach(function (l) { l[0].removeEventListener(l[1], l[2]); });
        listeners = [];
        if (observer) observer.disconnect();
      },

      listen: function (target, type, fn) {
        target.addEventListener(type, fn);
        listeners.push([target, type, fn]);
      },

      boot: function () {
        var self = this;
        Promise.all([
          getJSON(cfg.game).catch(function () { return null; }),
          getJSON(cfg.rooms),
          getJSON(cfg.readings).catch(function () { return null; })
        ]).then(function (res) {
          self.setPlayers(res[0]);
          self.setReadings(res[2]);
          self.addRooms((res[1] && res[1].data) || []);
          self.ready = true;
          if (!self.rooms.length) {
            self.none = true;
            return;
          }
          self.open(self.rooms[0].id, false);
          pending.splice(0).forEach(function (row) { self.receive(row); });
          self.loadAll();
        }).catch(function (err) {
          console.error('chat:', err);
          self.loadError = 'Chat unavailable, reload the page to retry.';
          self.ready = true;
        });
      },

      // ---- data ----
      setPlayers: function (game) {
        var players = {};
        ((game && game.players) || []).forEach(function (p) {
          players[p.id] = { country: p.country, name: p.name || null };
        });
        this.players = players;
      },

      setReadings: function (res) {
        var self = this;
        ((res && res.data) || []).forEach(function (rd) {
          var have = self.readings[rd.room];
          // never move a known mark backwards
          if (have && (have.message || 0) > (rd.message || 0)) rd.message = have.message;
          self.readings[rd.room] = rd;
        });
      },

      // a room row from the API, shaped for the box; DM rooms are named after the OTHER member's country
      normalize: function (row) {
        var players = this.players;
        var members = row.members || [];
        var me = members.filter(function (m) { return Number(m.player) === playerId; })[0];
        var general = row.type !== 10;
        var other = general ? null : members.filter(function (m) { return Number(m.player) !== playerId; })[0];
        var who = other ? players[other.player] : null;
        var country = who ? who.country : null;
        var name = general ? 'Global' : (country || row.name || 'Room ' + row.id);
        var title = general ? 'Global: every power' : name + (who && who.name ? ' · ' + who.name : '');
        return {
          id: row.id, type: row.type, general: general, name: name, country: country,
          key: country ? countryKey(country) : null, label: general ? 'GLOBAL' : short(name, 3), title: title,
          members: members, me: me ? me.id : null,
          messages: [], loaded: false, loading: false, page: 0, more: false, unread: 0
        };
      },

      // add the rooms not known yet; Global first, then by name; DM labels lengthened until unique
      addRooms: function (rows) {
        var self = this;
        var list = this.rooms.slice();
        rows.forEach(function (row) {
          if (!list.some(function (r) { return r.id === row.id; })) list.push(self.normalize(row));
        });
        list.sort(function (a, b) {
          if (a.general !== b.general) return a.general ? -1 : 1;
          return a.name.localeCompare(b.name) || a.id - b.id;
        });
        var dms = list.filter(function (r) { return !r.general; });
        for (var n = 4; n <= 16; n++) {
          var seen = {};
          dms.forEach(function (r) { seen[r.label] = (seen[r.label] || 0) + 1; });
          var dup = dms.filter(function (r) { return seen[r.label] > 1; });
          if (!dup.length) break;
          dup.forEach(function (r) { r.label = short(r.name, n); });
        }
        this.rooms = list;
      },

      // refetch players, rooms and readings (a message for an unknown room); concurrent calls share one fetch
      reloadRooms: function () {
        var self = this;
        if (reloading) return reloading;
        reloading = Promise.all([
          getJSON(cfg.game).catch(function () { return null; }),
          getJSON(cfg.rooms),
          getJSON(cfg.readings).catch(function () { return null; })
        ]).then(function (res) {
          if (res[0]) self.setPlayers(res[0]);
          self.setReadings(res[2]);
          self.addRooms((res[1] && res[1].data) || []);
          if (self.rooms.length) self.none = false;
          if (self.active === null && self.rooms.length) self.open(self.rooms[0].id, false);
          self.loadAll();
        }).catch(function (err) {
          console.error('chat:', err);
        }).then(function () {
          reloading = null;
        });
        return reloading;
      },

      findRoom: function (id) {
        id = Number(id);
        for (var i = 0; i < this.rooms.length; i++) if (this.rooms[i].id === id) return this.rooms[i];
        return null;
      },

      // merge rows into a room's messages, kept in id order; returns how many were new (dedupe by id)
      merge: function (room, rows) {
        var have = {};
        room.messages.forEach(function (m) { have[m.id] = true; });
        var add = rows.filter(function (m) {
          if (!m || m.id === undefined || m.id === null || have[m.id]) return false;
          have[m.id] = true;
          return true;
        });
        if (!add.length) return 0;
        var list = room.messages.concat(add);
        list.sort(function (a, b) { return a.id - b.id; });
        room.messages = list;
        return add.length;
      },

      // next page of a room (page 1 on first load), newest first from the API
      loadRoom: function (id) {
        var self = this;
        if (loads[id]) return loads[id];
        var room = this.findRoom(id);
        if (!room) return Promise.resolve();
        var page = room.page + 1;
        room.loading = true;
        loads[id] = request(cfg.messages.replace(':ID:', id) + '?page=' + page).then(function (res) {
          var r = self.findRoom(id);
          if (!r) return;
          if (!res.ok) throw new Error(res.status + ' room ' + id);
          var rows = (res.data && res.data.data) || [];
          self.merge(r, rows);
          r.page = page;
          r.more = rows.length >= PAGE;
          r.loaded = true;
          self.recount(r);
        }).catch(function (err) {
          console.error('chat:', err);
          var r = self.findRoom(id);
          if (r) r.loaded = true;   // show what we have rather than LOADING forever
        }).then(function () {
          delete loads[id];
          var r = self.findRoom(id);
          if (r) r.loading = false;
        });
        return loads[id];
      },

      // page 1 of every room not loaded yet, a few at a time: the unread badges need them
      loadAll: function () {
        var self = this;
        var queue = this.rooms.filter(function (r) { return !r.loaded; }).map(function (r) { return r.id; });
        function next() {
          var id = queue.shift();
          if (id === undefined) return null;
          return self.loadRoom(id).then(next, next);
        }
        for (var i = 0; i < LOADERS; i++) next();
      },

      earlier: function () {
        var self = this;
        var room = this.room();
        var list = this.$refs.list;
        if (!room || !room.more || loads[room.id]) return;
        var fromBottom = list ? list.scrollHeight - list.scrollTop : 0;
        var id = room.id;
        this.loadRoom(id).then(function () {
          self.$nextTick(function () {
            if (list && self.active === id) list.scrollTop = list.scrollHeight - fromBottom;
          });
        });
      },

      // ---- unread ----
      mark: function (id) {
        var rd = this.readings[id];
        return (rd && rd.message) || 0;
      },

      // unread = messages after the reading's message (all of them when it is null), not counting our own
      recount: function (room) {
        var mark = this.mark(room.id);
        var me = room.me;
        room.unread = room.messages.filter(function (m) {
          return m.id > mark && (me === null || m.sender !== me);
        }).length;
      },

      // our own message moved the mark on the server (ChatMessage.update_readings): follow locally, no PUT
      bump: function (id, messageId) {
        var rd = this.readings[id];
        if (rd && (rd.message || 0) < messageId) rd.message = messageId;
      },

      // the room is being read: move the mark to its last message and tell the server
      markRead: function (id) {
        var room = this.findRoom(id);
        if (!room) return;
        if (room.messages.length) {
          var last = room.messages[room.messages.length - 1].id;
          var rd = this.readings[id];
          if (!rd) {
            this.readings[id] = { id: null, room: id, member: room.me, message: last };
          } else if ((rd.message || 0) < last) {
            rd.message = last;
            this.putRead(id);
          }
        }
        this.recount(room);
      },

      // one PUT per room at a time; a mark moved meanwhile is sent when it returns
      putRead: function (id) {
        var self = this;
        var rd = this.readings[id];
        if (!rd || rd.id === null || rd.id === undefined) return;
        if (readBusy[id]) {
          readDirty[id] = true;
          return;
        }
        readBusy[id] = true;
        readDirty[id] = false;
        request(cfg.read.replace(':ID:', rd.id), { method: 'PUT', body: { message: rd.message } })
          .then(function (res) {
            if (!res.ok) console.warn('chat: reading not saved', res.status, res.data);
          })
          .catch(function (err) { console.warn('chat: reading not saved', err); })
          .then(function () {
            readBusy[id] = false;
            if (readDirty[id]) self.putRead(id);
          });
      },

      // ---- rooms ----
      room: function () {
        return this.active === null ? null : this.findRoom(this.active);
      },

      open: function (id, focus) {
        var self = this;
        var room = this.findRoom(id);
        if (!room) return;
        var rid = room.id;
        if (this.active !== rid) this.error = '';
        this.active = rid;
        var show = function () {
          if (self.active !== rid) return;
          self.scrollBottom();
          if (!self.collapsed) self.markRead(rid);
        };
        if (room.loaded) show();
        else this.loadRoom(rid).then(show);
        if (focus) this.$nextTick(function () { if (self.$refs.composer) self.$refs.composer.focus(); });
      },

      // ---- socket ----
      receive: function (row) {
        var self = this;
        if (!row || row.id === undefined || row.id === null || row.room === undefined || row.room === null) return;
        if (!this.ready) {
          pending.push(row);
          return;
        }
        var room = this.findRoom(row.room);
        if (!room) {
          if (unknownTried[row.room]) return;
          unknownTried[row.room] = true;
          this.reloadRooms().then(function () {
            if (self.findRoom(row.room)) self.receive(row);
          });
          return;
        }
        if (!this.merge(room, [row])) return;   // already there: the echo of our own send
        if (room.me !== null && row.sender === room.me) this.bump(room.id, row.id);
        if (room.id === this.active && !this.collapsed) {
          this.scrollBottom();
          this.markRead(room.id);
        } else {
          this.recount(room);
        }
      },

      // ---- composer ----
      send: function () {
        var self = this;
        var room = this.room();
        var text = this.draft.trim();
        if (!room || !text || this.sending) return;
        var id = room.id;
        this.sending = true;
        this.error = '';
        request(cfg.send, { method: 'POST', body: { room: id, text: text } })
          .then(function (res) {
            if (res.status === 201 && res.data && res.data.id !== undefined) {
              var r = self.findRoom(res.data.room !== undefined ? res.data.room : id);
              if (r) {
                self.merge(r, [res.data]);
                self.bump(r.id, res.data.id);
                self.recount(r);
              }
              if (self.draft.trim() === text) self.draft = '';
              self.$nextTick(function () {
                self.grow();
                if (r && self.active === r.id) self.scrollBottom();
              });
            } else {
              self.error = describeError(res);
            }
          })
          .catch(function () {
            self.error = 'Network error, message not sent.';
          })
          .then(function () {
            self.sending = false;
          });
      },

      // Enter sends, Shift+Enter is a newline (IME composition untouched)
      onEnter: function (e) {
        if (e.shiftKey || e.isComposing) return;
        e.preventDefault();
        this.send();
      },

      grow: function () {
        var ta = this.$refs.composer;
        if (!ta) return;
        ta.style.height = '';
        if (ta.value) ta.style.height = Math.min(ta.scrollHeight + 2, 96) + 'px';
      },

      // ---- box ----
      board: function () {
        return document.getElementById('board') || this.$root.parentElement;
      },

      // collapsing keeps the edge the box rests on: the bottom edge when it touches the board's bottom
      // (the default position), the top edge otherwise
      toggle: function () {
        var self = this;
        var el = this.$root, board = this.board();
        var top = el.offsetTop, left = el.offsetLeft;
        var atBottom = board && (board.clientHeight - (top + el.offsetHeight)) <= EDGE + 2;
        this.collapsed = !this.collapsed;
        this.$nextTick(function () {
          if (board && window.Floating) {
            if (self.collapsed) {
              el.style.height = '';
              self.pos = atBottom ? [left, board.clientHeight - el.offsetHeight - EDGE] : [left, top];
            } else if (atBottom) {
              var h = self.size ? self.size[1] : Math.max(MIN_H, Math.round(board.clientHeight * 0.5));
              self.pos = [left, board.clientHeight - h - EDGE];
            }
          }
          self.place();
          if (!self.collapsed && self.active !== null) {
            self.scrollBottom();
            self.markRead(self.active);
          }
        });
      },

      // apply the session's position and size, or the defaults (bottom-left, 340 px, half the board's height);
      // collapsed is the header alone. Clamped into the board, without overwriting what the user chose.
      place: function () {
        var el = this.$root;
        var board = this.board();
        if (!board || !window.Floating || !el.offsetParent) return;
        var size = this.size ? [this.size[0], this.size[1]]
          : [BOX_W, Math.max(MIN_H, Math.round(board.clientHeight * 0.5))];
        if (this.collapsed) {
          el.style.width = Math.min(size[0], board.clientWidth - 8) + 'px';
          el.style.height = '';
        }
        Floating.place(el, { pos: this.pos ? [this.pos[0], this.pos[1]] : null, size: this.collapsed ? null : size },
          board, { pos: function (e, c) { return [EDGE, c.clientHeight - e.offsetHeight - EDGE]; } });
      },

      scrollBottom: function () {
        var self = this;
        this.$nextTick(function () {
          var list = self.$refs.list;
          if (list) list.scrollTop = list.scrollHeight;
        });
      },

      // ---- rendering ----
      messages: function () {
        var room = this.room();
        return room ? room.messages : [];
      },

      roomCount: function () {
        var n = this.rooms.length;
        return n + (n === 1 ? ' room' : ' rooms');
      },

      totalUnread: function () {
        return this.rooms.reduce(function (sum, r) { return sum + r.unread; }, 0);
      },

      // every loaded message unread and older pages left: there may be more
      badge: function (room) {
        return room.unread + (room.more && room.unread >= room.messages.length ? '+' : '');
      },

      placeholder: function () {
        var room = this.room();
        if (!room) return 'No room';
        return 'Message ' + (room.general ? 'everyone' : room.name) + '…';
      },

      kind: function (m) {
        if (m.sender === null || m.sender === undefined) return 'system';
        var room = this.room();
        return room && room.me !== null && m.sender === room.me ? 'own' : 'other';
      },

      sender: function (m) {
        var room = this.room();
        if (!room) return null;
        var member = room.members.filter(function (x) { return x.id === m.sender; })[0];
        return member ? this.players[member.player] || null : null;
      },

      // the sender's country, in Global only (a DM room is named after the other side already)
      showSender: function (m) {
        var room = this.room();
        return !!room && room.general && this.kind(m) === 'other';
      },

      senderLabel: function (m) {
        var who = this.sender(m);
        return who ? who.country : '?';
      },

      senderKey: function (m) {
        var who = this.sender(m);
        return who ? countryKey(who.country) : null;
      },

      senderName: function (m) {
        var who = this.sender(m);
        return who && who.name ? who.name : '';
      },

      time: function (m) {
        var d = parseTime(m.created_at);
        return d ? pad(d.getHours()) + ':' + pad(d.getMinutes()) : '';
      },

      stamp: function (m) {
        var d = parseTime(m.created_at);
        return d ? d.toLocaleString() : '';
      }
    };
  }

  // ---- registration (see the header comment) ----
  var el = document.getElementById('chat');

  function attach() {
    if (!el || !el.hasAttribute('data-x-data')) return false;
    el.setAttribute('x-data', el.getAttribute('data-x-data'));
    el.removeAttribute('data-x-data');
    return true;
  }

  if (window.Alpine) {
    window.Alpine.data('chat', factory);
    // after Alpine.start, which the build queued as a microtask when its script ran
    queueMicrotask(function () {
      var Alpine = window.Alpine;
      if (!el || !el.hasAttribute('data-x-data')) return;
      Alpine.mutateDom(attach);
      Alpine.initTree(el);
    });
  } else {
    document.addEventListener('alpine:init', function () {
      window.Alpine.data('chat', factory);
      attach();
    });
  }
})();
