# -*- coding: utf-8 -*-

from datetime import datetime

from diplomatic import NObject, NSubscription, db, queue


_canceled_mail_text = """Dear %(user)s,
the game %(game)s was canceled since not enough players joined.
You're credits was funded back to you.

See you soon,
Diplomatic team
"""


def game_canceled(game):
    nchan = "game_" + str(game.id)
    nobj = NObject.get_one(nchan, "game_process")
    users = NSubscription.find_subscribers(nchan, nobj)
    for user in users:
        db.NEvent.insert(
            object=nobj,
            recipient=user,
            actor="game " + game.name,
            data={"msg": "Game was canceled", "type": "game"},
            occurred_at=datetime.utcnow(),
        )
        usettings = db.UserSettings(user=user)
        if usettings.notification["email"]["processing"]:
            recipient = db.User(id=user)
            queue.mail_send(
                to=recipient.email,
                subject="Game " + game.name + " was canceled",
                message=_canceled_mail_text % dict(user=recipient.username, game=game.name),
            )


_opened_mail_text = """Dear %(user)s,
the game %(game)s has started.
Start doing some diplomacy and insert your orders!

See you soon,
Diplomatic team
"""


def game_opened(game):
    nchan = "game_" + str(game.id)
    nobj = NObject.get_one(nchan, "game_process")
    users = NSubscription.find_subscribers(nchan, nobj)
    for user in users:
        db.NEvent.insert(
            object=nobj,
            recipient=user,
            actor="game " + game.name,
            data={"msg": "Game has started", "type": "game"},
            occurred_at=datetime.utcnow(),
        )
        usettings = db.UserSettings(user=user)
        if usettings.notification["email"]["processing"]:
            recipient = db.User(id=user)
            queue.mail_send(
                to=recipient.email,
                subject="Game " + game.name + " has started",
                message=_opened_mail_text % dict(user=recipient.username, game=game.name),
            )


_new_phase_mail_text = """Dear %(user)s,
the game %(game)s was updated to a new phase.
Review what's happened and set your orders for the next turn!

See you soon,
Diplomatic team
"""


def game_new_phase(game):
    nchan = "game_" + str(game.id)
    nobj = NObject.get_one(nchan, "game_process")
    users = NSubscription.find_subscribers(nchan, nobj)
    for user in users:
        db.NEvent.insert(
            object=nobj,
            recipient=user,
            actor="game " + game.name,
            data={"msg": "Game has been processed", "type": "game"},
            occurred_at=datetime.utcnow(),
        )
        usettings = db.UserSettings(user=user)
        if usettings.notification["email"]["processing"]:
            recipient = db.User(id=user)
            queue.mail_send(
                to=recipient.email,
                subject="Game " + game.name + " has been updated",
                message=_new_phase_mail_text % dict(user=recipient.username, game=game.name),
            )


_new_msg_mail_text = """Dear %(user)s,
%(source)s sent a new message in the game %(game)s.
Ensure you review it before the next turn!

See you soon,
Diplomatic team
"""


def game_new_message(game, to, source):
    nchan = "game_" + str(game.id)
    nobj = NObject.get_one(nchan, "msg_" + to)
    users = NSubscription.find_subscribers(nchan, nobj)
    for user in users:
        if to == "all" and user == source["id"]:
            continue
        db.NEvent.insert(
            object=nobj,
            recipient=user,
            actor=source["country"],
            data={"msg": "Sent a new message", "type": "message"},
            occurred_at=datetime.utcnow(),
        )
        usettings = db.UserSettings(user=user)
        if usettings.notification["email"]["messages"]:
            recipient = db.User(id=user)
            queue.mail_send(
                to=recipient.email,
                subject="Game " + game.name + " has been updated",
                message=_new_msg_mail_text % dict(user=recipient.username, source=source["country"], game=game.name),
            )
