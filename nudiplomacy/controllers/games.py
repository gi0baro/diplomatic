
import json
from weppy import AppModule, url, abort, request, redirect
from weppy.tools import requires
from nudiplomacy import app, db, mdb, auth, Game
from nudiplomacy.handlers import AppStatus
from nudiplomacy.contexts import BaseContext
from nudiplomacy.helpers.mongo import longToObjid, objidToLong

games = AppModule(app, "games", __name__, url_prefix="games",
                  template_folder="games")
games.common_helpers = [AppStatus(), BaseContext()]


@games.route("/")
def index():
    return dict(show="open")


@games.route(template="index.haml")
def all():
    return dict(show="all")


@games.route("/aj/list/<str:mode>")
def query(mode):
    if mode not in ["all", "open"]:
        return dict(games=[])
    step = request.params.step or 0
    limit = (step, step + 20)
    if mode == "open":
        q = (db.Game.is_open == True)
    else:
        q = (db.Game)
    gamelist = db(q).select(orderby=~db.Game.created_at, limitby=limit)
    for game in gamelist:
        game._jslots = json.dumps(game.slots)
    return dict(games=gamelist)


@games.route("/create")
@requires(auth.is_logged_in, url("main.account", "login"))
def new():
    def validate(form):
        app.log.debug(form.params.countries)
        #: variant check
        mapdata = db.Map(id=form.params.map)
        if not mapdata:
            form.errors.map = "Invalid map"
            return
        #: max players check
        maxplayers = len(mapdata.countries)
        if form.params.nplayers < mapdata.min_players or \
                form.params.nplayers > maxplayers:
            form.errors.nplayers = "Invalid number of players"
            return
        #: bet check
        playerdata = db.UserData(user=auth.user.id)
        if playerdata.credits < form.params.bet:
            form.errors.bet = "You have not enough credits to set this bet"
            return
        if form.params.bet > 1 and form.params.nplayers == 2:
            form.errors.bet = "Maximum bet for 2 players is 1 credit"
        #: countries enabled check
        if not form.params.countries_enabled or \
                len(form.params.countries_enabled) < form.params.nplayers:
            form.params.countries_enabled = list(mapdata.countries.keys())
        #: assign check
        if form.params.countries_assign == "choose":
            # validate user chosen
            if form.params.countries.get('me') not in form.params.countries_enabled:
                form.params.countries_assign.error = "When players have to " + \
                    "choose their countries, you must too."
                return
        #: access check
        if form.params.access == "password":
            if not form.params.password or len(form.params.password) < 4:
                form.params.access.password = "When you protect your game " + \
                    "with a password, it must be at least of 4 characters"

    form = Game.form(onvalidation=validate)
    if form.accepted:
        redirect(url('.play', form.params.id))
    app.log.debug(form.errors)
    return dict(form=form)


@games.route("/play/<int:gid>")
def play(gid):
    game = db(db.Game.id == gid).select().first()
    if not game:
        abort(404)
    #: evaluate real sc for win
    scs = game.target_sc or game.map.scs_towin
    #: get player chats
    inMatch = ['all']
    playercountry = game.player_country()
    if playercountry:
        inMatch.append(longToObjid(auth.user.id))
    chatsr = mdb.chats.find({
        'game': longToObjid(gid), 'users': {'$in': inMatch}
    })
    chats = {}
    for r in chatsr:
        if 'all' in r['users']:
            chats['global'] = r['id']
            continue
    if playercountry:
        #for country, player in game.countries.iteritems():
        for el in game.countries:
            if el['country'] == playercountry:
                continue
            for r in chatsr:
                if el['player'] in r['users']:
                    chats[el['country']] = r['id']
                    break
    #: ui stuffs
    if len(game.countries) < 3:
        statscol = 6
    elif len(game.countries) >= 3 and len(game.countries) < 4:
        statscol = 4
    else:
        statscol = 3
    usernames = {}
    for el in game.countries:
        usernames[el['country']] = db.User(id=objidToLong(el['player'])).username
    return dict(game=game, scs=scs, chats=chats, timer=game.time_to_next(),
                statscol=statscol, unames=usernames)


@games.route("/mine")
@requires(auth.is_logged_in, url("games.index"))
def owned():
    return dict()
