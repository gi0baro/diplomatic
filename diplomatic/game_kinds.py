from emmett import T, sdict, url

from .models.game import GamePhase, GameRole
from .notifications import Kind, register


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


_OVER_LINES = {
    GameRole.State.WON: T("You won game {name}."),
    GameRole.State.SURVIVED: T("Game {name} is over: {winner} won, you survived."),
    GameRole.State.DEFEATED: T("Game {name} is over: {winner} won, you were defeated."),
    GameRole.State.DRAWN: T("Game {name} ended in a draw."),
}


def _over(data):
    #: a draw leaves no winner to name, whatever the role's own result
    state = data["state"] if data["winner"] else GameRole.State.DRAWN
    return str(_OVER_LINES[state].format(**data))


register(Kind("game.started", T("Game started"), _line(T("Game {name} has started.")), _game_page))
register(Kind("game.phase", T("New turn"), _turn, _game_page))
register(Kind("game.messages", T("New messages"), _line(T("You have new messages in game {name}.")), _game_page))
register(Kind("game.missed", T("Missed turn"), _line(T("You missed a turn in game {name}.")), _game_page))
register(
    Kind(
        "game.disorder",
        T("Civil disorder"),
        _line(T("{country} is in civil disorder in game {name} and can be taken over.")),
        _game_page,
    )
)
register(
    Kind(
        "game.taken_over",
        T("Country taken over"),
        _line(T("You lost {country} in game {name}: another player took it over.")),
        _game_page,
    )
)
register(Kind("game.defeated", T("Eliminated"), _line(T("You were eliminated from game {name}.")), _game_page))
register(Kind("game.cancelled", T("Game cancelled"), _line(T("Game {name} was cancelled: not enough players joined."))))
register(Kind("game.over", T("Game over"), _over, _game_page))
