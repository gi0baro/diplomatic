
class Environment
    constructor: ->
        #: terr id and color
        @colors = {}
        #: pixels of terrs
        @pix = {}
        #: allowed movements
        @moves =
            armies: ''
            fleets: ''
            mc: ''
        #: coord ref for armies
        @oxy = {}
        #: countries in game
        @countries = {}
        #: starting countries terrs
        @countries_init = {}
        #: map terrs type
        @neutrals = []
        @seas = []
        @coasts = []
        @mcoasts = []
        @mcoasts_oxy = {}
        @same = {}
        #: supply centers
        @supply = {}
        @_supplylist = []
        @homes = {}
        #: terr names
        @names = {}
        return

    init: (data) ->
        @colors = data.colors
        @moves.armies = data.links.armies
        @moves.fleets = data.links.fleets
        @moves.mc = data.links.mc
        @oxy = data.oxy
        @neutrals = data.neutrals
        @same = data.same
        @seas = data.seas
        @coasts = data.coasts
        @mcoasts_oxy = data.mcoasts
        @supply = data.supply
        @_supplylist = (key for key of @supply)
        @homes = data.homes
        @names = data.names
        @countries = data.countries
        @countries_init = data.init.territories
        @mcoasts = (key for key of @mcoasts_oxy)
        return

    isSame: (id) ->
        return id in (key for key of @same)

    isSea: (id) ->
        return id in @seas

    isCoast: (id) ->
        return id in @coasts

    isMCoast: (id) ->
        return id in @mcoasts

    isSupply: (id) ->
        if app.game.buildew
            return id in @_supplylist
        return id in @homes[app.game.country]

    isNeutral: (id) ->
        return id in @neutrals

    getTerritoryByColor: (color) ->
        #: this get the territory id from color
        for key, value of @colors
            db_color = r: value[0], g: value[1], b: value[2]
            if db_color.r is color.r and db_color.g is color.g and db_color.b is color.b
                Id = key
                break
        return Id

window.Environment = Environment
