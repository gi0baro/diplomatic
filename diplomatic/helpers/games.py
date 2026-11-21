from collections import defaultdict
from datetime import timezone

from emmett import T

from .. import Game, GamePhase, GameRole, Map


CARD_FIELDS = [field for field in Game.table if field.name not in ("history", "chat_history", "password")]
GAME_MAP_FIELDS = (Map.id, Map.name, Map.scs_to_win)
DEADLINE_FORMAT = "%d %b %H:%M UTC"
PRESS_LABELS = {
    Game.Press.ALL: (T("Open press"), T("Open")),
    Game.Press.GLOBAL: (T("Global press only"), T("Global only")),
    Game.Press.NONE: (T("No press"), T("None")),
}


def duration(minutes):
    #: as human() in games/create.haml: "1 day 12 h 30 min", zero parts omitted
    days, hours, rest = minutes // 1440, minutes // 60 % 24, minutes % 60
    parts = []
    if days:
        parts.append(f"{days} day" if days == 1 else f"{days} days")
    if hours:
        parts.append(f"{hours} h")
    if rest:
        parts.append(f"{rest} min")
    return " ".join(parts)


def iso_utc(at):
    return (at.replace(tzinfo=timezone.utc) if at.tzinfo is None else at).isoformat()


def card_rules(game):
    if game.stage == Game.Stage.OVER:
        return []
    rules = []
    if game.build_everywhere:
        rules.append(("hammer", T("Build anywhere")))
    if game.stage == Game.Stage.PREGAME and game.is_open and game.build_on_start:
        rules.append(("flag", T("Builds on start")))
    if game.stage == Game.Stage.PREGAME and game.is_open and game.countries_assignment == Game.Assignment.RANDOM:
        rules.append(("die", T("Random countries")))
    if game.anonymous:
        rules.append(("eye-off", T("Anonymous")))
    return rules


def card_values(game, variant, roles, user):
    role = next((r for r in roles if user and r.user == user.id), None)
    choices = None
    if (
        user
        and not role
        and game.is_open
        and (game.stage == Game.Stage.GAME or game.countries_assignment == Game.Assignment.CHOICE)
    ):
        choices = game.available_countries()
    at = game.next_process_at
    return {
        "count": sum(1 for r in roles if r.state != GameRole.State.LEFT),
        "role": role,
        "choices": choices,
        "winner": next((r.country for r in roles if r.state == GameRole.State.WON), None),
        "deadline_iso": iso_utc(at) if at else "",
        "deadline": at.strftime(DEADLINE_FORMAT) if at else "",
        "status": Game.Stage(game.stage).label,
        "turn": None,
        "rules": card_rules(game),
        "skips": ", ".join(day[:3].capitalize() for day in Game.PROC_DAYS if game.skip_processing.get(day)),
        "centers": game.target_sc or variant.scs_to_win,
        "press": PRESS_LABELS[game.press_type][0],
        "press_short": PRESS_LABELS[game.press_type][1],
        "lang": Game.LANGS[game.lang] if game.press_type != Game.Press.NONE else None,
    }


def set_card_phase(card, game, phase):
    if not phase:
        return
    card["turn"] = GamePhase.label(phase)
    if game.stage == Game.Stage.GAME:
        card["status"] = GamePhase.type_label(phase)


def build_cards(games, variants, user, running=False):
    ids = [game.id for game in games]
    roles = defaultdict(list)
    if ids:
        for role in GameRole.where(lambda m: m.game.belongs(ids)).select():
            roles[role.game].append(role)
    phases = {}
    if running:
        open_phases = GamePhase.where(lambda m: m.game.belongs(ids) & (m.stage == GamePhase.Stage.OPEN))
        fields = (GamePhase.id, GamePhase.game, GamePhase.year, GamePhase.season, GamePhase.type)
        phases = {phase.game: phase for phase in open_phases.select(*fields)}
    cards = {game.id: card_values(game, variants[game.id], roles[game.id], user) for game in games}
    for game in games:
        set_card_phase(cards[game.id], game, phases.get(game.id))
    return cards
