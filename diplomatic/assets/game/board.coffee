#: The board: the engine's renderer on the inline SVG (replaces the canvas `screen.coffee`).
#:
#: Same contract as the old Screen (called through `app.screen` by game, interactions, main):
#: `init`, `change`, `drawLines`, `drawTroops`, `markTerritory`, `offTerritory`, `onTerritory`,
#: `register_callbacks`, and the no-ops `buildElements` and `update` (the SVG is live DOM, there is
#: no frame to push). What to draw is the old walk over the game state (screen.coffee's `drawTroops`
#: and `newLine`); how to draw it is the mockup (docs/design/: element structure, stylesheet,
#: geometry through static/js/geometry.js and viewBox.js).
#:
#: The page owns `svg#map` (the variant's SVG inlined server-side, its <style> dropped: the page's
#: stylesheet styles it). Province identity in the engine is the row id; the SVG speaks names
#: (`env.ids` maps them back).

SVGNS = "http://www.w3.org/2000/svg"
#: glyphs, in the mockup's glyph units (scaled by --kg through the .kg groups)
HEAD = "M0 0L-11 -5.5L-8 0L-11 5.5Z"
RHEAD = "M0 0L-10 -5.5L-7 0L-10 5.5ZM-9 0L-19 -5.5L-16 0L-19 5.5Z"
FLEET = "M0 10L10 -7.5L-10 -7.5Z"
SC_PATH = "M0 -5.5L5.5 0L0 5.5L-5.5 0Z"
PLUS = "M-3 0H3M0 -3V3"
CROSS = "M-7 -7L7 7M7 -7L-7 7"
#: dislodged offset in glyph units: the same value as `.unit.dislodged .off` in the stylesheet
DIS_OFF = [22, 20]
#: province codes sit this far under the anchor (glyph units, in the .kf group): 8.5 x preset + 14.5
LABEL_Y = 23
#: an outgoing order layer / unit is removed after its fade-out (CSS: .3 s layers, .45 s units)
FADE_MS = 800
#: when viewing the virtual "next" step, also draw the orders that led to it (the old board drew them
#: grey). The design shows only the player's own orders in the current phase, so they are off; those
#: orders are the history of the step before.
SHOW_PAST_ON_NEXT = false


octagon = (r) ->
    pts = for i in [0...8]
        a = Math.PI / 8 + i * Math.PI / 4
        "#{(r * Math.cos(a)).toFixed(1)},#{(r * Math.sin(a)).toFixed(1)}"
    pts.join(" ")


