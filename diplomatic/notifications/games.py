from datetime import datetime

from emmett import T, sdict, url

from ..helpers.games import DEADLINE_FORMAT, duration
from ..models.game import GamePhase, GameRole
from . import Kind, register


def _game_page(notification):
    return url("front.games.play", notification.subject_id)


def _line(line):
    return lambda data: str(line.format(**data))


def _turn(data):
    phase = sdict(data)
    return str(
        T("New turn in game {name}: {turn}, {type}.").format(
            name=data["name"], turn=GamePhase.label(phase), type=GamePhase.type_label(phase)
        )
    )


def _over_state(data):
    return data["state"] if data["winner"] else GameRole.State.DRAWN


_OVER_LINES = {
    GameRole.State.WON: T("You won game {name}."),
    GameRole.State.SURVIVED: T("Game {name} is over: {winner} won, you survived."),
    GameRole.State.DEFEATED: T("Game {name} is over: {winner} won, you were defeated."),
    GameRole.State.DRAWN: T("Game {name} ended in a draw."),
}


def _over(data):
    return str(_OVER_LINES[_over_state(data)].format(**data))


def _context(data):
    rv = {"turn": None, "type": None, "deadline": None, "result": None, "State": GameRole.State, **data}
    if "type" in data:
        phase = sdict(data)
        rv.update(turn=GamePhase.label(phase), type=GamePhase.type_label(phase))
    if "deadline" in data:
        rv["deadline"] = datetime.fromisoformat(data["deadline"]).strftime(DEADLINE_FORMAT)
    if "turn_length" in data:
        rv["turn_length"] = duration(data["turn_length"])
    if "state" in data:
        rv["result"] = _over_state(data)
    return rv


def _game_kind(key, label, text, subject, action=_game_page):
    register(Kind(key, label, text, subject, _context, action))


_game_kind("game.started", T("Game started"), _line(T("Game {name} has started.")), "game {name} has started")
_game_kind("game.phase", T("New turn"), _turn, "the next turn is open in game {name}")
_game_kind(
    "game.messages",
    T("New messages"),
    _line(T("You have new messages in game {name}.")),
    "new messages in game {name}",
)
_game_kind(
    "game.missed",
    T("Missed turn"),
    _line(T("You missed a turn in game {name}.")),
    "you missed a turn in game {name}",
)
_game_kind(
    "game.disorder",
    T("Civil disorder"),
    _line(T("{country} is in civil disorder in game {name} and can be taken over.")),
    "{country} is in civil disorder in game {name}",
)
_game_kind(
    "game.taken_over",
    T("Country taken over"),
    _line(T("You lost {country} in game {name}: another player took it over.")),
    "you lost {country} in game {name}",
)
_game_kind(
    "game.defeated",
    T("Eliminated"),
    _line(T("You were eliminated from game {name}.")),
    "you were eliminated from game {name}",
)
_game_kind(
    "game.cancelled",
    T("Game cancelled"),
    _line(T("Game {name} was cancelled: not enough players joined.")),
    "game {name} was cancelled",
    action=None,
)
_game_kind("game.over", T("Game over"), _over, "game {name} is over")

LIVE_KINDS = ("game.started", "game.phase", "game.over")
PAGE_KINDS = (*LIVE_KINDS, "game.messages")
