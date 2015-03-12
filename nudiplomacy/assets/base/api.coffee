class API
    constructor: ->
        @urls = {}
        return

    route: (name, url) ->
        @urls[name] = url
        return

    join: (gid, country=null, psw=null) ->
        url = @urls.join + "/" + gid
        d =
            country: country
            password: psw
        $.ajax url,
            type: 'POST'
            contentType: "application/json"
            data: JSON.stringify(d)
            success: (data) ->
                if data.status is "Ok"
                    act.joinedGame()
                else
                    act.cannotJoin(data.data)
                return
            error: ->
                act.cannotJoin("Unknown error")
                return
        return

window.api = new API()
