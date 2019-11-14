
class App
    constructor: ->
        @net = new Network()
        @ui = new UI()
        @screen = new Screen()
        @act = new Interactions()
        @env = new Environment()
        @game = new Game()
        return

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
        if currentPlayer and not preGame
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

window.app = new App()
