class Step
    constructor: (@app, step, prev=true) ->
        console.log('NEW STEP', step)
        @id = if step.type isnt "next" then step.id else "next"
        @type = if step.data.type is undefined then step.type else step.data.type
        @year = if step.id is null then null else step.data.year
        @season = if step.id is null then null else step.data.season
        @territories = step.data.territories or {}
        @troops = step.data.troops or {}
        @mcpos = step.data.coasts or {}
        @dislodged = step.data.dislodged or {}
        @orders = step.orders
        @isLast = step.isLast
        @prev = null
        if prev is true and step.prev() isnt null
            @prev = new Step(@app, step.prev(), false)
        @builds = {}
        @pastMoves = {}
        @listArmies = []
        @listFleets = []
        for key, value of @troops
            for t, l of value
                for i in l
                    if t is "armies"
                        @listArmies.push(i)
                    else
                        @listFleets.push(i)
        @_genPastMoves()
        if step.id isnt "next"
            @_genBuilds()
        return

    _genBuilds: ->
        for country, orders of @orders
            for order in orders
                territory = order.territory
                if order.type is ORDER_TYPES.build
                    if order.data.troop is TROOP_TYPES.fleet
                        @builds[territory] = type: "build_fleet"
                    else
                        @builds[territory] = type: "build_army"
                    if order.data.coast isnt undefined
                        @builds[territory].coast = order.data.coast
                if order.type is ORDER_TYPES.disband
                    @builds[territory] = type: "disband"
        return

    _genPastMoves: ->
        allOrders = if @id is "next" then @prev.orders else @orders
        for country, orders of allOrders
            for order in orders
                territory = order.territory
                if order.type not in [ORDER_TYPES.hold, ORDER_TYPES.build]
                    w = order.data
                    w.src = order.data.src or territory
                    @pastMoves[territory] = w
                    @pastMoves[territory].type = ORDER_TYPES.remote_to_internal(order.type)
                    @pastMoves[territory].success = order.stage is ORDER_STATES.successful
        return

    isArmy: (id) ->
        return id in @listArmies

    isFleet: (id) ->
        return id in @listFleets

    canConvoy: (id) ->
        res = false
        if @isFleet(id) and @app.env.isSea(id)
            links = @app.env.moves.fleets[id]
            for i in links
                if @isArmy(i)
                    res = true
                    break
        return res

    getCountryByTerritory: (id) ->
        for country, list of @territories
            if id in list
                return country
        return false

    getCountryTroops: (country=null) ->
        country = country or @app.game.country
        troops = []
        for ttype, tlist of @troops[country]
            for troop in tlist
                troops.push(troop)
        return troops

window.Step = Step
