class Game
    constructor: ->
        @country = null
        @_phases = {}
        @colors = {}
        @_currentPhase = 0
        @_nphases = 0
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

    init: (data, orders) ->
        #: load current player
        @country = data.currentPlayer
        #: set participating countries
        @_setCountries(data.countries)
        @buildew = data.buildew
        @presstype = data.presstype
        #: load phases
        i = 0
        for phase in data.phases
            cstr = i+''
            @_phases[cstr] = new Phase(i, phase.type, phase.year, phase.season, phase.territories, phase.troops, phase.mc, phase.dislodged, phase.orders)
            i++
        @_nphases = data.phases.length
        @_currentPhase = @_nphases-1
        @_nextPhase = new PhaseNext()
        @orders = orders.data
        if orders.ready
            @ready = true
        @_initOrders()
        @_setStartingColors()
        if @gotOrders()
            @_currentPhase = "next"
        if @phase('last').type is "win"
            @win = data.phases[@_nphases-1].winner
        return

    phase: (id='last') ->
        #if id is 'next' or (id is 'last' and @_currentPhase is 'next')
        if id is 'next'
            return @_nextPhase
        if id isnt 'last'
            return @_phases[id+'']
        #return @_phases[@_currentPhase+'']
        return @_phases[@_nphases-1]

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

    _initOrders: ->
        for k, v of @orders
            if v.type isnt "hold"
                if v.type in ["build", "disband"]
                    if v.troop is "fleet"
                        d = type: "build_fleet"
                    else if v.troop is "army"
                        d = type: "build_army"
                    else
                        d = type: "disband"
                    if v.mc isnt undefined
                        d.mc = v.mc
                    @_nextPhase.builds[k] = d
                else
                    @moves[k] = v
                    if not @moves[k].from
                        @moves[k].from = k
        return

    _setStartingColors: ->
        #:set all terrs to ground color
        color = r: 226, g: 198, b: 158
        for i of app.env.colors
            @colors[i] = color
        #:set neutrals
        color = r: 0, g: 0, b: 0
        for i in app.env.neutrals
            @colors[i] = color
        #:set seas
        color = r: 197, g: 223, b: 234
        for i in app.env.seas
            @colors[i] = color
        #:set countries terrs
        cterrs = if @phase().id is 0 then app.env.countries_init else @phase().territories
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
        if not @phase('last').type is "builds"
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

    addMove: (id, type, from, to) ->
        data = type: type, from: from, to: to
        @_addMove(id, data)
        return

    addMoveConvoy: (id, type, from, to, croute) ->
        data = type: type, from: from, to: to, viaConvoy: true, croute: croute
        @_addMove(id, data)
        return

    addMoveMC: (id, type, from, to, mc) ->
        data = data = type: type, from: from, to: to, mc: mc
        @_addMove(id, data)
        return

    enqueueMove: (id, type, from, to) ->
        data = id: id, type: type, from: from, to: to
        @moves_queue.push(data)
        return

    dequeueMove: ->
        m = @moves_queue.pop(0)

    delMove: (id) ->
        to_delete = []
        to_delete.push(id)
        if @moves[id].type is "move"
            for key, value of @moves
                if value.from is id
                    to_delete.push(key)
        else if @moves[id].type is "sup_move"
            ## remove move order if no other sup_move
            del_move = true
            for key, value of @moves
                if value.from is @moves[id].from and value.type in ["sup_move", "convoy"]
                    if key isnt id
                        del_move = false
                        break
            if del_move
                to_delete.push(@moves[id].from)
        else if @moves[id].type is "convoy"
            to_delete.push(@moves[id].from)
            for key, value of @moves
                if value.from is @moves[id].from and value.type is "convoy"
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
            odata["mc"] = data.mc
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

    addOrder: (id, data) ->
        @orders[id]["type"] = data.type
        if data.type isnt "build"
            @orders[id]["to"] = data.to
        else
            @orders[id]["troop"] = data.troop
            if app.env.isMCoast(id) and data.troop is "fleet"
                @orders[id]["mc"] = data.mc
        #@orders[id] = type: data.type, to: data.to
        if data.type is "move"
            if data.viaConvoy
                @orders[id]["viaConvoy"] = data.viaConvoy
                @orders[id]["convoy_route"] = data.croute
            if app.env.isMCoast(data.to)
                #@orders[id]["mc"] = @moves_mc[id]
                @orders[id]["mc"] = data.mc
        else if data.type in ["sup_move", "convoy"]
            @orders[id]["from"] = data.from
        #country = app.GetCountryByTerr(id)
        #try
        #   @orders_country[country].push(id)
        #catch
        #   @orders_country[country] = []
        #   @orders_country[country].push(id)
        app.ui.addOrder(id, @orders[id])
        app.ui.autoSave()
        return

    delOrder: (id) ->
        @orders[id] = type: "hold"
        app.ui.delOrder(id)
        app.ui.autoSave()
        return

window.Game = Game
