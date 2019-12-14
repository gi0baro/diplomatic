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
            coast:
                open: () -> return
                close: () -> return
        @activeMenu = null
        @alertMethod = () -> return
        return

    configure: (
        menuTerritoryOpen, menuTerritoryClose,
        menuBuildOpen, menuBuildClose,
        menuRetreatOpen, menuRetreatClose,
        menuCoastOpen, menuCoastClose,
        alertMethod
    ) ->
        @menus.territory.open = menuTerritoryOpen
        @menus.territory.close = menuTerritoryClose
        @menus.build.open = menuBuildOpen
        @menus.build.close = menuBuildClose
        @menus.retreat.open = menuRetreatOpen
        @menus.retreat.close = menuRetreatClose
        @menus.coast.open = menuCoastOpen
        @menus.coast.close = menuCoastClose
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
        setTimeout (=>
            @app.reload()
        ), 5000
        return

    menuOpen: (type, data) ->
        @activeMenu = type
        @menus[type].open(data)

    menuClose: (type) ->
        @menus[type].close()
        @activeMenu = null

    relevantActionMenuOpen: (position, territory) ->
        if @app.game.phase().type is PHASE_TYPES.diplomacy
            canConvoy = @app.game.phase().canConvoy(territory)
            @menuOpen('territory', {position: position, canConvoy: canConvoy, territory: territory})
        if @app.game.phase().type is PHASE_TYPES.builds
            canBuild = true
            canBuildFleet = @app.env.isCoast(territory)
            canDisband = false
            if territory in @app.game.phase().getCountryTroops()
                if @app.game.hasBuild(territory)
                    canDisband = true
            @menuOpen('build', {position: position, canBuild: canBuild, canDisband: canDisband, canBuildFleet: canBuildFleet, territory: territory})
        if @app.game.phase().type is PHASE_TYPES.retreats
            @menuOpen('retreat', {position: position, territory: territory})
        return

    relevantActionMenuClose: () ->
        if @activeMenu isnt null
            @menuClose(@activeMenu)

    alert: (message, dismissable=true, autoDismiss=null) ->
        @alertMethod(message, dismissable, autoDismiss)
        return

window.UX = UX