class Board
    constructor: (@app) ->
        @callbacks =
            update: ->
                return
            after_init: ->
                return
        @svg = null
        @view = null
        @_kg = 1
        @provinces = {}     # id -> <g data-province>
        @anchors = {}       # id -> [x, y]
        @coastAnchors = {}  # id -> {coast name: [x, y]}
        @centers = {}       # id -> [x, y]
        @scs = {}           # id -> path.sc
        @labels = {}        # id -> text.lbl
        @units = {}         # unit key -> g.unit
        @groups = {}        # layer groups appended after .provinces
        @_layer = null      # {step, under, over}: the order layer of the displayed step
        @_troopsStep = null # the step the units were last drawn for (unit glides)
        return

    #: kept for the contract: there are no sprites any more
    buildElements: ->
        return

    #: `update` is accepted and never called (no frame); `after_init` runs at the end of `init`
    register_callbacks: (update, after_init) ->
        @callbacks.update = update if update
        @callbacks.after_init = after_init if after_init
        return

    init: ->
        @svg = document.getElementById("map")
        @_indexProvinces()
        @_buildLayers()
        @_buildSupplyCenters()
        @_buildLabels()
        @view = ViewBox.attach(@svg, onChange: (level) => @_zoomed(level))
        @_kg = @view.relayout()
        @change()
        @callbacks.after_init()
        return

    #: nothing to push: the SVG is live DOM
    update: ->
        return

    # ------------------------------------------------------------------ setup

    _el: (tag, attrs={}, parent=null) ->
        el = document.createElementNS(SVGNS, tag)
        for key, value of attrs
            el.setAttribute(key, value) if value?
        parent.appendChild(el) if parent
        return el

    #: a glyph host: positioned in map units, drawn in glyph units inside the scaled .kg group
    _at: (parent, xy, cls="kg") ->
        g = @_el("g", {transform: "translate(#{xy[0].toFixed(1)},#{xy[1].toFixed(1)})"}, parent)
        return @_el("g", {class: cls}, g)

    _point: (circle) ->
        return [parseFloat(circle.getAttribute("cx")), parseFloat(circle.getAttribute("cy"))]

    _indexProvinces: ->
        for g in @svg.querySelectorAll(".provinces g[data-province]")
            id = @app.env.ids[g.getAttribute("data-province")]
            continue unless id?
            g.setAttribute("data-id", id)
            @provinces[id] = g
            for c in g.querySelectorAll("circle.anchor")
                coast = c.getAttribute("data-coast")
                if coast
                    @coastAnchors[id] ?= {}
                    @coastAnchors[id][coast] = @_point(c)
                else
                    @anchors[id] = @_point(c)
            center = g.querySelector("circle.center")
            @centers[id] = @_point(center) if center
        return

    #: the mockup's layer order, after the provinces
    _buildLayers: ->
        for name in ["scs", "labels", "orders-under", "units", "orders-over"]
            @groups[name] = @_el("g", {class: name}, @svg)
        return

    _buildSupplyCenters: ->
        for id in @app.env._supplylist
            xy = @centers[id] or @anchors[id]
            continue unless xy
            g = @_el("g", {transform: "translate(#{xy[0]},#{xy[1]})"}, @groups.scs)
            @scs[id] = @_el("path", {class: "sc kg", "data-id": id, d: SC_PATH}, g)
        return

    _buildLabels: ->
        for id, code of @app.env.codes
            xy = @anchors[id]
            continue unless xy and code
            kind = @provinces[id]?.getAttribute("data-kind") or ""
            g = @_el("g", {transform: "translate(#{xy[0]},#{xy[1]})"}, @groups.labels)
            text = @_el("text", {class: "lbl kf #{kind}".trim(), "data-id": id, y: LABEL_Y}, g)
            text.textContent = code
            @labels[id] = text
        return

    # ------------------------------------------------------------------ positions

    #: anchor of a province, or of one of its coasts (coast: index in env.coastNames[id])
    _anchor: (id, coast=null) ->
        if coast? and @app.env.isMCoast(id)
            name = (@app.env.coastNames[id] or [])[coast]
            xy = @coastAnchors[id]?[name] if name?
            return xy if xy
        return @anchors[id] or @centers[id] or null

    # ------------------------------------------------------------------ zoom

    _zoomed: (level) ->
        @_relayout()
        document.dispatchEvent(new CustomEvent("board:zoom", detail: {level: level}))
        return

    #: screen-constant annotations: re-run the order geometry with the current glyph scale
    _relayout: ->
        return unless @view
        @_kg = @view.relayout()
        for el in @svg.querySelectorAll(".order")
            @_layoutOrder(el) if el._geo
        return

    _layoutOrder: (el) ->
        res = Geometry.layout(el._geo, @_kg, DIS_OFF)
        for p in el.querySelectorAll(".ln, .flow")
            p.setAttribute("d", res.d)
        if res.head
            hd = el.querySelector(".hd")
            if hd
                h = res.head
                hd.setAttribute("transform", "translate(#{h.x.toFixed(1)},#{h.y.toFixed(1)}) rotate(#{h.angle.toFixed(1)})")
        return

    # ------------------------------------------------------------------ ownership and highlights

    _getTerritories: ->
        if @app.game.phase().type is "pre"
            rv = {}
            for key of @app.env.countries
                rv[key] = []
                for terr in (@app.env.countries_init[key] or [])
                    rv[key].push(terr)
            return rv
        return @app.game.phase().territories

    #: data-owner on the province, its supply centre and its code; the fill comes from the stylesheet
    _applyOwners: (territories) ->
        owners = {}
        for country, list of territories
            continue unless @app.env.countries[country]?
            key = @app.env.countryKey(country)
            for id in (list or [])
                owners[id] = key
        for collection in [@provinces, @scs, @labels]
            for id, el of collection
                if owners[id]
                    el.setAttribute("data-owner", owners[id])
                else
                    el.removeAttribute("data-owner")
        return

    change: ->
        @_applyOwners(@_getTerritories())
        @drawTroops()
        @drawLines()
        @markActionable()
        @update()
        return

    #: valid target of the order being built (interactions): the design's pulsating highlight;
    #: `kind` (dest, convoy, support, source) is kept as data-hint for styling, all look the same for now
    markTerritory: (id, kind) ->
        g = @provinces[id]
        return unless g
        g.classList.add("target")
        g.setAttribute("data-hint", kind)
        g.parentNode.appendChild(g)
        @svg.classList.add("picking")
        return

    offTerritory: (id) ->
        g = @provinces[id]
        return unless g
        g.classList.remove("selected", "target")
        g.removeAttribute("data-hint")
        @svg.classList.remove("picking") unless @svg.querySelector(".provinces g.target")
        return

    #: provinces the player can act on in the viewed step get `act` (hover highlight, pointer cursor)
    markActionable: ->
        can = @app.act?.canSelect
        for id, g of @provinces
            on_ = if can then can.call(@app.act, id) else false
            g.classList.toggle("act", !!on_)
        return

    onTerritory: (id) ->
        g = @provinces[id]
        return unless g
        g.classList.add("selected")
        #: raised above its neighbours so their borders do not paint over the selection edge
        g.parentNode.appendChild(g)
        return

    # ------------------------------------------------------------------ order layers

    #: the order layer of the displayed step: a new one per step (the old one fades out, the new one
    #: fades in), redrawn in place while the step stays the same (order entry)
    _layerFor: (step) ->
        return @_layer if @_layer and @_layer.step is step
        if @_layer
            old = @_layer
            old.under.classList.remove("on")
            old.over.classList.remove("on")
            setTimeout (->
                for gone in [old.under, old.over]
                    gone.parentNode?.removeChild(gone)
                return
            ), FADE_MS
        cls = if step.id is "next" then "cur" else "hist"
        under = @_el("g", {class: "orders #{cls}", "data-layer": cls}, @groups["orders-under"])
        over = @_el("g", {class: "orders #{cls}", "data-layer": cls}, @groups["orders-over"])
        under.getBoundingClientRect()  # flush styles: the .on below is a transition, not the first state
        under.classList.add("on")
        over.classList.add("on")
        @_layer = {step: step, under: under, over: over}
        return @_layer

    _clearKind: (layer, kind) ->
        for g in [layer.under, layer.over]
            for el in g.querySelectorAll(":scope > [data-k=#{kind}]")
                g.removeChild(el)
        return

    _orderGroup: (parent, type, country, failed, kind) ->
        attrs =
            class: "order #{type}" + (if failed then " failed" else "")
            "data-k": kind
        attrs["data-power"] = @app.env.countryKey(country) if country
        return @_el("g", attrs, parent)

    _line: (g) ->
        @_el("path", {class: "ln"}, g)
        @_el("path", {class: "flow"}, g)
        return

    _head: (g, d) ->
        hd = @_el("g", {class: "hd"}, g)
        kg = @_el("g", {class: "kg"}, hd)
        @_el("path", {class: "head", d: d}, kg)
        return

    _place: (g, geo) ->
        g._geo = geo
        @_layoutOrder(g)
        return

    # ------------------------------------------------------------------ units

    #: territory -> country, from orders grouped by country
    _orderCountries: (orders) ->
        rv = {}
        for country, list of (orders or {})
            for o in (list or [])
                rv[o.territory] = country
        return rv

    #: the country of the unit standing in a territory; a dislodged unit shares its territory with its
    #: attacker, `dislodged` says which one is wanted
    _unitCountry: (step, id, dislodged=false) ->
        return null unless step
        found = null
        for country, troops of (step.troops or {})
            for type, list of troops
                if id in (list or [])
                    isDis = id in (step.dislodged?[country] or [])
                    return country if isDis is dislodged
                    found ?= country
        return found

    #: units that moved between two adjacent steps keep their element, re-keyed, so they glide
    _unitRenames: (old, cur) ->
        return null unless old and cur and old isnt cur
        return null if old.id is "next" or cur.id is "next"
        if cur.prev and cur.prev.id is old.id
            orders = cur.orders
            forward = true
        else if old.prev and old.prev.id is cur.id
            orders = old.orders
            forward = false
        else
            return null
        rv = {}
        for country, list of (orders or {})
            key = @app.env.countryKey(country)
            for o in (list or [])
                continue unless o.type in [ORDER_TYPES.move, ORDER_TYPES.retreat]
                continue unless o.stage is ORDER_STATES.successful and o.data?.dst?
                src = "u-#{key}-#{o.territory}"
                dst = "u-#{key}-#{o.data.dst}"
                if forward then rv[src] = dst else rv[dst] = src
        return rv

    _rekey: (renames) ->
        return unless renames
        moved = {}
        for from, to of renames
            if @units[from]
                moved[to] = @units[from]
                delete @units[from]
        for key, el of moved
            @_retire(@units[key]) if @units[key]
            el.setAttribute("data-unit", key)
            @units[key] = el
        return

    _retire: (el) ->
        return unless el
        el.classList.add("gone")
        setTimeout (-> el.parentNode?.removeChild(el)), FADE_MS
        return

    _unit: (key, country, fleet) ->
        el = @units[key]
        if not el
            el = @_el("g", {class: "unit gone", "data-unit": key})
            kg = @_el("g", {class: "kg"}, el)
            @_el("line", {class: "dis-tether", x1: 0, y1: 0, x2: DIS_OFF[0] - 7, y2: DIS_OFF[1] - 6}, kg)
            el._off = @_el("g", {class: "off"}, kg)
            @_el("circle", {class: "dis", r: 18}, el._off)
            el._fresh = true
            @units[key] = el
        el.setAttribute("data-power", @app.env.countryKey(country))
        kind = if fleet then "fleet" else "army"
        if el._kind isnt kind
            el._body.parentNode.removeChild(el._body) if el._body
            if fleet
                el._body = @_el("path", {class: "body", d: FLEET}, el._off)
            else
                el._body = @_el("circle", {class: "body", r: 8.5}, el._off)
            el.classList.remove("army", "fleet")
            el.classList.add(kind)
            el._kind = kind
        return el

    drawTroops: ->
        return unless @svg
        step = @app.game.phase()
        @_rekey(@_unitRenames(@_troopsStep, step))
        @_troopsStep = step
        seen = {}
        for country, troops of (step.troops or {})
            dislodged = step.dislodged?[country] or []
            key = @app.env.countryKey(country)
            for type, tlist of troops
                fleet = type is "fleets"
                for id in (tlist or [])
                    isDis = id in dislodged
                    if fleet and @app.env.isMCoast(id)
                        #: a dislodged fleet stands where it was before (its coast may now be the attacker's)
                        mc_pos = if isDis then (step.prev?.mcpos?[id] ? step.mcpos?[id]) else step.mcpos?[id]
                        xy = @_anchor(id, mc_pos)
                    else
                        xy = @_anchor(id)
                    continue unless xy
                    ukey = "u-#{key}-#{id}"
                    seen[ukey] = true
                    el = @_unit(ukey, country, fleet)
                    el.style.transform = "translate(#{xy[0]}px, #{xy[1]}px)"
                    el.classList.toggle("dislodged", isDis)
                    if el._fresh
                        el._fresh = false
                        @groups.units.appendChild(el)
                        el.getBoundingClientRect()  # flush: fade in from the new position, no glide
                    el.classList.remove("gone")
        for ukey, el of @units
            continue if seen[ukey]
            delete @units[ukey]
            @_retire(el)
        @_drawBuilds(step)
        return

    _buildCountry: (step, tid) ->
        return @app.game.country if step.id is "next"
        for country, list of (step.orders or {})
            for o in (list or [])
                if o.territory is tid and o.type in [ORDER_TYPES.build, ORDER_TYPES.disband]
                    return country
        return @_unitCountry(step.prev, tid) or step.getCountryByTerritory(tid) or null

    #: build ghosts (under the units) and disband marks (over them)
    _drawBuilds: (step) ->
        layer = @_layerFor(step)
        @_clearKind(layer, "build")
        builds = if step.id is "next" then @app.game.builds else step.builds
        for tid, tdata of (builds or {})
            coast = null
            if tdata.type in ["build_fleet", "disband"] and @app.env.isMCoast(tid)
                coast = if tdata.type is "build_fleet" then tdata.coast else step.prev?.mcpos?[tid]
            xy = @_anchor(tid, coast)
            continue unless xy
            country = @_buildCountry(step, tid)
            if tdata.type is "disband"
                g = @_orderGroup(layer.over, "disband", country, false, "build")
                host = @_at(g, xy)
                if country and tid in (step.dislodged?[country] or [])
                    host = @_el("g", {transform: "translate(#{DIS_OFF[0]},#{DIS_OFF[1]})"}, host)
                @_el("circle", {class: "dring", r: 17}, host)
                @_el("path", {class: "x", d: CROSS}, host)
            else if tdata.type in ["build_army", "build_fleet"]
                g = @_orderGroup(layer.under, "build", country, false, "build")
                host = @_at(g, xy)
                @_el("circle", {class: "pulse", r: 22}, host)
                if tdata.type is "build_fleet"
                    @_el("path", {class: "ghost", d: FLEET}, host)
                else
                    @_el("circle", {class: "ghost", r: 8.5}, host)
                badge = @_el("g", {transform: "translate(12,-12)"}, host)
                @_el("circle", {class: "plusbg", r: 5.5}, badge)
                @_el("path", {class: "plus", d: PLUS}, badge)
        return

    # ------------------------------------------------------------------ orders

    drawLines: ->
        return unless @svg
        step = @app.game.phase()
        layer = @_layerFor(step)
        @_clearKind(layer, "line")
        entries = []
        if step.id isnt "next" or SHOW_PAST_ON_NEXT
            #: past orders: the orders that led to the viewed step, read against the step before it
            prev = step.prev or step
            countries = @_orderCountries(if step.id is "next" then step.prev?.orders else step.orders)
            ctx =
                time: "past"
                mcpos: prev.mcpos or {}
                isFleet: (i) -> prev.isFleet(i)
                moves: step.pastMoves
            for id, obj of step.pastMoves
                country = countries[id] or @_unitCountry(prev, id)
                entries.push(@_entry(step, ctx, id, obj, obj.success or false, country))
        if step.id is "next"
            #: pending orders; moves of units that are not the player's (expected moves) read as failed
            mine = step.getCountryTroops()
            ctx =
                time: "future"
                mcpos: step.mcpos or {}
                isFleet: (i) -> step.isFleet(i)
                moves: @app.game.moves
            for id, obj of @app.game.moves
                country = @_unitCountry(step, id, obj.type is "retreat") or @app.game.country
                entries.push(@_entry(step, ctx, id, obj, id in mine, country))
        @_drawEntries(layer, step, entries)
        return

    _entry: (step, ctx, id, obj, success, country) ->
        route = obj.croute or obj.routes?[0] or null
        return {
            ctx: ctx
            id: id
            type: obj.type
            src: obj.src or id
            dst: obj.dst
            coast: obj.coast
            through: !!obj.through
            route: if Array.isArray(route) then route else null
            success: success
            country: country
            dis: !!country and id in (step.dislodged?[country] or [])
        }

    #: where an ordering unit stands (a dislodged one as drawTroops draws it)
    _posOf: (step, e, uid, dis=false) ->
        if e.ctx.isFleet(uid) and @app.env.isMCoast(uid)
            mc = if dis then (step.prev?.mcpos?[uid] ? e.ctx.mcpos[uid]) else e.ctx.mcpos[uid]
            return @_anchor(uid, mc)
        return @_anchor(uid)

    _drawEntries: (layer, step, entries) ->
        #: convoy orders are drawn with the army's move they carry: rings on the fleets, path through them
        convoys = {}
        for e in entries when e.type is "convoy"
            k = "#{e.ctx.time}:#{e.src}>#{e.dst}"
            (convoys[k] ?= []).push(e)
        for e in entries
            switch e.type
                when "move"
                    k = "#{e.ctx.time}:#{e.src}>#{e.dst}"
                    fleets = convoys[k] or []
                    delete convoys[k]
                    @_drawMove(layer, step, e, fleets)
                when "support_hold"
                    @_drawSupportHold(layer, step, e)
                when "support_move"
                    @_drawSupportMove(layer, step, e)
                when "retreat"
                    @_drawRetreat(layer, step, e)
        for k, fleets of convoys
            @_drawConvoyOnly(layer, step, fleets)
        return

    #: convoying fleets in route order: the order's route when known, else nearest first from the army
    _chain: (start, ids) ->
        left = (i for i in ids when @anchors[i])
        out = []
        cur = start
        while left.length
            best = 0
            bestD = Infinity
            for i, n in left
                p = @anchors[i]
                d = Math.hypot(p[0] - cur[0], p[1] - cur[1])
                if d < bestD
                    best = n
                    bestD = d
            out.push(left.splice(best, 1)[0])
            cur = @anchors[out[out.length - 1]]
        return out

    _rings: (g, via) ->
        for v in via
            host = @_at(g, @_anchor(v))
            @_el("circle", {class: "cring", r: 17}, host)
        return

    _drawMove: (layer, step, e, fleets) ->
        from = @_posOf(step, e, e.src, e.dis)
        if e.ctx.isFleet(e.src) and @app.env.isMCoast(e.dst)
            to = @_anchor(e.dst, e.coast)
        else
            to = @_anchor(e.dst)
        return unless from and to
        if e.route
            via = (v for v in e.route when @_anchor(v))
        else
            via = @_chain(from, (f.id for f in fleets))
        type = if via.length or e.through then "convoy" else "move"
        g = @_orderGroup(layer.under, type, e.country, not e.success, "line")
        @_line(g)
        @_head(g, HEAD)
        @_rings(g, via)
        @_place(g, {t: "m", p: [from].concat((@_anchor(v) for v in via), [to]), d: (if e.dis then 1 else 0)})
        return

    #: convoy orders whose army move is not in the set: the convoyed move, as far as the fleets know it
    _drawConvoyOnly: (layer, step, fleets) ->
        first = fleets[0]
        from = @_anchor(first.src)
        to = @_anchor(first.dst)
        return unless from and to
        via = @_chain(from, (f.id for f in fleets))
        failed = false
        for f in fleets
            failed = true unless f.success
        g = @_orderGroup(layer.under, "convoy", first.country, failed, "line")
        @_line(g)
        @_head(g, HEAD)
        @_rings(g, via)
        @_place(g, {t: "m", p: [from].concat((@_anchor(v) for v in via), [to]), d: 0})
        return

    _drawSupportHold: (layer, step, e) ->
        s = @_posOf(step, e, e.src, e.dis)
        t = @_posOf(step, e, e.dst)
        return unless s and t
        g = @_orderGroup(layer.under, "support", e.country, not e.success, "line")
        @_line(g)
        host = @_at(g, t)
        @_el("polygon", {class: "oct", points: octagon(19)}, host)
        @_place(g, {t: "sh", s: s, e: t, d: (if e.dis then 1 else 0)})
        return

    _drawSupportMove: (layer, step, e) ->
        s = @_posOf(step, e, e.id, e.dis)
        a = @_posOf(step, e, e.src)
        if e.ctx.isFleet(e.src) and @app.env.isMCoast(e.dst)
            #: the supported fleet's target coast: from its own move, else from the support order
            mc = e.ctx.moves?[e.src]?.coast ? e.coast
            b = @_anchor(e.dst, mc)
        else
            b = @_anchor(e.dst)
        return unless s and a and b
        m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
        g = @_orderGroup(layer.under, "support", e.country, not e.success, "line")
        @_line(g)
        host = @_at(g, m)
        @_el("circle", {class: "knob", r: 5}, host)
        @_place(g, {t: "sm", s: s, m: m, d: (if e.dis then 1 else 0)})
        return

    _drawRetreat: (layer, step, e) ->
        s = @_posOf(step, e, e.src, e.dis)
        if e.ctx.isFleet(e.src) and @app.env.isMCoast(e.dst)
            t = @_anchor(e.dst, e.coast)
        else
            t = @_anchor(e.dst)
        return unless s and t
        g = @_orderGroup(layer.under, "retreat", e.country, not e.success, "line")
        @_line(g)
        @_head(g, RHEAD)
        #: offset start only while the unit still stands dislodged at its source (pending retreats)
        @_place(g, {t: "r", s: s, e: t, d: (if e.dis then 1 else 0)})
        return

window.Board = Board
