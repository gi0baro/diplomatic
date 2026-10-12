#: The game's phases shaped as the engine's raw steps (what `ux.stepChange` and `new Step` consume).
#: A step shows the board at the start of its phase and the orders that led there (its parent phase's
#: orders, loaded lazily by `ensureOrders`); `prev()` gives the step before it.
#:
#:   shaper = new Steps(app, getJSON)       # getJSON(url) -> Promise of the parsed body
#:   steps = shaper.build(mapData, gameData, phases, player, withNext)
#:   shaper.link(steps)
#:   shaper.ensureOrders(step).then (step) -> ...
class Steps
    #: phase type codes of the /api phases rows
    @TYPES: {0: "diplomacy", 1: "retreats", 2: "builds"}

    constructor: (@app, @getJSON) ->
        #: game players as /api/game returns them, set by `build`
        @players = []
        return

    #: pre-game, every phase (orders not loaded yet: null), the virtual next step when `withNext`
    build: (mapData, gameData, phases, player, withNext) ->
        @players = gameData.players
        steps = [@buildPreGameStep(mapData)]
        for phase, i in phases
            steps.push(@buildGameStep(mapData, phase, null, i is phases.length - 1))
        if withNext
            steps.push(@buildNextGameStep(player, steps[steps.length - 1]))
        return steps

    buildGameStep: (mapData, data, orders, isLast) ->
        rv =
            id: data.id
            type: Steps.TYPES[data.type]
            parent: data.parent
            isLast: !!isLast
            supply_centers: {}
            troops: {}
            orders: orders
            data: data
        for obj in @players
            key = obj.country
            owned = (data.territories or {})[key] or []
            troops = (data.troops or {})[key] or {}
            rv.supply_centers[key] = (t for t in owned when t in mapData.supply_centers).length
            rv.troops[key] =
                armies: (troops.armies or []).length
                fleets: (troops.fleets or []).length
        if orders isnt null
            for obj in @players
                rv.orders[obj.country] = orders[obj.country] or []
        return rv

    buildPreGameStep: (mapData) ->
        rv =
            id: null
            type: "pre"
            parent: null
            isLast: false
            supply_centers: {}
            troops: {}
            orders: {}
            data:
                territories: {}
                troops: {}
                coasts: {}
                dislodged: {}
                year: mapData.year
        for obj in @players
            key = obj.country
            rv.data.territories[key] = mapData.init.territories[key] or []
            rv.supply_centers[key] = (mapData.home_centers[key] or []).length
            rv.troops[key] = {armies: 0, fleets: 0}
            rv.orders[key] = []
        return rv

    #: the player's pending orders on top of the last phase (filled in by the page)
    buildNextGameStep: (player, prev) ->
        rv =
            id: null
            type: "next"
            parent: prev.id
            isLast: false
            supply_centers: Object.assign({}, prev.supply_centers)
            troops: Object.assign({}, prev.troops)
            orders: {}
            data:
                type: prev.data.type
                year: prev.data.year
                season: prev.data.season
                territories: prev.data.territories
                troops: prev.data.troops
                coasts: prev.data.coasts
                dislodged: prev.data.dislodged
        rv.orders[player] = []
        return rv

    link: (steps) ->
        for step, i in steps
            do (step, i) ->
                step.idx = i
                step.prev = -> if i > 0 then steps[i - 1] else null
                step.next = -> if i < steps.length - 1 then steps[i + 1] else null
                return
        return steps

    #: the orders that led to a step are its parent phase's (closed, so the API returns them)
    ensureOrders: (step) ->
        return Promise.resolve(step) if not step or step.orders isnt null
        if not step.parent?
            step.orders = {}
            return Promise.resolve(step)
        return @getJSON(@app.net.routes.phase.replace(":ID:", step.parent)).then (data) =>
            orders = (data and data.orders) or {}
            for obj in @players
                orders[obj.country] = orders[obj.country] or []
            step.orders = orders
            return step

window.Steps = Steps
