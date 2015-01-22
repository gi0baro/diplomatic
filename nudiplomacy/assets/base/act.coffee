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
        $('#joinmsg').html "Joining.."
        $('#joinbtn').attr
            disabled: 'disabled'
        api.join(gid)
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

    cannotJoin: (msg) ->
        $('#joinmsg').html msg
        $('#joinbtn').html "Error"
        return

window.act = new Act()
