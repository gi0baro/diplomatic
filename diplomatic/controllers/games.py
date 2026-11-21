import json
from datetime import timezone

from emmett import abort, redirect, request, response, url
from emmett.tools import requires

from .. import Game, GameRole, Map, Notification, Vault, app, auth, db
from ..game_kinds import PAGE_KINDS
from ..helpers.events import publish
from ..helpers.games import CARD_FIELDS, GAME_MAP_FIELDS, build_cards, card_values, set_card_phase
from . import front, query_page


games = front.module(__name__, "games", url_prefix="games", template_folder="games")

RUNNING_STAGES = [Game.Stage.GAME, Game.Stage.PROCESSING, Game.Stage.PAUSE, Game.Stage.CRASH]
LOBBY_MODES = {
    "open": Game.where(lambda g: g.is_open == True),
    "running": Game.running(include_pre=True),
    "finished": Game.in_stage(Game.Stage.OVER),
}
LOBBY_PAGE = 20


def card_context(game, user):
    roles = GameRole.where(lambda m: m.game == game.id).select()
    variant = Map.where(lambda m: m.id == game.map).select(*GAME_MAP_FIELDS).first()
    card = card_values(game, variant, roles, user)
    if game.stage in RUNNING_STAGES:
        set_card_phase(card, game, game.active_phase())
    return {"game": game, "variant": variant, **card, "error": None, "Game": Game}


def lobby_context():
    mode = request.query_params.mode
    if mode not in LOBBY_MODES:
        mode = "open"
    page = query_page()
    rows = (
        LOBBY_MODES[mode]
        .where(lambda g: g.map == Map.id)
        .select(
            *CARD_FIELDS,
            *GAME_MAP_FIELDS,
            orderby=~Game.created_at,
            limitby=((page - 1) * LOBBY_PAGE, page * LOBBY_PAGE + 1),
        )
    )
    has_next = len(rows) > LOBBY_PAGE
    rows = list(rows)[:LOBBY_PAGE]
    listed = [row.games for row in rows]
    variants = {row.games.id: row.maps for row in rows}
    cards = build_cards(listed, variants, auth.user, mode != "finished")
    return {
        "games": listed,
        "mode": mode,
        "page": page,
        "has_next": has_next,
        "variants": variants,
        "cards": cards,
        "Game": Game,
    }


@games.route("/")
def index():
    return lobby_context()


@games.route("/list", template="partials/list.haml")
def partial_list():
    return lobby_context()


@games.route("/<str:gid>/join", methods="post", template="partials/card.haml")
@requires(auth.is_logged, url("auth.login"))
async def join(gid):
    error = await join_game(gid)
    if not error:
        if request.headers.get("hx-request"):
            response.headers["HX-Redirect"] = url(".play", gid)
        else:
            redirect(url(".play", gid))
    game = Game.get(gid)
    if not game:
        abort(404)
    return {**card_context(game, auth.user), "error": error}


