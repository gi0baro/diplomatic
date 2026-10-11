
class App
    constructor: ->
        @net = new Network(@)
        @screen = new Board(@)
        @act = new Interactions(@)
        @env = new Environment(@)
        @game = new Game(@)
        @ux = new UX(@)
        @utils = new Utils(@)
        @launched = false
        return

    #: map_src, army_src and fleet_src are kept for compatibility and ignored: the board is the inline SVG
    init: (map_src, army_src, fleet_src, map_update_callback, screen_init_callback, menu_territory_method, alert_method) ->
        @screen.register_callbacks(map_update_callback, screen_init_callback)

    #: only `step` is used (the engine asking the page for the virtual next step); menus, chat and
    #: alerts are DOM events now (see ux.coffee), their callbacks are accepted and ignored
    bindings: (
        menu_territory_open, menu_territory_close,
        menu_build_open, menu_build_close,
        menu_retreat_open, menu_retreat_close,
        menu_coast_open, menu_coast_close,
        step, chat_receiver, alert
    ) ->
        @game.bind(step)
        @ux.configure()
        return

    launch: (mapData, gameData, player, isGameActive, isPreGame, isGameOver, isPlayerReady, orders, callback) ->
        @env.init(mapData)
        @game.init(gameData, player, orders, isPlayerReady)
        @screen.init()
        @ux.launched(isPreGame, isGameOver)
        if player and not isGameOver
            @net.setSockets()
        @launched = true
        document.dispatchEvent(new CustomEvent("board:launched", {detail: {
            player: player
            power: if player then @env.countryKey(player) else null
            players: @game.players
            scsToWin: @game.scsToWin
            canOrder: !!(player and @game.canOrder)
            ready: @game.ready
            pre: isPreGame
            over: isGameOver
        }}))
        @game._emitOrders()
        callback()

    reload: ->
        location.reload()
        return

window.gapp = new App()
