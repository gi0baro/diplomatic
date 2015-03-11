from weppy import AppModule, url, abort, request, redirect
from weppy.tools import requires
from nudiplomacy import app, db, mdb, auth, Game
from nudiplomacy.handlers import AppStatus
from nudiplomacy.contexts import BaseContext
from nudiplomacy.helpers.mongo import longToObjid

games = AppModule(app, "games", __name__, url_prefix="games",
                  template_folder="games")
games.common_helpers = [AppStatus(), BaseContext()]


@games.expose("/")
def index():
    return dict(show="open")


@games.expose(template="index.haml")
def all():
    return dict(show="all")


@games.expose("/aj/list/<str:mode>")
def query(mode):
    if mode not in ["all", "open"]:
        return dict(games=[])
    step = request.vars.step or 0
    limit = (step, step+20)
    if mode == "open":
        q = (db.Game.open == True)
    else:
        q = (db.Game.id > 0)
    gamelist = db(q).select(orderby=~db.Game.created, limitby=limit)
    return dict(games=gamelist)


@games.expose("/create")
@requires(auth.is_logged_in, url("main.account", "login"))
def new():
    def validate(form):
        #: variant check
        mapdata = db.Map(id=form.vars.map)
        if not mapdata:
            form.errors.map = "Invalid map"
            return
        #: max players check
        maxplayers = len(mapdata.countries)
        if form.vars.nplayers < mapdata.minplayers or \
                form.vars.nplayers > maxplayers:
            form.errors.nplayers = "Invalid number of players"
            return
        #: bet check
        playerdata = db.UserData(user=auth.user.id)
        if playerdata.credits < form.vars.bet:
            form.errors.bet = "You have not enough credits to set this bet"
            return
        if form.vars.bet > 1 and form.vars.nplayers == 2:
            form.errors.bet = "Maximum bet for 2 players is 1 credit"
        #: countries enabled check
        if not form.vars.countriesenabled or \
                len(form.vars.countriesenabled) < form.vars.nplayers:
            form.vars.countriesenabled = mapdata.countries.keys()
        #: assign check
        if form.vars.countriesassign == "choose":
            # validate user chosen
            if form.vars.countries.get('me') not in form.vars.countriesenabled:
                form.vars.countriesassign.error = "When players have to " + \
                    "choose their countries, you must too."
                return
        #: access check
        if form.vars.access == "password":
            if not form.vars.password or len(form.vars.password) < 4:
                form.vars.access.password = "When you protect your game " + \
                    "with a password, it must be at least of 4 characters"

    form = Game.form(onvalidation=validate)
    if form.accepted:
        redirect(url('.play', form.vars.id))
    return dict(form=form)


@games.expose("/play/<int:gid>")
def play(gid):
    game = db(db.Game.id == gid).select().first()
    if not game:
        abort(404)
    #: evaluate real sc for win
    scs = game.targetsc or game.map.scstowin
    #: get player chats
    inMatch = ['all']
    playercountry = game.playercountry()
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
    return dict(game=game, scs=scs, chats=chats, timer=game.timetonext(),
                statscol=statscol)


@games.expose("/mine")
@requires(auth.is_logged_in, url("games.index"))
def owned():
    return dict()
