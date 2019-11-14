class Network
    constructor: ->
        @urls = {}
        @sockets = {}
        return

    route: (name, url) ->
        @urls[name] = url
        return

    setSockets: ->
        @sockets.state = new WebSocket(@urls.status)
        @sockets.state.binaryType = 'arraybuffer'
        @sockets.state.addEventListener 'message', (event) ->
            app.ui.gotGameStatus(String.fromCharCode.apply(null, new Uint8Array(event.data)))

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

    getPhases: ->
        rv = {}
        $.ajax @urls['phases'],
            type: 'GET'
            async: false
            success: (data) ->
                rv = data.data
                return
        return rv

    # getGameStatus: ->
    #     $.ajax @urls['status'],
    #         type: 'GET'
    #         success: (data) ->
    #             app.ui.gotGameStatus(data.status, data.phase)
    #             return
    #     return

    getOrders: (phase, callback) ->
        console.log('called getOrders for phase', phase)
        rv = {}
        $.ajax @urls['phase_orders'].replace(':PHASE_ID:', phase.id),
            type: 'GET'
            success: (response) ->
                callback(response.data)
                return
        return

    getCurrentOrders: ->
        rv = {}
        $.ajax @urls['orders'],
            type: 'GET'
            async: false
            success: (data) ->
                rv = data
                return
        return rv

    getMessages: (cid, country, since=null) ->
        u = @urls['messages']+"/"+cid
        if since
            u += "?since="+since
        $.ajax u,
            type: 'GET'
            success: (data) ->
                app.ui.gotMessages(country, data.data)
                return
        return

    postOrder: (order) ->
        app.ui.saving()
        $.ajax @urls['save_orders'].replace(':ORDER_ID:', order.id),
            type: 'PUT'
            contentType: "application/json"
            data: JSON.stringify(order)
            success: (data) ->
                console.log(data)
                order._changed = false
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
        d =
            ready: true
        $.ajax @urls['ready'],
            type: 'POST'
            contentType: "application/json"
            data: JSON.stringify(d)
            success: (data) ->
                app.ui.didReady(data.data)
                return
        return

    setUnready: ->
        d =
            ready: false
        $.ajax @urls['ready'],
            type: 'POST'
            contentType: "application/json"
            data: JSON.stringify(d)
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
