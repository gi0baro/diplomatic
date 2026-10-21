class Game
    constructor: (@app) ->
        @country = null
        @steps = {}
        @step =
            territories: {}
            troops: {}
            mcpos: {}
            dislodged: {}
            isLast: false
        @moves = {}
        @builds = {}
        @moves_queue = []
        @orders = {}
        # useless?
        @ready = false
        @buildew = null
        @presstype = null
        @scsToWin = 0
        #: set by the page before launch: the player has the virtual "next" step (can give orders now)
        @canOrder = false
        #: game players as /api/game returns them ({id, country, name, is_ready, is_active})
        @players = []
        @win = null
        @orderMethod = () -> return
        @movePhaseToNext = () -> return
        #: saving: 3 s debounce after the last change; one save in flight at a time
        @_saveTimer = null
        @_saving = null
        @_saveAgain = false
        @_saveGen = 0
        @_emitQueued = false
        #: live updates of the players (ready / join), relayed by the game socket
        document.addEventListener "game:players", (e) =>
            @_playerUpdate(e.detail or {})
            return
        return

    bind: (stepNextMethod) ->
        @movePhaseToNext = stepNextMethod

    init: (data, player, orders, isPlayerReady) ->
        #: load current player
        @country = player
        @players = ((Object.assign({}, p) for p in (data.players or [])))
        #: set participating countries
        @_setCountries(data.players)
        @buildew = data.build_everywhere
        @presstype = data.press_type
        @orders = {}
        @ready = isPlayerReady
        @_initOrders(orders)
        return

    resetPhase: (data, orders, isPlayerReady, canOrder) ->
        lost = (order for territory, order of @orders when order._changed).length
        @_saveGen++
        clearTimeout(@_saveTimer) if @_saveTimer isnt null
        @_saveTimer = null
        @_saving = null
        @_saveAgain = false
        @orders = {}
        @moves = {}
        @builds = {}
        @moves_queue = []
        @steps = {}
        @ready = !!isPlayerReady
        @canOrder = !!canOrder
        @players = ((Object.assign({}, p) for p in (data.players or [])))
        @_initOrders(orders)
        return lost

    setStep: (step) ->
        oldStep = @step
        @step = step
        if @app.launched
            @loadStep(@step, oldStep)

    #: the displayed step
    phase: ->
        return @step

    isLastPhase: ->
        return @step.isLast

    _setCountries: (players) ->
        all = []
        countries = players.map (obj) ->
            return obj.country
        for k, v of @app.env.countries
            all.push(k)
        for k in all
            if k not in countries
                delete @app.env.countries[k]
        return

    _initOrders: (orders) ->
        for order in orders
            territory = order.territory
            order.data = order.data or {}
            @orders[territory] = order
            if order.type isnt ORDER_TYPES.hold
                if order.type in [ORDER_TYPES.build, ORDER_TYPES.disband]
                    if order.data.troop is TROOP_TYPES.fleet
                        internalType = "build_fleet"
                    else if order.data.troop is TROOP_TYPES.army
                        internalType = "build_army"
                    else
                        internalType = "disband"
                    #: copies: the internal type and src must not leak into the server row's data
                    @builds[territory] = Object.assign({}, order.data)
                    @builds[territory].type = internalType
                else
                    @moves[territory] = Object.assign({}, order.data)
                    @moves[territory].type = ORDER_TYPES.remote_to_internal(order.type)
                    if not @moves[territory].src
                        @moves[territory].src = territory
        return

    loadStep: (step, oldStep, drawl=true, drawt=true) ->
        reset_map = not (step.id is "next" and oldStep.isLast)
        if reset_map
            @app.screen.change()
        else
            if drawl
                @app.screen.drawLines()
                @app.screen.drawTroops()
            if drawt
                @app.screen.drawTroops()
            if drawt or drawl
                @app.screen.update()
        return

    #: supply centres minus units of the player in the viewed step: > 0 builds, < 0 disbands
    buildBalance: ->
        ntroops = @phase().getCountryTroops().length
        owned = @phase().territories[@country] or []
        nsupply = 0
        for i in @app.env._supplylist
            if i in owned
                nsupply++
        return nsupply - ntroops

    canBuild: ->
        if @phase().type isnt PHASE_TYPES.builds
            return 0
        base = @buildBalance()
        builds = (b for b of @builds).length
        if base < 0
            return base+builds
        return base-builds

    _addMove: (id, data) ->
        @moves[id] = data
        if id in @phase().getCountryTroops()
            @addOrder(id, data)
        return

    addMove: (id, type, src, dst) ->
        data = type: type, src: src, dst: dst
        @_addMove(id, data)
        return

    addMoveConvoy: (id, type, src, dst, croute) ->
        data = type: type, src: src, dst: dst, through: true, croute: croute
        @_addMove(id, data)
        return

    addMoveMC: (id, type, src, dst, coast) ->
        data = data = type: type, src: src, dst: dst, coast: coast
        @_addMove(id, data)
        return

    enqueueMove: (id, type, src, dst) ->
        data = id: id, type: type, src: src, dst: dst
        @moves_queue.push(data)
        return

    dequeueMove: ->
        return @moves_queue.shift()

    delMove: (id) ->
        to_delete = []
        to_delete.push(id)
        if @moves[id].type is "move"
            for key, value of @moves
                if value.src is id
                    to_delete.push(key)
        else if @moves[id].type is "convoy"
            to_delete.push(@moves[id].src)
            for key, value of @moves
                if value.src is @moves[id].src and value.type is "convoy"
                    if key not in to_delete
                        to_delete.push(key)
        for i in to_delete
            delete @moves[i]
            if i in @phase().getCountryTroops()
                @delOrder(i)
        return

    hasMove: (id) ->
        movement = @moves[id]
        if movement
            return movement.type
        return false

    _addBuild: (id, data) ->
        @builds[id] = data
        if data.type is "disband"
            order = type: "disband"
        else
            order = type: "build", troop: data.type.split("_")[1]
        if data.coast isnt undefined
            order.coast = data.coast
        @addOrder(id, order)
        return

    addBuild: (id, type, coast=null) ->
        data = type: type
        if coast isnt null
            data.coast = coast
        @_addBuild(id, data)
        return

    delBuild: (id) ->
        delete @builds[id]
        @delOrder(id)
        return

    hasBuild: (id) ->
        build = @builds[id]
        if build
            return build.type
        return false

    gotOrders: ->
        return !isObjectEmpty(@moves) or !isObjectEmpty(@builds)

    addOrder: (territory, data) ->
        order = @orders[territory]
        if not order
            console.warn("no order row for", territory)
            return
        order.type = ORDER_TYPES.internal_to_remote(data.type)
        #: a fresh payload: keys of the previous order type must not survive
        order.data = {}
        if data.type isnt 'build'
            order.data.dst = data.dst if data.dst?
        else
            order.data.troop = TROOP_TYPES.internal_to_remote(data.troop)
            if @app.env.isMCoast(territory) and data.troop is 'fleet'
                order.data.coast = data.coast
        if data.type in ['move', 'retreat']
            if data.type is 'move' and data.through
                order.data.through = data.through
                order.data.routes = [data.croute]
            if @app.env.isMCoast(data.dst) and data.coast?
                order.data.coast = data.coast
        else if data.type in ['support_move', 'convoy']
            order.data.src = data.src
        @_touch(order)
        return

    delOrder: (territory) ->
        order = @orders[territory]
        return unless order
        order.type = ORDER_TYPES.internal_to_remote('hold')
        order.data = {}
        @_touch(order)
        return

    #: an order row changed: pending until saved (_rev tells a save in flight that it went stale)
    _touch: (order) ->
        order._changed = true
        order._rev = (order._rev or 0) + 1
        @_scheduleSave()
        @_emitOrders()
        return

    # ------------------------------------------------------------------ events

    _emit: (name, detail) ->
        document.dispatchEvent(new CustomEvent(name, {detail: detail}))
        return

    #: `orders:changed`, once per tick however many rows a mutation touched (delMove cascades)
    _emitOrders: ->
        return unless @app.launched
        return if @_emitQueued
        @_emitQueued = true
        Promise.resolve().then =>
            @_emitQueued = false
            @_emit("orders:changed", @ordersState())
            return
        return

    ordersState: ->
        step = @phase()
        orders = @orderList(step)
        unsaved = false
        for o in orders
            unsaved = true if o.pending
        unsaved = true if not unsaved and @_hasChanged()
        return {
            orders: orders
            phase: {id: step.id, type: step.type, isNext: step.id is "next"}
            editable: step.id is "next" and not @ready
            unsaved: unsaved
            saving: @_saving isnt null
            ready: @ready
        }

    _hasChanged: ->
        for territory, order of @orders
            return true if order._changed
        return false

    # ------------------------------------------------------------------ saving and ready

    _scheduleSave: ->
        clearTimeout(@_saveTimer) if @_saveTimer isnt null
        @_saveTimer = setTimeout (=>
            @_saveTimer = null
            @saveNow()
            return
        ), 3000
        return

    #: save every changed row now; resolves {saved, errors}. While a save is in flight, another one is
    #: chained after it (rows changed meanwhile keep _changed and go in the next round).
    saveNow: ->
        if @_saveTimer isnt null
            clearTimeout(@_saveTimer)
            @_saveTimer = null
        if @_saving isnt null
            @_saveAgain = true
            return @_saving
        changed = (order for territory, order of @orders when order._changed)
        if not changed.length
            return Promise.resolve({saved: 0, errors: {}})
        @_emit("orders:saving", {count: changed.length})
        gen = @_saveGen
        saving = @app.net.saveOrders(changed).then (res) =>
            #: after a phase change @_saving may already be a newer save's
            @_saving = null if @_saving is saving
            #: the phase changed meanwhile: drop the result
            return res if gen isnt @_saveGen
            if not isObjectEmpty(res.errors)
                @_emit("orders:error", res.errors)
            else if not @_hasChanged()
                #: "saved" only when nothing is pending: rows changed during the save wait for the next round
                @_emit("orders:saved", res)
            @_emitOrders()
            if @_saveAgain
                @_saveAgain = false
                @_scheduleSave() if @_hasChanged()
            return res
        @_saving = saving
        return @_saving

    #: kept for older callers
    saveOrders: ->
        return @saveNow()

    #: pending orders are saved first (the server refuses orders from a ready player); a failed save
    #: keeps the player not ready
    setReady: (ready) ->
        ready = !!ready
        none = {saved: 0, errors: {}}
        if ready
            #: twice: a save already in flight resolves with its own round, rows changed meanwhile need another
            before = @saveNow().then (res) =>
                return res if not isObjectEmpty(res.errors) or not @_hasChanged()
                return @saveNow()
        else
            before = Promise.resolve(none)
        return before.then (res) =>
            if ready and not isObjectEmpty(res.errors)
                @app.ux.alert("Some orders could not be saved: you are not ready yet.", true, 6)
                @_emit("game:ready", @ready)
                return @ready
            return @app.net.setReady(ready).then (r) =>
                if r and r.status is "ok"
                    @_applyReady(!!r.data)
                else
                    @app.ux.alert("Could not change the ready state.", true, 6)
                    @_emit("game:ready", @ready)
                return @ready
        .catch (err) =>
            console.error(err)
            @app.ux.alert("Could not change the ready state.", true, 6)
            @_emit("game:ready", @ready)
            return @ready

    _applyReady: (ready) ->
        @ready = ready
        #: a ready player gives no orders: drop whatever was being built
        @app.act.cancel() if ready and @app.act.current isnt "none"
        @_emit("game:ready", @ready)
        @_emitOrders()
        @app.screen.markActionable()
        return

    _playerUpdate: (data) ->
        return unless data.country
        player = null
        for p in @players
            player = p if p.country is data.country
        if player is null
            player = {country: data.country, name: null, is_ready: false, is_active: false}
            @players.push(player)
        player.is_ready = data.is_ready if data.is_ready?
        player.is_active = data.is_active if data.is_active?
        #: the same player in another tab
        if data.country is @country and data.is_ready? and !!data.is_ready isnt @ready
            @_applyReady(!!data.is_ready)
        return

    # ------------------------------------------------------------------ orders list

    #: the order kind as the T strings name it (orders.<kind>)
    _orderKind: (order) ->
        if order.type is ORDER_TYPES.build
            return if order.data?.troop is TROOP_TYPES.fleet then "build_fleet" else "build_army"
        return ORDER_TYPES.remote_to_internal(order.type) or "hold"

    _coastText: (tid, coast) ->
        return "" unless coast?
        name = (@app.env.coastNames[tid] or [])[coast]
        return "" unless name
        key = "orders.coasts." + name.toLowerCase()
        text = T.get(key)
        return if text is key then " (" + name.toLowerCase() + " coast)" else text

    orderText: (order) ->
        kind = @_orderKind(order)
        d = order.data or {}
        name = (id) => if id? then (@app.env.names[id] or id) else ""
        coastAt = if kind is "build_fleet" then order.territory else d.dst
        return T.get("orders." + kind)
            .replace(":TERRITORY:", name(order.territory))
            .replace(":SRC:", name(d.src))
            .replace(":DST:", name(d.dst))
            .replace(":THROUGH:", if d.through then T.get("orders.vec.through") else "")
            .replace(":COAST:", @_coastText(coastAt, d.coast))

    _orderRow: (order, country, units, pending) ->
        kind = @_orderKind(order)
        t = order.territory
        unit = null
        if kind is "build_army"
            unit = "army"
        else if kind is "build_fleet"
            unit = "fleet"
        else if units
            unit = if units.isFleet(t) then "fleet" else if units.isArmy(t) then "army" else null
        return {
            id: order.id
            territory: t
            code: @app.env.codes[t] or ""
            name: @app.env.names[t] or t
            text: @orderText(order)
            type: kind
            unit: unit
            country: country
            power: if country then @app.env.countryKey(country) else null
            mine: country is @country
            failed: order.stage is ORDER_STATES.failed
            success: order.stage is ORDER_STATES.successful
            pending: pending and !!order._changed
        }

    #: the orders of a step for the sidebar: the player's pending orders on the virtual "next" step
    #: (holds included), the resolved orders that led to any other step (every power, the player's first)
    orderList: (step=@step) ->
        rows = []
        return rows unless step and @app.launched
        if step.id is "next"
            for territory, order of @orders
                rows.push(@_orderRow(order, @country, step, true))
        else
            units = step.prev or step
            for country, list of (step.orders or {})
                for order in (list or [])
                    rows.push(@_orderRow(order, country, units, false))
        rows.sort (a, b) ->
            return (if a.mine then -1 else 1) if a.mine isnt b.mine
            return (if a.country < b.country then -1 else 1) if a.country isnt b.country
            return a.name.localeCompare(b.name)
        return rows

    #: back to hold (a retreat: back to no order), from the orders panel
    resetOrder: (territory) ->
        return if @ready
        order = @orders[territory]
        return unless order
        @app.act.cancel() if @app.act.current isnt "none"
        if @builds[territory]
            @delBuild(territory)
        else if @moves[territory]
            @delMove(territory)
        else if order.type isnt ORDER_TYPES.hold
            @delOrder(territory)
        else
            return
        @app.screen.drawLines()
        @app.screen.drawTroops()
        return

window.Game = Game
