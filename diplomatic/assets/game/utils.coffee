class Utils
    constructor: (@app) ->
        return

    getTerritoryName: (id) ->
        if @app.env.names[id]
            return @app.env.names[id]
        return

window.Utils = Utils
