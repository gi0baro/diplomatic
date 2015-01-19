class Act
    constructor: ->
        @jgid = null

    _showJoinFrame: ->
        $('#joinframe').fadeToggle 350
        return

    hideJoinFrame: ->
        @jgid = null
        $('#joinframe').fadeToggle(
            350
            (event) ->
                return
            )
        return

    joinGame: (gid, bet) ->
        @jgid = gid
        $('#betwarn').html bet
        @_showJoinFrame()
        return

    confirmJoinGame: (gid) ->
        $('#joinmsg').html "Loading"
        return

    joinedGame: ->
        $('#joinmsg').html "You joined the game successfully."
        $('#joinbtn').css
            display: 'none'
        setTimeout(
            ->
                window.location.replace(api.urls.game+"/"+@jgid)
                return
            1000
        )
        return

window.act = new Act()
