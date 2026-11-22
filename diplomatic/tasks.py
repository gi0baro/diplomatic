from collections import defaultdict
from datetime import date, datetime, timedelta

from emmett import now

from . import (
    ChatMessage,
    Game,
    GameRole,
    Notification,
    StatsCountries,
    StatsEvent,
    StatsGames,
    StatsTime,
    app,
    celery,
    db,
    mailer,
    notifications,
    redis,
)
from .helpers.events import publish


MAIL_TASK = "diplomatic.mail.send"
MAIL_QUEUE = "mail"
NOTIFICATION_RETENTION = timedelta(days=30)


@celery.task(queue="games")
def manage_games():
    with db.connection():
        start_games()
        cancel_games()
        process_games()


def start_games():
    for game in (
        Game.in_stage(Game.Stage.PREGAME)
        .where(lambda g: (g.is_ready == True) & (g.starts_on == Game.Start.ASAP))
        .select()
    ):
        if game.claim(Game.Stage.PREGAME):
            db.commit()
            start_game.delay(game.id)
    for game in (
        Game.in_stage(Game.Stage.PREGAME)
        .where(lambda g: (g.is_ready == True) & (g.starts_on == Game.Start.ON_TIME) & (g.next_process_at <= now()))
        .select()
    ):
        if game.claim(Game.Stage.PREGAME):
            db.commit()
            start_game.delay(game.id)


def cancel_games():
    for game in (
        Game.in_stage(Game.Stage.PREGAME).where(lambda g: (g.is_ready == False) & (g.next_process_at <= now())).select()
    ):
        if game.claim(Game.Stage.PREGAME):
            db.commit()
            cancel_game.delay(game.id)


def process_games():
    for game in Game.in_stage(Game.Stage.GAME).where(lambda g: g.is_ready == True).select():
        if game.claim(Game.Stage.GAME):
            db.commit()
            process_game.delay(game.id)
    for game in (
        Game.in_stage(Game.Stage.GAME).where(lambda g: (g.is_ready == False) & (g.next_process_at <= now())).select()
    ):
        if game.claim(Game.Stage.GAME):
            db.commit()
            process_game.delay(game.id)


@celery.task(queue="games")
def start_game(game_id):
    with db.connection():
        game = Game.get(game_id)
        if not game or game.stage != Game.Stage.PROCESSING:
            app.log.warning(f"start_game: game {game_id} not claimed, skipping")
            return
        game.start()
    publish(redis, f"game:{game_id}:state", "state", "started")


@celery.task(queue="games")
def cancel_game(game_id):
    with db.connection():
        game = Game.get(game_id)
        if not game or game.stage != Game.Stage.PROCESSING:
            app.log.warning(f"cancel_game: game {game_id} not claimed, skipping")
            return
        game.cancel()
    publish(redis, f"game:{game_id}:state", "state", "over")


@celery.task(queue="games")
def process_game(game_id):
    with db.connection():
        game = Game.get(game_id)
        if not game or game.stage != Game.Stage.PROCESSING:
            app.log.warning(f"process_game: game {game_id} not claimed, skipping")
            return
        crashed = not game.process()
    if crashed:
        publish(redis, f"game:{game_id}:state", "state", "crashed")
        return
    publish(redis, f"game:{game_id}:state", "state", "over" if game.stage == Game.Stage.OVER else "processed")


@celery.task(queue="stats")
def fold_stats(day=None):
    day = date.fromisoformat(day) if day else now().date() - timedelta(days=1)
    start = datetime(day.year, day.month, day.day)
    end = start + timedelta(days=1)
    outcomes = {
        GameRole.State.WON: "won",
        GameRole.State.SURVIVED: "survived",
        GameRole.State.DEFEATED: "defeated",
        GameRole.State.DRAWN: "drawn",
    }
    with db.connection():
        events = defaultdict(list)
        for event in StatsEvent.where(lambda m: (m.created_at >= start) & (m.created_at < end)).select(
            orderby=StatsEvent.created_at
        ):
            events[event.variant].append(event)
        with db.atomic():
            for variant, rows in events.items():
                countries = StatsCountries.get(variant=variant)
                games = StatsGames.get(variant=variant)
                started = 0
                for event in rows:
                    if event.kind == StatsEvent.Kind.GAME_STARTED:
                        started += 1
                        for field, key in (("lang", "lang"), ("players", "players_number"), ("pot", "pot_type")):
                            value = str(event.data[key])
                            games[field][value] = games[field].get(value, 0) + 1
                        for country in event.data["countries"]:
                            countries.played[country] = countries.played.get(country, 0) + 1
                    elif event.kind == StatsEvent.Kind.GAME_ENDED:
                        turns = str(event.data["turns"])
                        games.turns[turns] = games.turns.get(turns, 0) + 1
                        for country, state in event.data["outcomes"].items():
                            if state in outcomes:
                                counter = countries[outcomes[state]]
                                counter[country] = counter.get(country, 0) + 1
                countries.update_record(
                    played=countries.played,
                    won=countries.won,
                    survived=countries.survived,
                    defeated=countries.defeated,
                    drawn=countries.drawn,
                )
                games.update_record(lang=games.lang, players=games.players, pot=games.pot, turns=games.turns)
                if started:
                    stats_time = StatsTime.get(variant=variant, date=day)
                    if stats_time:
                        stats_time.update_record(games=started)
                    else:
                        StatsTime.create(variant=variant, date=day, games=started)


@celery.task(queue="notifications")
def deliver_notifications():
    #: at most once: the row leaves PENDING and commits before the email is handed off
    with db.connection():
        due = Notification.due(now() - timedelta(minutes=app.config.notifications.email_debounce))
        for row, delivery in due:
            if not Notification.decide(row, delivery):
                continue
            db.commit()
            if delivery == Notification.Delivery.SENT:
                subject, body = notifications.email(row, app.config.site_url)
                celery.send_task(MAIL_TASK, args=(row.user.email, subject, body), queue=MAIL_QUEUE)


@celery.task(name=MAIL_TASK, queue=MAIL_QUEUE)
def send_mail(address, subject, body):
    #: with no mailer configured the email is dropped; no retry, emails are at most once
    if not mailer:
        return
    mailer.send_mail(recipients=address, subject=subject, body=body)


@celery.task(queue="notifications")
def notify_chat_message(message_id):
    with db.connection():
        message = ChatMessage.get(message_id)
        if not message:
            return
        Game.get(message.room.game).notify_messages(message, redis)


@celery.task(queue="notifications")
def purge_notifications():
    with db.connection():
        with db.atomic():
            Notification.purge(now() - NOTIFICATION_RETENTION)
