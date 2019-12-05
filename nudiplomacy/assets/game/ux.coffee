class UX
    constructor: (@app) ->
        @gamePre = false
        @gameOver = false
        @alertMethod = () -> return
        return

    configure: (alertMethod) ->
        @alertMethod = alertMethod

    alert: (message, dismissable=true, autoDismiss=null) ->
        @alertMethod(message, dismissable, autoDismiss)
        return

    launched: (gamePre, gameOver) ->
        @gamePre = gamePre
        @gameOver = gameOver
        @afterLaunch()
        return

    afterLaunch: ->
        if @gamePre
            @alert("This is a pre-game phase. The game will start when all the players have been joined.", false)
        return

    gameStateChanged: (data) ->
        @alert("Game changed, reloading in 5 seconds..", false)
        setTimeout (->
            @app.reload()
        ), 5000
        return

window.UX = UX
