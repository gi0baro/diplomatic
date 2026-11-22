import re
import uuid
from collections import defaultdict

import click
import yaml
from diplomatico.constants import OrderType, Phase, Season, Troop
from emmett import url

from diplomatico import Board

from . import ChatMember, ChatMessage, ChatRoom, Game, GameRole, Map, Order, User, Vault, db
from .diplomacy import process_order


KEYS = ("variant", "name", "players", "settings", "chat", "phases", "stop")
CHOICES = {
    "pot_type": Game.PotType,
    "press_type": Game.Press,
    "access": Game.Access,
    "starts_on": Game.Start,
    "countries_assignment": Game.Assignment,
}
INTS = ("bet", "phase_time", "join_time", "max_years", "target_sc")
BOOLS = ("build_everywhere", "build_on_start", "anonymous")
SETTINGS = ("lang", "password", "skip_processing", *INTS, *BOOLS, *CHOICES)
#: local play: the smallest bet (the only one a 2-player game takes), the countries the scenario
#: assigns, and the longest phase the validation takes (its range excludes the end, ~10 days) so a
#: running scheduler does not process the game
DEFAULTS = {"lang": "en", "bet": 1, "phase_time": 60 * 24 * 10 - 1, "countries_assignment": Game.Assignment.CHOICE}
COASTS = {"NC": "North", "SC": "South", "EC": "East", "WC": "West"}
PROVINCE = r"[A-Z]{2,4}(?:/[A-Z]{2})?"
ORDER = re.compile(
    rf"(?P<unit>{PROVINCE})(?:"
    r"\s+(?P<hold>H)"
    rf"|\s*-\s*(?P<move>{PROVINCE})(?P<via>\s+VIA)?"
    rf"|\s+S\s+(?P<supported>{PROVINCE})(?:\s*-\s*(?P<support_dst>{PROVINCE}))?"
    rf"|\s+C\s+(?P<convoyed>{PROVINCE})\s*-\s*(?P<convoy_dst>{PROVINCE})"
    rf"|\s+R\s+(?P<retreat>{PROVINCE})"
    r"|\s+B\s+(?P<build>A|F(?:/[A-Z]{2})?)"
    r"|\s+(?P<disband>D)"
    r")"
)
#: the generated general chat (`general: <count>`)
LINES = [
    "Morning all.",
    "Anyone up for a non-aggression pact this year?",
    "I have no designs on the north, whatever the rumours say.",
    "Those fleets are purely defensive.",
    "Let's talk before the deadline, please.",
    "Fine by me.",
    "I'd rather see the board settle a bit before committing to anything long term; "
    "too many armies are pointed at too few centres right now.",
    "Who moved into the Channel?",
    "Not me.",
    "Congratulations on the build.",
    "We all know how this ends if nobody holds the line in the middle.",
    "Ready when you are.",
    "Can we push the deadline? Busy week.",
    "Bounce again, really?",
    "Noted.",
    "Peace in our time.",
]


class OrderError(ValueError):
    pass


def fail(message):
    raise click.ClickException(message)


def load_scenario(path):
    with open(path) as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict):
        fail(f"{path}: a scenario is a mapping")
    unknown = set(doc) - set(KEYS)
    if unknown:
        fail(f"{path}: unknown keys {', '.join(sorted(unknown))} (allowed: {', '.join(KEYS)})")
    for key in ("variant", "name"):
        if not isinstance(doc.get(key), str) or not doc[key]:
            fail(f"{path}: '{key}' must be a string")
    players = doc.get("players")
    if (
        not isinstance(players, dict)
        or not players
        or not all(isinstance(country, str) and isinstance(user, str) for country, user in players.items())
    ):
        fail(f"{path}: 'players' maps countries to usernames")
    if len(set(players.values())) != len(players):
        fail(f"{path}: 'players': a user plays one country per game")
    settings = doc.get("settings") or {}
    if not isinstance(settings, dict):
        fail(f"{path}: 'settings' is a mapping of game fields")
    phases = doc.get("phases") or []
    if not isinstance(phases, list):
        fail(f"{path}: 'phases' is a list, one entry per phase")
    entries = []
    for number, entry in enumerate(phases, 1):
        entry = entry or {}
        if not isinstance(entry, dict):
            fail(f"{path}: phase {number}: a mapping of countries to their orders")
        for country, orders in entry.items():
            if country not in players:
                fail(f"{path}: phase {number}: {country} is not a player")
            if orders is not None and (not isinstance(orders, list) or not all(isinstance(o, str) for o in orders)):
                fail(f"{path}: phase {number}: {country}'s orders are a list of strings")
        entries.append({country: orders or [] for country, orders in entry.items()})
    stop = doc.get("stop") or {}
    if not isinstance(stop, dict) or set(stop) - {"ready"}:
        fail(f"{path}: 'stop' takes 'ready' only")
    ready = stop.get("ready") or []
    if not isinstance(ready, list) or any(country not in players for country in ready):
        fail(f"{path}: 'stop: ready' is a list of players' countries")
    return {
        "variant": doc["variant"],
        "name": doc["name"],
        "players": players,
        "settings": settings,
        "chat": _load_chat(path, doc.get("chat") or {}, list(players)),
        "phases": entries,
        "ready": ready,
    }


