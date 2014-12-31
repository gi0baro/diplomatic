from nudiplomacy import app

css_base = app.ext.Assets.css(['css/base.css'], output='base.css').minify()

app.ext.Assets.register('css_base', css_base)

js_game = app.ext.Assets.js([
    'helpers/Point.js',
    'helpers/Intersection.js',
    'game/objects.coffee',
    'game/net.coffee',
    'game/env.coffee',
    'game/game.coffee',
    'game/screen.coffee',
    'game/interactions.coffee',
    'game/ui.coffee',
    'game/main.coffee'], output='game.js')

css_game = app.ext.Assets.css(['css/game.css'], output='game.css').minify()

app.ext.Assets.register('js_game', js_game)
app.ext.Assets.register('css_game', css_game)
