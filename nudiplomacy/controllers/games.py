# -*- coding: utf-8 -*-

import os

from emmett import url, abort, request, redirect
from emmett.helpers import stream_file
from emmett.tools import requires
from .. import app, auth, Game, Map
from . import front

games = front.module(__name__, 'games', url_prefix='games', template_folder='games')


@games.route("/")
def index():
    mode = request.query_params.mode or 'open'
    try:
        page = request.query_params.page or 1
        page = int(page)
        assert page >= 1
    except Exception:
        page = 1
    if mode not in ['all', 'open']:
        mode = 'open'
    games = Game.where(lambda g: g.is_open == True) if mode == 'open' else Game.all()
    return {'games': games.select(orderby=~Game.created_at, paginate=(page, 20), including='user'), 'show': mode}


@games.route()
@requires(auth.is_logged, url("auth.login"))
async def create():
    def validate(form):
        app.log.debug(form.params.countries)
        # #: variant check
        # mapdata = db.Map(id=form.params.map)
        # if not mapdata:
        #     form.errors.map = "Invalid map"
        #     return
        variant = Map.get(form.params.map)
        #: max players check
        maxplayers = len(variant.countries)
        if form.params.players_number < variant.min_players or form.params.players_number > maxplayers:
            form.errors.players_number = "Invalid number of players"
            return
        #: bet check
        if auth.user.vault().balance < form.params.bet:
            form.errors.bet = "You have not enough coins to set this bet"
            return
        if form.params.bet > 1 and form.params.players_number == 2:
            form.errors.bet = "Maximum bet for 2 players is 1 coin"
        #: countries enabled check
        if (
            not form.params.countries or
            len([key for key, val in form.params.countries.items() if val]) < form.params.players_number
        ):
            form.params.countries = {key: True for key in variant.countries.keys()}
        #: assign check
        if form.params.countries_assignment == "choice":
            #: validate user choice
            if form.input_params.country_choice not in form.params.countries_enabled:
                form.params.countries_assignment.error = "When players have to choose their countries, you must too."
                return
        #: access check
        if form.params.access == "password":
            if not form.params.password or len(form.params.password) < 4:
                form.params.access.error = \
                    "When you password-protect your game, the password must be at least 4 characters long"
                return
        form.params.user = auth.user

    form = await Game.form(onvalidation=validate)
    app.log.debug(form.params)
    app.log.debug(form.input_params)
    if form.accepted:
        form.params.id.add_player(auth.user, form.input_params.country_choice)
        redirect(url('.play', form.params.id))
    app.log.debug(form.errors)
    return dict(form=form)


@games.route("/play/<int:gid>", template="board.html")
def play(gid):
    game = Game.get(gid)
    if not game:
        abort(404)
    #: evaluate real sc for win
    scs = game.target_sc or game.map.scs_to_win
    #: get player chats
    # inMatch = ['all']
    # playercountry = game.player_country(auth.user)
    # if playercountry:
    #     inMatch.append(longToObjid(auth.user.id))
    # chatsr = mdb.chats.find({
    #     'game': longToObjid(gid), 'users': {'$in': inMatch}
    # })
    # chats = {}
    # for r in chatsr:
    #     if 'all' in r['users']:
    #         chats['global'] = r['id']
    #         continue
    # if playercountry:
    #     #for country, player in game.countries.iteritems():
    #     for el in game.countries:
    #         if el['country'] == playercountry:
    #             continue
    #         for r in chatsr:
    #             if el['player'] in r['users']:
    #                 chats[el['country']] = r['id']
    #                 break
    #: ui stuffs
    # if len(game.countries) < 3:
    #     statscol = 6
    # elif len(game.countries) >= 3 and len(game.countries) < 4:
    #     statscol = 4
    # else:
    #     statscol = 3
    # usernames = {}
    # for el in game.countries:
    #     usernames[el['country']] = db.User(id=objidToLong(el['player'])).username
    players = game.players.join('user').select()
    player = game.player(auth.user) if auth.is_logged() else None
    return {
        'game': game, 'scs': scs, 'chats': {'global': 1}, 'players': players, 'timer': game.timer(),
        'player_id': player.id if player else None,
        'player_country': player.country if player else None,
        'player_ready': player.is_ready if player else False,
        'player_active': player.is_active if player else False,
        'statscol': 6
        #timer=game.time_to_next(),
        #statscol=statscol, unames=usernames)}
    }


@games.route('/mapimg/<int:gid>')
async def map_img(gid):
    game = Game.get(gid)
    if not game:
        abort(404)
    img_path = os.path.join(app.root_path, '..', 'variants', game.map.name.lower(), 'map.png')
    stream_file(img_path)


@games.route("/mine")
@requires(auth.is_logged, url("front.games.index"))
def owned():
    return dict()
