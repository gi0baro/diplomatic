from emmett import now

from . import Game, app, celery, db, redis
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
