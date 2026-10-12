from collections import defaultdict
from datetime import date, datetime, timedelta

from emmett import now

from . import Game, GameRole, StatsCountries, StatsEvent, StatsGames, StatsTime, app, celery, db, redis
from .helpers.events import publish


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
        try:
            with db.atomic():
                game.start()
        except Exception:
            app.log.exception(f"start_game: game {game_id} crashed")
            game.update_record(stage=Game.Stage.CRASH)
            db.commit()
            publish(redis, f"game:{game_id}:state", "state", "crashed")
            return
    publish(redis, f"game:{game_id}:state", "state", "started")


@celery.task(queue="games")
def cancel_game(game_id):
    with db.connection():
        game = Game.get(game_id)
        if not game or game.stage != Game.Stage.PROCESSING:
            app.log.warning(f"cancel_game: game {game_id} not claimed, skipping")
            return
        try:
            with db.atomic():
                game.cancel()
        except Exception:
            app.log.exception(f"cancel_game: game {game_id} crashed")
            game.update_record(stage=Game.Stage.CRASH)
            db.commit()
            publish(redis, f"game:{game_id}:state", "state", "crashed")
            return
    publish(redis, f"game:{game_id}:state", "state", "over")


@celery.task(queue="games")
def process_game(game_id):
    with db.connection():
        game = Game.get(game_id)
        if not game or game.stage != Game.Stage.PROCESSING:
            app.log.warning(f"process_game: game {game_id} not claimed, skipping")
            return
        try:
            with db.atomic():
                game.process()
        except Exception:
            app.log.exception(f"process_game: game {game_id} crashed")
            game.update_record(stage=Game.Stage.CRASH)
            db.commit()
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
