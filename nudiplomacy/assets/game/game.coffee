class Game
    constructor: ->
        @country = null
        @_phases = {}
        @colors = {}
        @_currentPhase = 0
        @_nphases = 0
        @_phases_loaded = 0
        @moves = {}
        @moves_mc = {}
        @moves_queue = []
        @orders = {}
        @ready = false
        @_nextPhase = null
        @buildew = null
        #@builds = {}
        @presstype = null
        @scsToWin = 0
        @win = null
        return

    init: (data, phases, orders, callback) ->
        #: load current player
        # @country = data.currentPlayer
        @country = currentPlayer
        #: set participating countries
        @_setCountries(data.players)
        @buildew = data.build_everywhere
        @presstype = data.press_type
        #: load phases
        @_phases["0"] = new Phase(0, null, 2, PHASE_TYPES.pregame, 1920, null, app.env.countries_init, {}, {}, {}, {})
        i = 1
        for phase in phases
            @_phases[i+''] = new Phase(i, phase.id, phase.stage, phase.type, phase.year, phase.season, phase.territories, phase.troops, phase.coasts, phase.dislodged, {})
            i++
        # TEMP
        console.log(phases, orders)
        @_nphases = phases.length + 1
        @_currentPhase = @_nphases-1
        @orders = {}
        # TODO: change ready to endpoint
        if orders.ready
            @ready = true
        @_initOrders(orders.data)
        @_setStartingColors()
        if @phase('last') isnt undefined and @phase('last').type is PHASE_TYPES.won
            @win = data.phases[@_nphases-1].winner
        @_loadPhasesOrders(callback)
        return

    _loadPhasesOrders: (callback) ->
        console.log('expected orders to load', @_nphases)
        for pos, phase of @_phases
            phase._fetchOrders((phase_id, loaded) =>
                @_phases_loaded += 1
                if @_phases_loaded is @_nphases
                    @_completeInit(callback)
                return
            )
        return

    _completeInit: (after) ->
        @_nextPhase = new PhaseNext()
        @_nextPhase._fetchOrders(->
            return
        )
        if @gotOrders()
            @_currentPhase = "next"
        after()
        return

    reload: (data, orders) ->
        @_phases = {}
        for phase in data.phases
            @_phases[i+''] = new Phase(i, phase.id, phase.stage, phase.type, phase.year, phase.season, phase.territories, phase.troops, phase.mc, phase.dislodged, phase.orders)
            i++
        @_nphases = data.phases.length
        @_currentPhase = @_nphases-1
        @_nextPhase = new PhaseNext()
        @orders = {}
        @moves = {}
        @moves_mc = {}
        @moves_queue = []
        @_initOrders(orders.data)
        return

    phase: (id='current') ->
        if id is 'next' or (id is 'current' and @_currentPhase is 'next')
            return @_nextPhase
        if id is 'last'
            return @_phases[@_nphases-1]
        if id isnt 'current'
            return @_phases[id+'']
        return @_phases[@_currentPhase+'']

    isLastPhase: ->
        return @_currentPhase is @_nphases-1

    _setCountries: (ingame) ->
        all = []
        for k, v of app.env.countries
            all.push(k)
        for k in all
            if k not in ingame
                delete app.env.countries[k]
        return

    _initOrders: (orders) ->
        for order in orders
            console.log(order)
            territory = order.territory
            @orders[territory] = order
            if order.type isnt ORDER_TYPES.hold
                if order.type in [ORDER_TYPES.build, ORDER_TYPES.disband]
                    if order.data.troop is TROOP_TYPES.fleet
                        d = type: "build_fleet"
                    else if order.data.troop is TROOP_TYPES.army
                        d = type: "build_army"
                    else
                        d = type: "disband"
                    if order.data.coast isnt undefined
                        d.mc = order.data.coast
                    # @_nextPhase.builds[territory] = d
                else
                    @moves[territory] = order.data
                    @moves[territory].type = ORDER_TYPES.remote_to_internal(order.type)
                    if not @moves[territory].src
                        @moves[territory].src = territory
                    #: add expected movements
                    # if order.type is ORDER_TYPES.support_move and order.data.src not in @_nextPhase.getCountryTroops()
                    #     @moves[order.data.src] =
                    #         from: order.data.src
                    #         dst: order.data.dst
                    #         type: 'move'
                    # if order.type is ORDER_TYPES.move and order.data.through
                    #     for route in order.data.routes
                    #         for convoying_territory in route
                    #             if convoying_territory not in @_nextPhase.getCountryTroops()
                    #                 @moves[convoying_territory] =
                    #                     from: order.data.src
                    #                     dst: order.data.dst
                    #                     type: 'convoy'
        return

    _setStartingColors: ->
        console.log('COLORS', GROUND_COLOR, NEUTRAL_COLOR, SEA_COLOR)
        #:set all terrs to ground color
        color = GROUND_COLOR
        for i of app.env.colors
            @colors[i] = color
        #:set neutrals
        color = NEUTRAL_COLOR
        for i in app.env.neutrals
            @colors[i] = color
        #:set seas
        color = SEA_COLOR
        for i in app.env.seas
            @colors[i] = color
        #:set countries terrs
        cterrs = @phase().territories
        for key, color of app.env.countries
            #for i in app.env.countries_terr[key]
            #for i in @phase().territories[key]
            for i in cterrs[key]
                @colors[i] = color
        return

    loadPhase: (id, drawl=true, drawt=true) ->
        console.log("LoadPhase called")
        console.log(drawl)
        reset_map = true
        old_tcolors = {}
        old_c_terrs = []
        app.ui.setOrdersPhase(id)
        if id is "next" and @isLastPhase()
            reset_map = false
        else
            for key, value of @colors
                old_tcolors[key] = value
            for key, terr_list of @phase().territories
                for terr in terr_list
                    old_c_terrs.push(terr)
        app.ui.setTopButtons("enable", false)
        if id is 0
            app.ui.setTopButtons("disable", "r")
        else if id is @_nphases-1
            if not @gotOrders()
                app.ui.setTopButtons("disable", "f")
        else if id is "next"
            app.ui.setTopButtons("disable", "f")
        app.ui.setPhase(id)
        @_currentPhase = id
        console.log(reset_map)
        if reset_map
            time_start = new Date().getTime()
            #app.SetMap()
            app.screen.change(old_c_terrs, old_tcolors)
            time_end = new Date().getTime()
            time_ex = time_end - time_start
            console.log("ChangeMap time "+time_ex)
        else
            if drawl
                time_start = new Date().getTime()
                app.screen.drawLines()
                app.screen.drawTroops()
                time_end = new Date().getTime()
                time_ex = time_end - time_start
                console.log("DrawLines time "+time_ex)
            if drawt
                app.screen.drawTroops()
            if drawt or drawl
                app.screen.update()
        return

    canBuild: ->
        if not @phase('last').type is PHASE_TYPES.builds
            return 0
        ntroops = @phase('last').getCountryTroops().length
        nsupply = 0
        for i in app.env._supplylist
            if i in @phase('last').territories[@country]
                nsupply++
        #if nsupply < ntroops
        #    return 0
        base = nsupply-ntroops
        builds = (b for b of @phase('next').builds).length
        if base < 0
            return base+builds
        return base-builds

    _addMove: (id, data) ->
        @moves[id] = data
        #if id in (key for key of app.map.troops[app.play.country])
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
        m = @moves_queue.pop(0)

    delMove: (id) ->
        to_delete = []
        to_delete.push(id)
        if @moves[id].type is "move"
            for key, value of @moves
                if value.src is id
                    to_delete.push(key)
        else if @moves[id].type is "support_move"
            ## remove move order if no otherORDER_TYPES.support_move            del_move = true
            for key, value of @moves
                if value.src is @moves[id].src and value.type in ["support_move", "convoy"]
                    if key isnt id
                        del_move = false
                        break
            if del_move
                to_delete.push(@moves[id].src)
        else if @moves[id].type is "convoy"
            to_delete.push(@moves[id].src)
            for key, value of @moves
                if value.src is @moves[id].src and value.type is "convoy"
                    if key not in to_delete
                        to_delete.push(key)
        for i in to_delete
            delete @moves[i]
            #if i in (key for key of app.map.troops[app.play.country])
            if i in @phase().getCountryTroops()
                @delOrder(i)
        return

    hasMove: (id) ->
        movement = @moves[id]
        if movement
            return movement.type
        return false

    _addBuild: (id, data) ->
        @_nextPhase.builds[id] = data
        if data.type is "disband"
            odata = type: "disband"
        else
            odata = type: "build", troop: data.type.split("_")[1]
        if data.mc isnt undefined
            odata['coast'] = data.mc
        console.log(id)
        console.log(odata)
        @addOrder(id, odata)
        return

    addBuild: (id, type, mc=null) ->
        data = type: type
        if mc isnt null
            data['mc'] = mc
        @_addBuild(id, data)
        return

    delBuild: (id) ->
        delete @_nextPhase.builds[id]
        @delOrder(id)
        return

    hasBuild: (id) ->
        build = @_nextPhase.builds[id]
        if build
            return build.type
        return false

    gotOrders: ->
        # TEMP edited
        #return !$.isEmptyObject(@moves)
        return !$.isEmptyObject(@moves) or !$.isEmptyObject(@_nextPhase.builds)

    addOrder: (territory, data) ->
        console.log('addOrder', territory, data)
        @orders[territory].type = ORDER_TYPES.internal_to_remote(data.type)
        if data.type isnt 'build'
            @orders[territory].data.dst = data.dst
        else
            @orders[territory].data.troop = TROOP_TYPES.internal_to_remote(data.troop)
            if app.env.isMCoast(territory) and data.troop is 'fleet'
                @orders[territory].data.coast = data.coast
        #@orders[territory] = type: data.type, to: data.to
        if data.type is 'move'
            if data.through
                @orders[territory].data.through = data.through
                @orders[territory].data.routes = [data.croute]
            if app.env.isMCoast(data.dst)
                #@orders[territory]["mc"] = @moves_mc[territory]
                @orders[territory].data.coast = data.coast
        else if data.type in ['support_move', 'convoy']
            @orders[territory].data.src = data.src
        #country = app.GetCountryByTerr(id)
        #try
        #   @orders_country[country].push(id)
        #catch
        #   @orders_country[country] = []
        #   @orders_country[country].push(id)
        @orders[territory]._changed = true
        app.ui.addOrder(territory, @orders[territory])
        app.ui.autoSave()
        return

    delOrder: (territory) ->
        @orders[territory] =
            id: @orders[territory].id
            territory: territory
            type: ORDER_TYPES.internal_to_remote('hold')
            stage: ORDER_STATES.planned
            data: {}
            _changed: true
        app.ui.delOrder(territory)
        app.ui.autoSave()
        return

    saveOrders: ->
        console.log(@orders)
        for territory, order of @orders
            if order._changed
                app.net.postOrder(order)

window.Game = Game