def _load_chat(path, chat, countries):
    if not isinstance(chat, dict) or set(chat) - {"general", "direct"}:
        fail(f"{path}: 'chat' takes 'general' and 'direct'")
    general = chat.get("general") or []
    if isinstance(general, int) and not isinstance(general, bool):
        general = [
            [countries[idx % len(countries)], f"{idx + 1}. {LINES[(idx * 7) % len(LINES)]}"] for idx in range(general)
        ]
    if not isinstance(general, list) or not all(
        isinstance(entry, list) and len(entry) == 2 and entry[0] in countries and isinstance(entry[1], str)
        for entry in general
    ):
        fail(f"{path}: 'chat: general' is a count or a list of [country, text]")
    direct = chat.get("direct") or []
    if not isinstance(direct, list) or not all(
        isinstance(entry, list)
        and len(entry) == 3
        and entry[0] in countries
        and entry[1] in countries
        and entry[0] != entry[1]
        and isinstance(entry[2], str)
        for entry in direct
    ):
        fail(f"{path}: 'chat: direct' is a list of [sender, recipient, text] between two players")
    return {"general": general, "direct": direct}


def play(scenario):
    variant = _variant(scenario["variant"])
    unknown = [country for country in scenario["players"] if country not in variant.countries]
    if unknown:
        fail(f"{', '.join(unknown)}: not in {variant.name} ({', '.join(variant.countries)})")
    users = {country: _user(username) for country, username in scenario["players"].items()}
    db.commit()
    game = _create(scenario, variant, users)
    try:
        _join(game, users)
        _start(game)
        _chat(game, scenario["chat"])
        _play(game, variant, scenario["phases"])
        _stop(game, users, scenario["ready"])
    except click.ClickException as e:
        raise click.ClickException(f"{e.message}\nThe game is left as it is: {_url(game)}")
    _report(game, variant, users)


def _variant(name):
    rows = [row for row in Map.all_latest().select(Map.id, Map.name) if row.name.lower() == name.lower()]
    if not rows:
        fail(f"variant '{name}' is not loaded (emmett load-maps)")
    return Map.get(rows[0].id)


def _user(username):
    #: as create_test_data
    user = User.get(username=username)
    if not user:
        res = User.create(email=f"{username}@diplomatic.com", password="foobar", username=username)
        if res.errors:
            fail(f"user {username}: {dict(res.errors)}")
        user = User.get(res.id)
        print(f"Created user {username} (password foobar)")
    return user


def _settings(settings):
    rv = dict(DEFAULTS)
    for key, value in settings.items():
        if key not in SETTINGS:
            fail(f"settings: unknown '{key}' (allowed: {', '.join(SETTINGS)})")
        if key in CHOICES:
            member = CHOICES[key].__members__.get(str(value).upper())
            if member is None:
                fail(f"settings: '{key}' is one of {', '.join(CHOICES[key].__members__)}")
            value = member
        elif key in INTS and (not isinstance(value, int) or isinstance(value, bool)):
            fail(f"settings: '{key}' is an integer")
        elif key in BOOLS and not isinstance(value, bool):
            fail(f"settings: '{key}' is a boolean")
        rv[key] = value
    return rv


