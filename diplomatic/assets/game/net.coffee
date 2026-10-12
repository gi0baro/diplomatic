class Network
    constructor: (@app) ->
        @routes = {}
        @socket = null
        @closing = false
        @retryDelay = 1000
        @retryTimer = null
        window.addEventListener 'pagehide', =>
            @closing = true
            return
        return

    route: (name, url) ->
        @routes[name] = url
        return

    #: one socket per game, the server relays several topics on it as text frames
    #  `{"topic": ..., "data": ...}`, re-dispatched on `document` as `game:<topic>` events
    setSockets: ->
        return unless @routes.socket
        @closing = false
        @openSocket()
        return

    openSocket: ->
        @retryTimer = null
        socket = new WebSocket(@routes.socket)
        socket.addEventListener 'open', =>
            @retryDelay = 1000
            return
        socket.addEventListener 'message', (event) =>
            try
                frame = JSON.parse(event.data)
            catch err
                return
            document.dispatchEvent(new CustomEvent("game:" + frame.topic, {detail: frame.data}))
            return
        socket.addEventListener 'close', =>
            @socket = null if @socket is socket
            @scheduleReconnect()
            return
        @socket = socket
        return

    #: exponential backoff, 1s doubling up to 30s, reset once a socket opens
    scheduleReconnect: ->
        return if @closing or @retryTimer isnt null
        delay = @retryDelay
        @retryDelay = Math.min(@retryDelay * 2, 30000)
        @retryTimer = setTimeout (=> @openSocket()), delay
        return

    _json: (url, method, body) ->
        return fetch(url, {
            method: method
            credentials: "same-origin"
            headers: {"Content-Type": "application/json", "Accept": "application/json"}
            body: JSON.stringify(body)
        })

    #: PUT every order row given ({type, data} each); a 200 clears `_changed` unless the row changed
    #: again while in flight. Never rejects: resolves {saved: n, errors: {territory: reason}} (422
    #: bodies carry the validator's {territory: reason}; other failures are filed under the row).
    saveOrders: (orders) ->
        errors = {}
        saved = 0
        one = (order) =>
            rev = order._rev
            url = @routes.order_save.replace(":ID:", order.id)
            return @_json(url, "PUT", {type: order.type, data: order.data})
                .then (r) ->
                    return r.json().catch(-> {}).then (body) ->
                        return {status: r.status, body: body or {}}
                .then (res) ->
                    if res.status is 200 and res.body.status is "ok"
                        saved++
                        order._changed = false if order._rev is rev
                    else if res.status is 422 and res.body.data and typeof res.body.data is "object"
                        for territory, reason of res.body.data
                            errors[territory] = reason
                    else
                        errors[order.territory] = res.body.data or "error " + res.status
                    return
                .catch (err) ->
                    errors[order.territory] = "network error"
                    return
        return Promise.all((one(order) for order in orders)).then ->
            return {saved: saved, errors: errors}

    #: resolves the response body ({status: 'ok', data: bool} on success)
    setReady: (ready) ->
        return @_json(@routes.ready, "PUT", {ready: !!ready}).then (r) ->
            return r.json()

    closeSockets: ->
        @closing = true
        if @retryTimer isnt null
            clearTimeout(@retryTimer)
            @retryTimer = null
        @socket.close() if @socket
        @socket = null
        return

window.Network = Network
