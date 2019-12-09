
class App
    constructor: ->
        @net = new Network(@)
        @ui = new UI()
        @screen = new Screen(@)
        @act = new Interactions(@)
        @env = new Environment(@)
        @game = new Game(@)
        @ux = new UX(@)
        @utils = new Utils(@)
        @launched = false
        console.log(@game.app)
        return

    init: (map_src, army_src, fleet_src, map_update_callback, screen_init_callback, alert_method) ->
        @screen.buildElements(map_src, army_src, fleet_src)
        @screen.register_callbacks(map_update_callback, screen_init_callback)
        @ux.configure(alert_method)

    launch: (mapData, gameData, player, isGameActive, isPreGame, isGameOver, isPlayerReady, callback) ->
        console.log('launch')
        @env.init(mapData)
        # temp
        phases = []
        orders =
            data: {}
        #
        @game.init(gameData, player, orders, isPlayerReady)
        @screen.init()
        @ux.launched(isPreGame, isGameOver)
        @net.setSockets()
        @launched = true
        callback()

    start: ->
        setTimeout(->
            app._start()
        , 300)

    _start: ->
        mapData = @net.getMap()
        #console.log(mapData)
        @env.init(mapData)
        gameData = @net.getGame()
        gamePhases = @net.getPhases()
        #console.log(gameData)
        if currentPlayer and isGameActive
            orders = @net.getCurrentOrders()
        else
            orders =
                data: {}
        @net.setSockets()
        @game.init(gameData, gamePhases, orders, =>
            @ui.init()
            @ui.buildOrders()
            @ui.initStats()
            @ui.initMessages()
            if @game.gotOrders()
                @ui.iconOn('ord')
            if @game.ready
                @ui.iconLight('ready')
                @ui.iconLight('ord')
            @screen.createElements()
            @screen.img.onload = ->
                app._launch()
        )
        return

    _launch: ->
        @ui.setProps()
        #console.log(@env)
        #console.log(@game)
        @screen.init()
        @ui.showMap(@screen.ref.layer.height)
        @ui.setHandlers()
        if @game.isLastPhase()
            @ui.setPhase('last')
        else
            @ui.setPhase('next')
        @ui.hideLoader()
        if @game.isWin
            @ui.win()
        return

    reload: ->
        # if preGame
        location.reload()
        return
        # gameData = @net.getGame()
        # orders = @net.getCurrentOrders()
        # @game.reload(gameData, orders)
        # @ui.reload()
        # @game.loadPhase(@game.phase('last').position)
        # return

window.gapp = new App()
