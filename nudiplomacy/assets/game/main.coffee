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
        #console.log(gameData)
        if gameData.currentPlayer
            orders = @net.getOrders()
        else
            orders =
                data: {}
        @game.init(gameData, orders)
        @ui.init()
        @ui.buildOrders()
        if @game.gotOrders()
            @ui.iconOn('ord')
        if @game.ready
            @ui.iconLight('ready')
            @ui.iconLight('ord')
        @screen.createElements()
        @screen.img.onload = ->
            app._launch()
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
        return

window.app = new App()
