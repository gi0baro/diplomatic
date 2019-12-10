class UX
    constructor: (@app) ->
        @gamePre = false
        @gameOver = false
        @menus =
            territory:
                open: () -> return
                close: () -> return
            build:
                open: () -> return
                close: () -> return
            retreat:
                open: () -> return
                close: () -> return
        @activeMenu = null
        @alertMethod = () -> return
        return

    configure: (menuTerritoryOpen, menuTerritoryClose, alertMethod) ->
        @menus.territory.open = menuTerritoryOpen
        @menus.territory.close = menuTerritoryClose
        @alertMethod = alertMethod

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

    menuOpen: (type, data) ->
        @activeMenu = type
        @menus[type].open(data)

    menuClose: (type) ->
        @menus[type].close()
        @activeMenu = null

    _remapAction: (action) ->
        return {
            hold: "hold",
            move: "move",
            sup_hold: "support_hold",
            sup_move: "support_move",
            convoy: "convoy",
            build_army: "army",
            build_fleet: "fleet",
            disband: "disband",
            retreat: "retreat"
        }[action]

    relevantActionMenuOpen: (position, territory) ->
        if @app.game.phase().type is PHASE_TYPES.diplomacy
            canConvoy = @app.game.phase().canConvoy(territory)
            # move = @app.game.hasMove(territory)
            @menuOpen('territory', {position: position, canConvoy: canConvoy, territory: territory})
        if @app.game.phase().type is PHASE_TYPES.builds
            canBuildFleet = @app.env.isCoast(territory)
            # if territory in @app.game.phase().getCountryTroops()
            #     build = @app.game.hasBuild(territory)
            #     action = if build then 'disband' else null
            # else
            #     action = @app.game.hasBuild(territory)
            @menuOpen('build', {position: position, canBuildFleet: canBuildFleet, territory: territory})
        if @app.game.phase().type is PHASE_TYPES.retreats
            # move = @app.game.hasMove(territory)
            # action = if move then 'retreat' else 'disband'
            @menuOpen('retreat', {position: position, territory: territory})
        return

    relevantActionMenuClose: () ->
        if @activeMenu isnt null
            @menuClose(@activeMenu)

    alert: (message, dismissable=true, autoDismiss=null) ->
        @alertMethod(message, dismissable, autoDismiss)
        return

window.UX = UX