def _create(scenario, variant, users):
    #: as the create form: its checks, then the game row with the fields the form posts
    settings = _settings(scenario["settings"])
    players_number = len(users)
    if not variant.min_players <= players_number <= len(variant.countries):
        fail(f"{variant.name} takes {variant.min_players} to {len(variant.countries)} players")
    if settings["bet"] > 1 and players_number == 2:
        fail("Maximum bet for 2 players is 1 point")
    if settings.get("access") == Game.Access.PASSWORD and len(str(settings.get("password") or "")) < 4:
        fail("When you password-protect your game, the password must be at least 4 characters long")
    short = []
    for user in users.values():
        vault = Vault.get(user=user.id)
        if vault.balance < settings["bet"]:
            short.append(f"{user.username} has {vault.balance}")
    if short:
        fail(f"Not enough points for a bet of {settings['bet']}: {', '.join(short)}")
    res = Game.create(
        name=f"{scenario['name']} {uuid.uuid4().hex[:6]}",
        map=variant.id,
        user=next(iter(users.values())).id,
        players_number=players_number,
        countries={country: country in users for country in variant.countries},
        **settings,
    )
    if res.errors:
        fail(f"game: {dict(res.errors)}")
    db.commit()
    return Game.get(res.id)


def _join(game, users):
    #: as game_join, one player after the other; then close and claim in one transaction, so a
    #: running scheduler never sees the game closed and unclaimed
    for country, user in users.items():
        row = Game.in_stage(Game.Stage.PREGAME).where(lambda g: g.id == game.id).select(for_update=True).first()
        vault = Vault.where(lambda m: m.user == user.id).select(for_update=True).first()
        if vault.balance < row.bet:
            fail(f"{user.username} ({country}): Not enough points")
        if row.players.count() == row.players_number:
            fail(f"{user.username} ({country}): no slots available")
        with db.atomic():
            role = row.add_player(user, country)
        if not role or role.country != country:
            fail(f"{user.username} cannot join as {country}")
    row = Game.get(game.id)
    if not row.close():
        fail("the game could not be closed")
    if not row.claim(Game.Stage.PREGAME):
        fail("the game could not be claimed for its start")
    db.commit()


def _start(game):
    Game.get(game.id).start()
    db.commit()


def _chat(game, chat):
    if not chat["general"] and not chat["direct"]:
        return
    game = Game.get(game.id)
    if game.press_type == Game.Press.NONE:
        fail("chat: in-game messaging is disabled (press_type NONE)")
    if chat["direct"] and game.press_type != Game.Press.ALL:
        fail("chat: direct messages need press_type ALL")
    countries = {str(role.id): role.country for role in game.players.current().select()}
    rooms = {str(room.id): room for room in game.chat_rooms.select()}
    members = defaultdict(dict)
    for member in ChatMember.where(lambda m: m.room.belongs(list(rooms))).select():
        members[str(member.room)][countries[str(member.player)]] = member.id
    general = next(rid for rid, room in rooms.items() if room.type == ChatRoom.Type.GENERAL)
    direct = {frozenset(members[rid]): rid for rid, room in rooms.items() if room.type == ChatRoom.Type.DM}
    messages = [(general, sender, text) for sender, text in chat["general"]]
    messages += [(direct[frozenset((sender, recipient))], sender, text) for sender, recipient, text in chat["direct"]]
    for room, sender, text in messages:
        #: as new_chat_message: the sender's membership of the room
        res = ChatMessage.create(room=room, sender=members[room][sender], text=text)
        if res.errors:
            fail(f"chat: {sender}: '{text}': {dict(res.errors)}")
    db.commit()
    print(f"Chat: {len(chat['general'])} general, {len(chat['direct'])} direct message(s)")


