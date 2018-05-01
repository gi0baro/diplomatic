
class Phase
    constructor: (@position, @id, @stage, @type, @year, @season, @territories, @troops, @mcpos, @dislodged) ->
        @orders = {}
        @builds = {}
        @pastMoves = {}
        #: shortcuts list for troops by type
        @listArmies = []
        @listFleets = []
        for key, value of @troops
            for t, l of value
                for i in l
                    if t is "armies"
                        @listArmies.push(i)
                    else
                        @listFleets.push(i)
        return

    _fetchOrders: (callback) ->
        console.log('called _fetchOrders for phase', @id, @position, @stage)
        if @id is null
            callback(@id, false)
            return
        previous = app.game.phase(@position - 1)
        if previous.id is null
            callback(@id, false)
            return
        app.net.getOrders(previous, (orders) =>
            @_ordersCallback(orders, callback)
            return
        )
        return

    _ordersCallback: (orders, callback) ->
        for order in orders
            if @orders[order.country] is undefined
                @orders[order.country] = {}
            @orders[order.country][order.territory] = order
        @_genBuilds()
        @_genPastMoves()
        callback(@id, true)
        return


    _genBuilds: ->
        for country, orders of @orders
            for territory, order of orders
                if order.type is ORDER_TYPES.build
                    if order.data.troop is TROOP_TYPES.fleet
                        @builds[territory] = type: "build_fleet"
                    else
                        @builds[territory] = type: "build_army"
                    if order.data.coast isnt undefined
                        @builds[territory]['mc'] = order.data.coast
                if order.type is ORDER_TYPES.disband
                    @builds[territory] = type: "disband"
        return

    _genPastMoves: ->
        for country, orders of @orders
            for territory, order of orders
                if order.type not in [ORDER_TYPES.hold, ORDER_TYPES.build]
                    w = order.data
                    w.src = order.data.src or territory
                    @pastMoves[territory] = w
                    @pastMoves[territory].type = ORDER_TYPES.remote_to_internal(order.type)
        return

    previous: ->
        if @position is 0
            return null
        return app.game.phase(@position - 1)

    next: ->
        if @position is app.game._nphases - 1
            next = "next"
        else
            next = @position + 1
        return app.game.phase(next)

    isArmy: (id) ->
        return id in @listArmies

    isFleet: (id) ->
        return id in @listFleets

    canConvoy: (id) ->
        res = false
        if @isFleet(id) and app.env.isSea(id)
            links = app.env.moves.fleets[id]
            for i in links
                if @isArmy(i)
                    res = true
                    break
        return res

    getCountryByTerritory: (id) ->
        for country, list of @territories
            if id in list
                console.log(country)
                return country
        return false

    getCountryTroops: (country=app.game.country) ->
        troops = []
        for ttype, tlist of @troops[country]
            for troop in tlist
                troops.push(troop)
        return troops


class PhaseNext extends Phase
    constructor: ->
        prev = app.game.phase(app.game._nphases-1)
        @position = 'next'
        @id = null
        @stage = 0
        @type = prev.type
        @year = null
        @season = null
        @territories = prev.territories
        @troops = prev.troops
        @mcpos = prev.mcpos
        @dislodged = prev.dislodged
        @orders = {}
        @builds = {}
        @pastMoves = {}
        @listArmies = prev.listArmies
        @listFleets = prev.listFleets
        return

    previous: ->
        return app.game.phase(app.game._nphases-2)

    next: ->
        return null

    _fetchOrders: (callback) ->
        if preGame
            callback(@id, false)
            return
        @orders = @previous.orders
        @_genBuilds()
        @_genPastMoves()
        callback(@id, true)
        return

window.Phase = Phase
window.PhaseNext = PhaseNext
