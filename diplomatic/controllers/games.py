# -*- coding: utf-8 -*-

from emmett import abort, redirect, request, url
from emmett.tools import requires

from .. import Game, GameRole, Map, app, auth
from . import front


games = front.module(__name__, "games", url_prefix="games", template_folder="games")


@games.route("/")
def index():
    mode = request.query_params.mode or "open"
    try:
        page = request.query_params.page or 1
        page = int(page)
        assert page >= 1
    except Exception:
        page = 1
    if mode not in ["all", "open"]:
        mode = "open"
    games = Game.where(lambda g: g.is_open == True) if mode == "open" else Game.all()
    return {"games": games.select(orderby=~Game.created_at, paginate=(page, 20), including="user"), "show": mode}


@games.route()
@requires(auth.is_logged, url("auth.login"))
async def create():
    def validate(form):
        app.log.debug(form.params)
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
            not form.params.countries
            or len([key for key, val in form.params.countries.items() if val]) < form.params.players_number
        ):
            form.params.countries = dict.fromkeys(variant.countries.keys(), True)
        #: assign check
        if form.params.countries_assignment == "choice":
            #: validate user choice
            if form.input_params.country_choice not in form.params.countries_enabled:
                form.params.countries_assignment.error = "When players have to choose their countries, you must too."
                return
        #: access check
        if form.params.access == "password":
            if not form.params.password or len(form.params.password) < 4:
                form.params.access.error = (
                    "When you password-protect your game, the password must be at least 4 characters long"
                )
                return
        form.params.user = auth.user

    form = await Game.form(onvalidation=validate)
    app.log.debug(form.params)
    app.log.debug(form.input_params)
    if form.accepted:
        app.log.debug(form.record)
        app.log.debug(form.record.validation_errors)
        form.record.add_player(auth.user, form.input_params.country_choice)
        redirect(url(".play", form.record.id))
    app.log.debug(form.errors)
    return dict(form=form)


@games.route("/play/<int:gid>", template="play.haml")
def play(gid):
    game = Game.get(gid)
    if not game:
        abort(404)
    variant = Map.get(game.map)
    #: evaluate real sc for win
    scs = game.target_sc or variant.scs_to_win
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
    players = game.players.join("user").select()
    player = game.player(auth.user) if auth.is_logged() else None

    #: the country key used by the board (`--c-<key>`, data-power, data-owner): lowercase, every run of
    #: characters other than a-z and 0-9 becomes one dash, no dash at the ends. Must match
    #: `Environment.countryKey` in assets/game/env.coffee.
    def country_key(name):
        return "-".join("".join(ch if ch.isascii() and ch.isalnum() else " " for ch in name.lower()).split())

    #: one custom property per country plus the attribute rules every board/chrome element reads
    colors = variant.countries or {}
    keys = {name: country_key(name) for name in colors}
    css = [":root {"]
    css += [f"  --c-{keys[name]}: rgb({c['r']} {c['g']} {c['b']});" for name, c in colors.items()]
    if player and player.country in keys:
        css.append(f"  --c-me: var(--c-{keys[player.country]});")
    css.append("}")
    css += [f'[data-power="{k}"], [data-owner="{k}"] {{ --c: var(--c-{k}); }}' for k in keys.values()]

    #: the stored SVG inlined: its draft <style> dropped (the page's stylesheet styles it), the
    #: board's id/classes on the root, and the patterns the stylesheet fills with (mockup values)
    svg = variant.svg or ""
    start = svg.find("<style")
    end = svg.find("</style>", start) if start >= 0 else -1
    if end >= 0:
        svg = svg[:start] + svg[end + len("</style>") :]
    root = svg.find("<svg")
    root_end = svg.find(">", root)
    board_svg = ""
    if root >= 0 and root_end >= 0:
        defs = (
            "<defs>"
            '<pattern id="sea" width="26" height="26" patternUnits="userSpaceOnUse">'
            '<rect width="26" height="26" fill="#070a0d"/>'
            '<path d="M26 0H0V26" fill="none" stroke="#597082" stroke-opacity=".09" stroke-width=".6"/></pattern>'
            '<pattern id="seaHi" width="26" height="26" patternUnits="userSpaceOnUse">'
            '<rect width="26" height="26" fill="#0e1c28"/>'
            '<path d="M26 0H0V26" fill="none" stroke="#9fe8ff" stroke-opacity=".16" stroke-width=".6"/></pattern>'
            '<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            '<rect width="7" height="7" fill="#0a0c0f"/>'
            '<line x1="0" y1="0" x2="0" y2="7" stroke="#252d35" stroke-width="1"/></pattern>'
            "</defs>"
        )
        board_svg = (
            '<svg id="map" class="instant" preserveAspectRatio="xMidYMid meet"'
            + svg[root + len("<svg") : root_end + 1]
            + defs
            + svg[root_end + 1 :]
        )

    #: deadline: countdown (static for now), absolute time, share of the phase time left
    timer = game.timer()
    left = timer.d * 86400 + timer.h * 3600 + timer.m * 60 + timer.s
    if not game.next_process_at or game.stage != Game.STAGES["game"]:
        countdown, deadline, left_pct = "--:--:--", None, 0
    else:
        if timer.d:
            countdown = f"{timer.d}d {timer.h:02d}:{timer.m:02d}"
        else:
            countdown = f"{timer.h:02d}:{timer.m:02d}:{timer.s:02d}"
        deadline = game.next_process_at.strftime("%d %b %H:%M UTC")
        left_pct = max(0, min(100, round(100 * left / max(1, game.phase_time * 60))))

    return {
        "game": game,
        "variant": variant,
        "board_svg": board_svg,
        "country_css": "\n".join(css),
        "player_key": keys.get(player.country) if player else None,
        "countdown": countdown,
        "deadline": deadline,
        "left_pct": left_pct,
        "scs": scs,
        "chats": {"global": 1},
        "players": players,
        "timer": timer,
        "player_id": player.id if player else None,
        "player_country": player.country if player else None,
        "player_ready": player.is_ready if player else False,
        "player_active": player.is_active if player else False,
        "statscol": 6,
        # timer=game.time_to_next(),
        # statscol=statscol, unames=usernames)}
    }


@games.route("/mine")
@requires(auth.is_logged, url("front.games.index"))
def owned():
    return {"games": auth.user.participated_games.where(Game.id == GameRole.game).select(Game.table.ALL)}
