class Utils
    constructor: (@app) ->
        return

    getTerritoryNameByPosition: (mapPosition) ->
        refcolor = @app.screen.getColor(mapPosition)
        id = @app.env.getTerritoryByColor(refcolor)
        if @app.env.names[id]
            return @app.env.names[id]
        return

window.Utils = Utils
