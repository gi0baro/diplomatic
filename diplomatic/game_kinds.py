from datetime import datetime

from emmett import T, sdict, url

from .helpers.games import DEADLINE_FORMAT, duration
from .models.game import GamePhase, GameRole
from .notifications import Kind, register


OPEN_GAME = "Open the game:"


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
    #: a draw leaves no winner to name, whatever the role's own result
    return data["state"] if data["winner"] else GameRole.State.DRAWN


_OVER_LINES = {
    GameRole.State.WON: T("You won game {name}."),
    GameRole.State.SURVIVED: T("Game {name} is over: {winner} won, you survived."),
    GameRole.State.DEFEATED: T("Game {name} is over: {winner} won, you were defeated."),
    GameRole.State.DRAWN: T("Game {name} ended in a draw."),
}


def _over(data):
    return str(_OVER_LINES[_over_state(data)].format(**data))


def _facts(data):
    #: the stored facts as the emails word them: the turn type first, dates in UTC, the site's turn length
    rv = dict(data)
    if "type" in data:
        phase = sdict(data)
        rv.update(turn=GamePhase.label(phase), type=GamePhase.type_label(phase))
    if "deadline" in data:
        rv["deadline"] = datetime.fromisoformat(data["deadline"]).strftime(DEADLINE_FORMAT)
    if "turn_length" in data:
        rv["turn_length"] = duration(data["turn_length"])
    return rv


def _email(*paragraphs):
    text = "\n\n".join(paragraphs)
    return lambda data: text.format(**_facts(data))


_MESSAGES = (
    "Other players have written to you in game {name} ({variant}), where you play {country}. "
    "Their messages are waiting in the game's chat."
)
_MESSAGES_PREGAME = _email(_MESSAGES)
_MESSAGES_STARTED = _email(_MESSAGES, "The current turn, {type} ({turn}), closes on {deadline}.")


def _messages(data):
    #: the turn exists only once the game has started
    return (_MESSAGES_STARTED if "deadline" in data else _MESSAGES_PREGAME)(data)


_OVER_END = "Every turn of the game, and its final position, stay on its page."
_OVER_BODIES = {
    GameRole.State.WON: _email(
        "Game {name} ({variant}) is over, and you won it as {country}. Well played.",
        _OVER_END,
    ),
    GameRole.State.SURVIVED: _email(
        "Game {name} ({variant}) is over: {winner} won. You survived to the end as {country}.",
        _OVER_END,
    ),
    GameRole.State.DEFEATED: _email(
        "Game {name} ({variant}) is over: {winner} won. {country}, your country, ended without supply centres.",
        _OVER_END,
    ),
    GameRole.State.DRAWN: _email(
        "Game {name} ({variant}) is over: it ended in a draw. You played {country}.",
        _OVER_END,
    ),
}


def _over_body(data):
    return _OVER_BODIES[_over_state(data)](data)


def _game_kind(key, label, text, subject, body):
    register(Kind(key, label, text, _email(subject), body, _game_page, OPEN_GAME))


_game_kind(
    "game.started",
    T("Game started"),
    _line(T("Game {name} has started.")),
    "game {name} has started",
    _email(
        "The game {name} you joined has started: {variant}, {players} players, one turn every {turn_length}.",
        "You play {country}. The first turn, {type} ({turn}), is open, and your orders are due by {deadline}.",
    ),
)
_game_kind(
    "game.phase",
    T("New turn"),
    _turn,
    "the next turn is open in game {name}",
    _email(
        "{type} ({turn}) is now open in game {name} ({variant}), where you play {country}.",
        "The previous turn has been resolved. Have a look at the board and send your orders by {deadline}.",
    ),
)
_game_kind(
    "game.messages",
    T("New messages"),
    _line(T("You have new messages in game {name}.")),
    "new messages in game {name}",
    _messages,
)
_game_kind(
    "game.missed",
    T("Missed turn"),
    _line(T("You missed a turn in game {name}.")),
    "you missed a turn in game {name}",
    _email(
        "A turn was resolved in game {name} ({variant}) without orders from you for {country}.",
        "If you miss another one, your country goes into civil disorder and another player can take it over. "
        "The next turn, {type} ({turn}), is open and closes on {deadline}.",
    ),
)
_game_kind(
    "game.disorder",
    T("Civil disorder"),
    _line(T("{country} is in civil disorder in game {name} and can be taken over.")),
    "{country} is in civil disorder in game {name}",
    _email(
        "You missed another turn in game {name} ({variant}), and {country}, your country, is now in civil disorder.",
        "While it is, any other player can take it over, and you would be out of the game. "
        "It is still yours: send orders for the open turn, {type} ({turn}), before {deadline}, to take it back.",
    ),
)
_game_kind(
    "game.taken_over",
    T("Country taken over"),
    _line(T("You lost {country} in game {name}: another player took it over.")),
    "you lost {country} in game {name}",
    _email(
        "{country}, your country in game {name} ({variant}), was in civil disorder "
        "and another player has taken it over.",
        "You are out of that game. You can still follow it from its page.",
    ),
)
_game_kind(
    "game.defeated",
    T("Eliminated"),
    _line(T("You were eliminated from game {name}.")),
    "you were eliminated from game {name}",
    _email(
        "{country}, your country in game {name} ({variant}), has no units or supply centres left: you are eliminated.",
        "The game goes on without you, and you can keep following it from its page.",
    ),
)
register(
    Kind(
        "game.cancelled",
        T("Game cancelled"),
        _line(T("Game {name} was cancelled: not enough players joined.")),
        _email("game {name} was cancelled"),
        _email(
            "The game {name} ({variant}) you joined did not reach its {players} players in time, and it was cancelled.",
            "The points you staked are back in your balance.",
        ),
    )
)
_game_kind("game.over", T("Game over"), _over, "game {name} is over", _over_body)

#: what the game page shows (the turn toast, the chat): read when the page loads and by the board as it lands
PAGE_KINDS = ("game.started", "game.phase", "game.over", "game.messages")
