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

    stepChange: (step) ->
        console.log('stepChange', step, @app.game.steps)
        stepKey = step.id + '_' + step.type
        if @app.game.steps[stepKey] is undefined
            @app.game.steps[stepKey] = new Step(@app, step)
        @app.game.setStep(@app.game.steps[stepKey])
        return

    gameStateChanged: (data) ->
        @alert("Game changed, reloading in 5 seconds..", false)
        setTimeout (->
            @app.reload()
        ), 5000
        return

window.UX = UX
