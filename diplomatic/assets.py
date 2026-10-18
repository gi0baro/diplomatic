from diplomatic import app


js_game = app.ext.Assets.js(
    [
        "base/translator.coffee",
        "game/proto.coffee",
        "game/constants.coffee",
        "game/objects.coffee",
        "game/steps.coffee",
        "game/net.coffee",
        "game/env.coffee",
        "game/game.coffee",
        "game/board.coffee",
        "game/interactions.coffee",
        "game/ux.coffee",
        "game/utils.coffee",
        "game/main.coffee",
    ],
    output="game.js",
)

app.ext.Assets.register("js_game", js_game)
