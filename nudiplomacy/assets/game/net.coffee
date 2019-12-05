class Network
    constructor: (@app) ->
        @routes = {}
        @sockets = {}
        return

    route: (name, url) ->
        @routes[name] = url
        return

    setSockets: ->
        @sockets.state = new WebSocket(@routes.status)
        @sockets.state.binaryType = 'arraybuffer'
        @sockets.state.addEventListener 'message', (event) =>
            @app.ux.gameStateChanged(String.fromCharCode.apply(null, new Uint8Array(event.data)))

    getMap: ->
        rv = {}
        $.ajax @routes['map'],
            type: 'GET'
            async: false
            success: (data) ->
                rv = data
                return
        return rv

    getGame: ->
        rv = {}
        $.ajax @routes['game'],
            type: 'GET'
            async: false
            success: (data) ->
                rv = data
                return
        return rv

    getPhases: ->
        rv = {}
        $.ajax @routes['phases'],
            type: 'GET'
            async: false
            success: (data) ->
                rv = data.data
                return
        return rv

    # getGameStatus: ->
    #     $.ajax @routes['status'],
    #         type: 'GET'
    #         success: (data) ->
    #             @app.ui.gotGameStatus(data.status, data.phase)
    #             return
    #     return

    getOrders: (phase, callback) ->
        console.log('called getOrders for phase', phase)
        rv = {}
        $.ajax @routes['phase_orders'].replace(':PHASE_ID:', phase.id),
            type: 'GET'
            success: (response) ->
                callback(response.data)
                return
        return

    getCurrentOrders: ->
        rv = {}
        $.ajax @routes['orders'],
            type: 'GET'
            async: false
            success: (data) ->
                rv = data
                return
        return rv

    getMessages: (cid, country, since=null) ->
        u = @routes['messages']+"/"+cid
        if since
            u += "?since="+since
        $.ajax u,
            type: 'GET'
            success: (data) ->
                @app.ui.gotMessages(country, data.data)
                return
        return

    postOrder: (order) ->
        @app.ui.saving()
        $.ajax @routes['save_orders'].replace(':ORDER_ID:', order.id),
            type: 'PUT'
            contentType: "application/json"
            data: JSON.stringify(order)
            success: (data) ->
                console.log(data)
                order._changed = false
                @app.ui.saved(data)
                return
            error: ->
                #console.log(error)
                return
        return

    postMessage: (cid, text) ->
        d =
            msg: text
        $.ajax @routes['postmessage']+"/"+cid,
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
        d =
            ready: true
        $.ajax @routes['ready'],
            type: 'POST'
            contentType: "application/json"
            data: JSON.stringify(d)
            success: (data) ->
                @app.ui.didReady(data.data)
                return
        return

    setUnready: ->
        d =
            ready: false
        $.ajax @routes['ready'],
            type: 'POST'
            contentType: "application/json"
            data: JSON.stringify(d)
            success: (data) ->
                @app.ui.didReady(data.data)
                return
        return

    setRead: (cid, mid, global=false) ->
        rv = {}
        u = @routes['readmessage']+"/"+cid+"/"+mid
        if global
            u += "?all=y"
        $.ajax u,
            type: 'GET'
            success: (data) ->
                rv = data
                return
        return rv

window.Network = Network
