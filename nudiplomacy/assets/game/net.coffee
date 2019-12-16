class Network
    constructor: (@app) ->
        @routes = {}
        @sockets = {}
        return

    route: (name, url) ->
        @routes[name] = url
        return

    setSockets: (watchState) ->
        if watchState
            @sockets.state = new WebSocket(@routes.status)
            @sockets.state.binaryType = 'arraybuffer'
            @sockets.state.addEventListener 'message', (event) =>
                @app.ux.gameStateChanged(String.fromCharCode.apply(null, new Uint8Array(event.data)))
        @sockets.messages = new WebSocket(@routes.chat_sub)
        @sockets.messages.binaryType = 'arraybuffer'
        @sockets.messages.addEventListener 'message', (event) =>
            @app.ux.chatMessageReceived(
                JSON.parse(String.fromCharCode.apply(null, new Uint8Array(event.data)))
            )

    # getMessages: (cid, country, since=null) ->
    #     u = @routes['messages']+"/"+cid
    #     if since
    #         u += "?since="+since
    #     $.ajax u,
    #         type: 'GET'
    #         success: (data) ->
    #             @app.ui.gotMessages(country, data.data)
    #             return
    #     return

    # postMessage: (cid, text) ->
    #     d =
    #         msg: text
    #     $.ajax @routes['postmessage']+"/"+cid,
    #         type: 'POST'
    #         contentType: "application/json"
    #         data: JSON.stringify(d)
    #         success: (data) ->
    #             console.log(data)
    #             return
    #         error: ->
    #             return
    #     return

    # setRead: (cid, mid, global=false) ->
    #     rv = {}
    #     u = @routes['readmessage']+"/"+cid+"/"+mid
    #     if global
    #         u += "?all=y"
    #     $.ajax u,
    #         type: 'GET'
    #         success: (data) ->
    #             rv = data
    #             return
    #     return rv

window.Network = Network