def _play(game, variant, phases):
    for number, entry in enumerate(phases, 1):
        game = Game.get(game.id)
        if game.stage != Game.Stage.GAME or game.is_ready:
            fail(f"phase {number}: the game does not take orders ({Game.Stage(game.stage).name})")
        phase = game.active_phase()
        label = f"phase {number} ({_label(phase)})"
        given = sum(_orders(game, variant, phase, label, country, orders) for country, orders in entry.items())
        #: as manage_games, then process_game
        if not game.claim(Game.Stage.GAME):
            fail(f"{label}: the game could not be claimed for processing")
        db.commit()
        crashed = not Game.get(game.id).process()
        db.commit()
        game = Game.get(game.id)
        if crashed or game.stage == Game.Stage.CRASH:
            fail(f"{label}: processing crashed, the game is in stage CRASH (the traceback is in the log)")
        if game.stage == Game.Stage.OVER and number < len(phases):
            fail(f"{label}: the game is over ({_state(game)}), {len(phases) - number} scenario phase(s) left")
        print(f"{label}: {given} order(s), processed: {_state(game)}")


def _orders(game, variant, phase, label, country, orders):
    #: as order_save, one order after the other
    if not orders:
        return 0
    where = f"{label}, {country}"
    role = game.players.current().where(lambda m: m.country == country).select().first()
    if not role.is_active or role.state != GameRole.State.PLAYING:
        fail(f"{where}: Cannot update orders in this turn")
    if role.is_ready:
        fail(f"{where}: Cannot update orders when ready")
    rows = {row.territory: row for row in phase.orders.where(lambda m: m.game_role == role.id).select()}
    given = set()
    for text in orders:
        try:
            territory, kind, data = parse_order(text, variant, phase, country)
        except OrderError as e:
            fail(f"{where}: '{text}': {e}")
        row = rows.get(territory)
        if not row:
            fail(f"{where}: '{text}': {country} has no order to give in {variant.codes[territory]}")
        if territory in given:
            fail(f"{where}: '{text}': a second order for {variant.codes[territory]}")
        given.add(territory)
        data, errors = process_order(country, game, territory, {**data, "type": int(kind)})
        order_type = data.pop("type")
        if errors:
            reasons = "; ".join(f"{variant.codes.get(key, key)}: {reason}" for key, reason in errors.items())
            fail(f"{where}: '{text}' rejected: {reasons}")
        res = Order.where(lambda m: m.id == row.id).validate_and_update(type=order_type, data=data)
        if res.errors:
            fail(f"{where}: '{text}': {dict(res.errors)}")
        db.commit()
    return len(given)


def parse_order(text, variant, phase, country):
    """The order row's territory, type and data as the client sends them to order_save
    (game.coffee `addOrder`, interactions.coffee); the unit is read from the phase's board."""
    match = ORDER.fullmatch(" ".join(text.upper().split()))
    if not match:
        raise OrderError("unparsable (forms: X H, X-Y, X-Y via, X S Y, X S Y-Z, X C Y-Z, X R Y, X B A, X B F, X D)")
    ids = {code: pid for pid, code in variant["codes"].items()}

    def province(token):
        code, _, coast = token.partition("/")
        if code not in ids:
            raise OrderError(f"unknown province {code}")
        return ids[code], _coast(variant, ids[code], coast) if coast else None

    unit, _ = province(match["unit"])  #: the unit's coast is the board's
    fleet = unit in phase.troops.get(country, {}).get("fleets", [])
    if match["hold"]:
        return unit, OrderType.HOLD, {}
    if match["disband"]:
        return unit, OrderType.DISBAND, {}
    if match["build"]:
        troop, _, coast = match["build"].partition("/")
        if troop == "A":
            return unit, OrderType.BUILD, {"troop": int(Troop.ARMY)}
        data = {"troop": int(Troop.FLEET)}
        if coast:
            data["coast"] = _coast(variant, unit, coast)
        return unit, OrderType.BUILD, data
    if match["move"] and match["via"]:
        dst, _ = province(match["move"])
        return unit, OrderType.MOVE, _convoyed(variant, phase, country, unit, dst)
    if match["move"] or match["retreat"]:
        dst, coast = province(match["move"] or match["retreat"])
        kind = OrderType.MOVE if match["move"] else OrderType.RETREAT
        return unit, kind, _step(variant, unit, phase.coasts.get(unit), dst, coast, fleet)
    if match["convoyed"]:
        src, _ = province(match["convoyed"])
        dst, _ = province(match["convoy_dst"])
        return unit, OrderType.CONVOY, {"dst": dst, "src": src}
    #: supports carry no coast (the client sends src and dst only)
    supported, _ = province(match["supported"])
    if match["support_dst"]:
        dst, _ = province(match["support_dst"])
        return unit, OrderType.SUPPORT_MOVE, {"dst": dst, "src": supported}
    return unit, OrderType.SUPPORT_HOLD, {"dst": supported}


