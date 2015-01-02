from weppy import AppModule, url, abort
from weppy.tools import requires
from nudiplomacy import app, db, auth, Game
from nudiplomacy.contexts import BaseContext

games = AppModule(app, "games", __name__, url_prefix="games",
                  template_folder="games")
games.common_helpers = [BaseContext()]


@games.expose("/")
def index():
    ## TEMP
    rows = db(db.Game.id > 0).select().as_list()
    app.log.debug(rows)
    ##
    return dict()


@games.expose("/create")
@requires(auth.is_logged_in, url("main.account", "login"))
def new():
    def validate(form):
        mapdata = db.Map(id=form.vars.map)
        if not mapdata:
            form.errors.map = "Invalid map"
            return
        maxplayers = len(mapdata.countries)
        if form.vars.nplayers < mapdata.minplayers or \
                form.vars.nplayers > maxplayers:
            form.errors.nplayers = "Invalid number of players"
            return
        if not form.vars.countriesenabled:
            import json
            form.vars.countriesenabled = json.dumps(
                mapdata.countries.keys())
        if form.vars.countriesassign == "choose":
            # validate user chosen
            pass

    form = Game.form(onvalidation=validate)
    return dict(form=form)


@games.expose("/play/<int:gid>")
def play(gid):
    game = db(db.Game.id == gid).select().first()
    if not game:
        abort(404)
    # temp
    orders = db(db.Orders.game == game.id).select().as_list()
    app.log.debug(orders)
    #
    return locals()


@games.expose("/mine")
@requires(auth.is_logged_in, url("games.index"))
def owned():
    return dict()
