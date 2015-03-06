# -*- coding: utf-8 -*-

from datetime import datetime
from nudiplomacy import db, NObject, NSubscription, queue


_canceled_mail_text = """Dear %(user)s,
the game %(game)s was canceled since not enough players joined.
You're credits was funded back to you.

See you soon,
nuDiplomacy team
"""


def game_canceled(game):
    nchan = "game_"+str(game.id)
    nobj = NObject.get_one(nchan, "game_process")
    users = NSubscription.find_subscribers(nchan, nobj)
    for user in users:
        db.NEvent.insert(
            object=nobj, recipient=user, actor="game "+game.name,
            data={"msg": "Game was canceled", "type": "game"},
            date=datetime.utcnow()
        )
        usettings = db.UserSettings(user=user)
        if usettings.notification['email']:
            recipient = db.User(id=user)
            queue.mail_send(
                to=recipient.email,
                subject="Game "+game.name+" was canceled",
                message=_canceled_mail_text % dict(
                    user=recipient.nickname,
                    game=game.name
                )
            )


_new_phase_mail_text = """Dear %(user)s,
the game %(game)s was updated to a new phase.
Review what's happened and set your orders for the next turn!

See you soon,
nuDiplomacy team
"""


def game_new_phase(game):
    nchan = "game_"+str(game.id)
    nobj = NObject.get_one(nchan, "game_process")
    users = NSubscription.find_subscribers(nchan, nobj)
    for user in users:
        db.NEvent.insert(
            object=nobj, recipient=user, actor="game "+game.name,
            data={"msg": "Game has been processed", "type": "game"},
            date=datetime.utcnow()
        )
        usettings = db.UserSettings(user=user)
        if usettings.notification['email']:
            recipient = db.User(id=user)
            queue.mail_send(
                to=recipient.email,
                subject="Game "+game.name+" has been updated",
                message=_new_phase_mail_text % dict(
                    user=recipient.nickname,
                    game=game.name
                )
            )