def _coast(variant, territory, abbreviation):
    #: the coast's index in the variant's coast_names, as the client sends it
    if abbreviation not in COASTS:
        raise OrderError(f"unknown coast /{abbreviation} (/{', /'.join(COASTS)})")
    names = variant["coast_names"].get(territory) or []
    if COASTS[abbreviation] not in names:
        raise OrderError(f"{variant['codes'][territory]} has no {COASTS[abbreviation].lower()} coast")
    return names.index(COASTS[abbreviation])


def _step(variant, unit, unit_coast, dst, coast, fleet):
    #: a fleet reaching one coast only of a multi-coast province gets it, as in the client;
    #: from a multi-coast province, only the coasts paired with the one the fleet is on count
    data = {"dst": dst}
    if dst in variant["multi_coasts"] and coast is None and fleet:
        reach = [
            idx
            for idx, links in enumerate(variant["links"]["multi_coasts"][dst])
            if unit in links and (links[unit] is None or unit_coast in links[unit])
        ]
        if len(reach) > 1:
            names = ", ".join(f"/{key}" for key, name in COASTS.items() if name in variant["coast_names"][dst])
            raise OrderError(f"{variant['codes'][dst]} needs a coast ({names})")
        coast = reach[0] if reach else None
    if coast is not None:
        data["coast"] = coast
    return data


def _convoyed(variant, phase, country, unit, dst):
    #: the client sends one route; the shortest made of the player's fleets, else the shortest
    routes = Board(variant, phase.troops, phase.coasts).convoy_routes(unit, dst)
    fleets = set(phase.troops.get(country, {}).get("fleets", []))
    mine = [route for route in routes if set(route) <= fleets]
    data = {"dst": dst, "through": True}
    if routes:
        data["routes"] = [min(mine or routes, key=len)]
    return data


def _stop(game, users, ready):
    #: as player_ready: the role's flag, then the game's when everyone is ready
    for country in ready:
        row = Game.get(id=game.id, is_ready=False, stage=Game.Stage.GAME)
        if not row:
            fail(f"stop: {country} cannot be ready, the game is not waiting for orders")
        roles = row.players.actionable().where(lambda m: m.user == users[country].id)
        if not roles.update(is_ready=True):
            fail(f"stop: {country} has no orders to give, cannot be ready")
        db.commit()
        if row.players_all_ready():
            row.set_ready()
        db.commit()


def _label(phase):
    season = "Winter" if phase.type == Phase.BUILDS else Season(phase.season).name.title()
    return f"{season} {phase.year} {Phase(phase.type).name.lower()}"


def _state(game):
    if game.stage == Game.Stage.OVER:
        winners = [role.country for role in game.players.select() if role.state == GameRole.State.WON]
        return f"over, {winners[0]} won" if winners else "over, no winner"
    if game.stage != Game.Stage.GAME:
        return Game.Stage(game.stage).name
    rv = f"{_label(game.active_phase())} open"
    ready = [role.country for role in game.players.current().select() if role.is_ready]
    if ready:
        rv += f", ready: {', '.join(ready)}"
    if game.is_ready:
        rv += " (everyone: the scheduler processes it next)"
    return rv


def _url(game):
    try:
        return url("front.games.play", game.id)
    except RuntimeError:
        #: the page routes are registered by diplomatic.web, not loaded under `-a diplomatic`
        return f"/games/play/{game.id}"


def _report(game, variant, users):
    game = Game.get(game.id)
    width = max(len(country) for country in users)
    print(f'Game "{game.name}" ({variant.name}): {_url(game)}')
    for country, user in users.items():
        print(f"  {country:<{width}}  {user.username}")
    print(f"  {_state(game)}")
