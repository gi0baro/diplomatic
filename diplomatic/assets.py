# -*- coding: utf-8 -*-

from diplomatic import app


css_base = app.ext.Assets.css(["helpers/bootstrap-slider.min.css", "css/base.css"], output="base.css").minify()

js_base = app.ext.Assets.js(
    [
        "helpers/masonry.min.js",
        "helpers/bootstrap-slider.min.js",
        "base/api.coffee",
        "base/act.coffee",
        "base/counter.coffee",
    ],
    output="base.js",
).minify()

app.ext.Assets.register("css_base", css_base)
app.ext.Assets.register("js_base", js_base)

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
