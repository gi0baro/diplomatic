
class Phase
    constructor: (@id, @type, @year, @season, @territories, @troops, @mcpos, @dislodged, @orders) ->
        #for key, value of @territories
        #    for i of value
        #        @territories[key][i] = value[i]+''
        @builds = {}
        @_genBuilds()
        #: generate prior phase movements
        @pastMoves = {}
        @_genPastMoves()
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

    _genBuilds: ->
        if not @id
            return
        prior = @id-1
        #for id, odata of app.game._phases[prior+''].orders
        for country, orders of app.game._phases[prior+''].orders
            for id, odata of orders
                if odata.type is "build"
                    if odata.troop is "fleet"
                        @builds[id] = type: "build_fleet"
                    else
                        @builds[id] = type: "build_army"
                    if odata.mc isnt undefined
                        @builds[id]['mc'] = odata.mc
                if odata.type is "disband"
                    @builds[id] = type: "disband"
        return

    _genPastMoves: ->
        console.log(@id)
        if not @id
            return
        if @id is "next"
            prior = app.game._nphases-2
        else
            prior = @id-1
        if prior <= 0
            return
        for country, orders of app.game._phases[prior+''].orders
            for id, odata of orders
                if odata.type not in ["hold", "build"]
                    w = odata
                    w.from = odata.from or id
                    @pastMoves[id] = w
        return

    previous: ->
        if @id is 0
            return null
        return app.game.phase(@id-1)

    next: ->
        if @id is app.game._nphases-1
            next = "next"
        else
            next = id+1
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
        if prev is undefined
            prev =
                type: 'pregame'
                territories: {}
                troops: {}
                mcpos: {}
                dislodged: {}
                listArmies: []
                listFleets: []
        @id = 'next'
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
        if not preGame
            @_genPastMoves()
        @listArmies = prev.listArmies
        @listFleets = prev.listFleets
        return

    previous: ->
        return app.game.phase(app.game._nphases-2)

    next: ->
        return null

window.Phase = Phase
window.PhaseNext = PhaseNext
