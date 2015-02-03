class Network
    constructor: ->
        @urls = {}
        return

    route: (name, url) ->
        @urls[name] = url
        return

    getMap: ->
        rv = {}
        $.ajax @urls['map'],
            type: 'GET'
            async: false
            success: (data) ->
                rv = data
                return
        return rv

    getGame: ->
        rv = {}
        $.ajax @urls['game'],
            type: 'GET'
            async: false
            success: (data) ->
                rv = data
                return
        return rv

    getOrders: ->
        rv = {}
        $.ajax @urls['orders'],
            type: 'GET'
            async: false
            success: (data) ->
                rv = data
                return
        return rv

    getMessages: (cid, country) ->
        $.ajax @urls['messages']+"/"+cid,
            type: 'GET'
            success: (data) ->
                app.ui.gotMessages(country, data.data)
                return
        return

    postOrders: ->
        d =
            orders: app.game.orders
        app.ui.saving()
        $.ajax @urls['saveorders'],
            type: 'POST'
            contentType: "application/json"
            data: JSON.stringify(d)
            success: (data) ->
                console.log(data)
                app.ui.saved(data)
                return
            error: ->
                #console.log(error)
                return
        return

    postMessage: (cid, text) ->
        d =
            msg: text
        $.ajax @urls['postmessage']+"/"+cid,
            type: 'POST'
            contentType: "application/json"
            data: JSON.stringify(d)
            success: (data) ->
                console.log(data)
                return
            error: ->
                return
        return

    setReady: ->
        $.ajax @urls['ready'],
            type: 'GET'
            success: (data) ->
                app.ui.didReady(data.data)
                return
        return

    setUnready: ->
        $.ajax @urls['unready'],
            type: 'GET'
            success: (data) ->
                app.ui.didReady(data.data)
                return
        return

    setRead: (cid, mid, global=false) ->
        rv = {}
        u = @urls['readmessage']+"/"+cid+"/"+mid
        if global
            u += "?all=y"
        $.ajax u,
            type: 'GET'
            success: (data) ->
                rv = data
                return
        return rv

window.Network = Network