async def join_game(gid):
    game = (
        Game.where(
            lambda g: (
                (g.id == gid) & ((g.stage == Game.Stage.PREGAME) | ((g.stage == Game.Stage.GAME) & (g.is_open == True)))
            )
        )
        .select(for_update=True)
        .first()
    )
    if not game:
        return "no game found"
    params = await request.body_params
    if game.players.where(lambda p: p.user == auth.user.id).count():
        return "already in game"
    if game.stage == Game.Stage.PREGAME:
        vault = Vault.where(lambda m: m.user == auth.user.id).select(for_update=True).first()
        if vault.balance < game.bet:
            return "Not enough points"
        if game.players.current().count() == game.players_number:
            return "no slots available"
    if game.access == Game.Access.PASSWORD:
        if params.password != game.password:
            return "wrong password"
    if game.stage == Game.Stage.GAME or game.countries_assignment == Game.Assignment.CHOICE:
        if params.country not in game.available_countries():
            return "Selected country not available"
    try:
        with db.atomic():
            role = game.add_player(auth.user, params.country)
    except Exception as e:
        app.log.exception(e)
        return "Cannot join game"
    if not role:
        return "Selected country not available" if game.stage == Game.Stage.GAME else "Cannot join game"
    if game.stage == Game.Stage.PREGAME and game.players.current().count() == game.players_number:
        game.close()
    db.commit()
    await publish(
        app.ext.Redis.client,
        f"game:{gid}:players",
        "players",
        {
            "country": role.country,
            "name": None if game.anonymous else auth.user.username,
            "is_active": role.is_active,
            "is_ready": role.is_ready,
            "state": role.state,
        },
    )
    return None


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
        vault = Vault.where(lambda m: m.user == auth.user.id).select(for_update=True).first()
        if vault.balance < form.params.bet:
            form.errors.bet = "You have not enough points to set this bet"
            return
        if form.params.bet > 1 and form.params.players_number == 2:
            form.errors.bet = "Maximum bet for 2 players is 1 point"
        #: countries enabled check
        if (
            not form.params.countries
            or len([key for key, val in form.params.countries.items() if val]) < form.params.players_number
        ):
            form.params.countries = dict.fromkeys(variant.countries.keys(), True)
        if form.params.countries_assignment == Game.Assignment.CHOICE:
            if not form.params.countries.get(form.input_params.country_choice):
                form.errors.countries_assignment = "When players have to choose their countries, you must too."
                return
        if form.params.access == Game.Access.PASSWORD:
            if not form.params.password or len(form.params.password) < 4:
                form.errors.password = (
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
    return {
        "form": form,
        "variants": Map.all_latest().select(Map.id, Map.name, orderby=Map.name),
        "balance": auth.user.vault().balance,
        "Game": Game,
        "langs": Game.LANGS,
    }


@games.route("/variant-options", template="partials/variant_options.haml")
@requires(auth.is_logged, url("auth.login"))
def partial_variant_options():
    variant = (
        Map.all_latest()
        .where(Map.id == request.query_params.map)
        .select(Map.id, Map.name, Map.min_players, Map.scs_to_win, Map.countries)
        .first()
    )
    if not variant:
        abort(404)
    return {"variant": variant}


@games.route("/play/<str:gid>")
def play(gid):
    game = Game.get(gid)
    if not game:
        abort(404)
    variant = Map.get(game.map)
    scs = game.target_sc or variant.scs_to_win
    players = game.players.current().join("user").select()
    player = None
    if auth.is_logged():
        player = game.player(auth.user)
        Notification.read(auth.user.id, Game.tablename, game.id, PAGE_KINDS)

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

    return {
        "game": game,
        "variant": variant,
        "board_svg": board_svg,
        "country_css": "\n".join(css),
        "player_key": keys.get(player.country) if player else None,
        **clock_values(game),
        "scs": scs,
        "chats": {"global": 1},
        "players": players,
        "player_id": player.id if player else None,
        "player_country": player.country if player else None,
        "player_ready": player.is_ready if player else False,
        "player_active": player.is_active if player else False,
        "notifications_read": json.dumps({"subject_type": Game.tablename, "subject_id": game.id, "kinds": PAGE_KINDS}),
        "statscol": 6,
    }


def clock_values(game):
    timer = game.timer()
    left = timer.d * 86400 + timer.h * 3600 + timer.m * 60 + timer.s
    running = game.stage == Game.Stage.GAME
    if not game.next_process_at or not running:
        countdown, deadline, deadline_iso, left_pct = "--:--:--", "", "", 0
    else:
        if timer.d:
            countdown = f"{timer.d}d {timer.h:02d}:{timer.m:02d}"
        else:
            countdown = f"{timer.h:02d}:{timer.m:02d}:{timer.s:02d}"
        deadline = game.next_process_at.strftime("%d %b %H:%M UTC")
        #: naive UTC
        at = game.next_process_at
        deadline_iso = (at.replace(tzinfo=timezone.utc) if at.tzinfo is None else at).isoformat()
        left_pct = max(0, min(100, round(100 * left / max(1, game.phase_time * 60))))
    phase = game.active_phase() if running else None
    return {
        "countdown": countdown,
        "deadline": deadline,
        "deadline_iso": deadline_iso,
        "left_pct": left_pct,
        "phase_time": game.phase_time,
        "resolved": phase.created_at.strftime("%d %b %H:%M UTC") if phase else "",
        "timer": timer,
    }


@games.route("/play/<str:gid>/clock", template="partials/clock.haml")
def partial_clock(gid):
    game = Game.get(gid)
    if not game:
        abort(404)
    return clock_values(game)
