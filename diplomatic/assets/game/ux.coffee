#: The engine's side of the page: everything the UI has to know leaves as a DOM event on `document`
#: (CustomEvent, payload in `detail`); the page's components listen. The engine knows nothing about the
#: UI but these names:
#:   board:menu {type, territory, name, code, current, coasts, unit, dislodged, country, position, ...menu data}
#:   board:menu-close {type}
#:   board:alert {message, dismissable, autoDismiss}
#:   game:step {index, current, count, label, ...: page info; id, isNext, isCurrent, phaseType, year,
#:              season, supplyCenters, troops}
#: (orders:*, game:ready come from Game; board:launched from App; game:<topic> from Network.)
class UX
    constructor: (@app) ->
        @gamePre = false
        @gameOver = false
        @activeMenu = null
        #: the last game:step detail, for components that start after it was sent
        @lastStep = null
        return

    #: kept for compatibility: menus and alerts are DOM events now, the callbacks are ignored
    configure: ->
        return

    _emit: (name, detail) ->
        document.dispatchEvent(new CustomEvent(name, {detail: detail}))
        return

    launched: (gamePre, gameOver) ->
        @gamePre = gamePre
        @gameOver = gameOver
        #: events dispatched by `Network` from the game socket frames; play.js handles "processed"
        document.addEventListener "game:state", (e) =>
            return if e.detail is "processed"
            @alert("Game changed, reloading in 5 seconds..", false)
            setTimeout (=>
                @app.reload()
            ), 5000
            return
        @afterLaunch()
        return

    afterLaunch: ->
        if @gamePre
            @alert("This is a pre-game phase. The game will start when all the players have been joined.", false)
        return

    #: step: the page's raw step; info: what the page knows about it (index, current, count, label)
    stepChange: (step, info={}) ->
        stepKey = step.id + '_' + step.type
        if @app.game.steps[stepKey] is undefined
            @app.game.steps[stepKey] = new Step(@app, step)
        current = @app.game.steps[stepKey]
        @app.game.setStep(current)
        kind = if typeof current.type is "number" then PHASE_TYPES.remote_to_internal(current.type) else current.type
        isCurrent = if info.index? and info.current? then info.index >= info.current else true
        @lastStep = Object.assign({}, info, {
            id: current.id
            isNext: current.id is "next"
            isCurrent: isCurrent
            phaseType: kind
            year: current.year
            season: current.season
            supplyCenters: step.supply_centers or {}
            troops: step.troops or {}
        })
        @_emit("game:step", @lastStep)
        @app.game._emitOrders()
        return

    _unitAt: (territory) ->
        step = @app.game.phase()
        return "fleet" if step.isFleet(territory)
        return "army" if step.isArmy(territory)
        return null

    menuOpen: (type, data={}) ->
        @activeMenu = type
        t = if data.territory? then data.territory else @app.act.active
        country = @app.game.country
        current = false
        if t?
            current = @app.game.hasMove(t) or @app.game.hasBuild(t) or false
        detail = Object.assign({}, data, {
            type: type
            territory: t
            name: if t? then (@app.env.names[t] or t) else null
            code: if t? then (@app.env.codes[t] or null) else null
            current: current
            coasts: (if t? then @app.env.coastNames[t] else null) or null
            unit: if t? then @_unitAt(t) else null
            dislodged: !!(t? and country and t in (@app.game.phase().dislodged[country] or []))
            country: country
            power: if country then @app.env.countryKey(country) else null
        })
        @_emit("board:menu", detail)
        return

    menuClose: (type) ->
        @_emit("board:menu-close", {type: type})
        @activeMenu = null
        return

    relevantActionMenuOpen: (position, territory) ->
        if @app.game.phase().type is PHASE_TYPES.diplomacy
            canConvoy = @app.game.phase().canConvoy(territory)
            @menuOpen('territory', {position: position, canConvoy: canConvoy, territory: territory})
        if @app.game.phase().type is PHASE_TYPES.builds
            #: an own unit can be disbanded when the country has more units than supply centres;
            #: builds go on empty centres (the select check only lets those through)
            own = territory in @app.game.phase().getCountryTroops()
            canBuild = not own
            canBuildFleet = canBuild and @app.env.isCoast(territory)
            canDisband = own and @app.game.buildBalance() < 0
            @menuOpen('build', {position: position, canBuild: canBuild, canDisband: canDisband, canBuildFleet: canBuildFleet, territory: territory})
        if @app.game.phase().type is PHASE_TYPES.retreats
            @menuOpen('retreat', {position: position, territory: territory})
        return

    relevantActionMenuClose: () ->
        if @activeMenu isnt null
            @menuClose(@activeMenu)
        return

    alert: (message, dismissable=true, autoDismiss=null) ->
        @_emit("board:alert", {message: message, dismissable: dismissable, autoDismiss: autoDismiss})
        return

window.UX = UX
