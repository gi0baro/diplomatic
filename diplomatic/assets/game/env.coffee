
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

    #: the province ids a fleet on coast `coast` of multi-coast `id` reaches (links.multi_coasts[id][coast]
    #: maps each of them to the coasts of it that this coast touches, null when it has none)
    fleetReach: (id, coast) ->
        return (k for k of @moves.mc[id][coast])

    #: which coasts of multi-coast `dst` a fleet in `src` reaches, as [coast 0, coast 1]: a coast counts
    #: when it borders `src` and, if `src` has coasts too, touches the fleet's own one, `srcCoast`
    #: (the server's touches_coast)
    reachableCoasts: (src, srcCoast, dst) ->
        res = []
        for reach in @moves.mc[dst]
            coasts = reach[src]
            res.push(src of reach and (coasts is null or srcCoast in coasts))
        return res

    isSupply: (id) ->
        if @app.game.buildew
            return id in @_supplylist
        return id in (@homes[@app.game.country] or [])

window.Environment = Environment
