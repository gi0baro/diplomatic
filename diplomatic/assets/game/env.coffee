
class Environment
    constructor: (@app) ->
        #: allowed movements
        @moves =
            armies: ''
            fleets: ''
            mc: ''
        #: countries in game
        @countries = {}
        #: starting countries terrs
        @countries_init = {}
        #: map terrs type
        @neutrals = []
        @seas = []
        @coasts = []
        @mcoasts = []
        #: coast names per multi-coast terr, in index order (the engine speaks indices, the SVG names)
        @coastNames = {}
        #: supply centers
        @_supplylist = []
        @homes = {}
        #: terr names (id -> name) and the inverse (name -> id, the SVG speaks names)
        @names = {}
        @ids = {}
        #: terr codes (id -> three-letter code)
        @codes = {}
        return

    init: (data) ->
        @moves.armies = data.links.armies
        @moves.fleets = data.links.fleets
        @moves.mc = data.links.multi_coasts
        @neutrals = data.neutrals or []
        @seas = data.seas or []
        @coasts = data.coasts or []
        @mcoasts = data.multi_coasts or []
        @coastNames = data.coast_names or {}
        @_supplylist = data.supply_centers or []
        @homes = data.home_centers
        @names = data.names
        @ids = {}
        for id, name of @names
            @ids[name] = id
        @codes = data.codes or {}
        @countries = data.countries
        @countries_init = data.init.territories
        #@_cleanAvailMoves()
        return

    _cleanAvailMoves: ->
        #: this can be avoided if we're sure links not contains neutrals
        rv =
            armies: {}
            fleets: {}
            mc: {}
        for k in ["armies", "fleets"]
            for tid, links of @moves[k]
                if tid not in @neutrals
                    rv[tid] = []
                    for l in links
                        if l not in @neutrals
                            rv[tid].push(l)
        for tid, alinks of @moves.mc
            if tid not in @neutrals
                rv.mc[tid] = [[], []]
                for i in [0, 1]
                    for l in alinks[i]
                        if l not in @neutrals
                            rv.mc[tid][i].push(l)
        @moves = rv
        return

    #: the key used for a country in the page: `--c-<key>` custom properties, `data-power` / `data-owner`
    #: attributes. Must match the server side (controllers/games.py, play): lowercase, every run of
    #: characters other than a-z and 0-9 becomes one dash, no leading or trailing dash.
    countryKey: (name) ->
        return String(name).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "")

    isSea: (id) ->
        return id in @seas

    isCoast: (id) ->
        return id in @coasts

    isMCoast: (id) ->
        return id in @mcoasts

    isSupply: (id) ->
        if @app.game.buildew
            return id in @_supplylist
        return id in (@homes[@app.game.country] or [])

window.Environment = Environment
