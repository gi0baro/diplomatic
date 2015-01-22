class API
    constructor: ->
        @urls = {}
        return

    route: (name, url) ->
        @urls[name] = url
        return

    join: (gid, country=null) ->
        url = @urls.join + "/" + gid
        if country isnt null
            url = url + "?country=" + country
        $.ajax url,
            type: 'GET'
            success: (data) ->
                if data.status is "Ok"
                    act.joinedGame()
                    return
                else
                    console.log(data.data)
                return
            error: ->
                return
        return

window.api = new API()
