from emmett import now

from . import Game, celery, db, redis
from .helpers.events import publish


@celery.task(queue="games")
def manage_games():
    with db.connection():
        start_games()
        cancel_games()
        process_games()


def start_games():
    for game in (
        Game.in_stage("pregame")
        .where(lambda g: (g.is_ready == True) & (g.starts_on == Game.START_MODES["asap"]))
        .select(Game.id)
    ):
        Game.where(lambda g: g.id == game.id).update(stage=Game.STAGES["processing"])
        db.commit()
        start_game.delay(game.id)
    for game in (
        Game.in_stage("pregame")
        .where(
            lambda g: (g.is_ready == True) & (g.starts_on == Game.START_MODES["on_time"]) & (g.next_process_at <= now())
        )
        .select(Game.id)
    ):
        Game.where(lambda g: g.id == game.id).update(stage=Game.STAGES["processing"])
        db.commit()
        start_game.delay(game.id)


def cancel_games():
    for game in (
        Game.in_stage("pregame").where(lambda g: (g.is_ready == False) & (g.next_process_at <= now())).select(Game.id)
    ):
        Game.where(lambda g: g.id == game.id).update(stage=Game.STAGES["processing"])
        db.commit()
        cancel_game.delay(game.id)


def process_games():
    for game in Game.in_stage("game").where(lambda g: g.is_ready == True).select(Game.id):
        Game.where(lambda g: g.id == game.id).update(stage=Game.STAGES["processing"])
        db.commit()
        process_game.delay(game.id)
    for game in (
        Game.in_stage("game").where(lambda g: (g.is_ready == False) & (g.next_process_at <= now())).select(Game.id)
    ):
        Game.where(lambda g: g.id == game.id).update(stage=Game.STAGES["processing"])
        db.commit()
        process_game.delay(game.id)


@celery.task(queue="games")
def start_game(game_id):
    with db.connection():
        game = Game.get(game_id)
        game.start()
    publish(redis, f"game:{game_id}:state", "state", "started")


@celery.task(queue="games")
def cancel_game(game_id):
    with db.connection():
        game = Game.get(game_id)
        game.cancel()


@celery.task(queue="games")
def process_game(game_id):
    with db.connection():
        game = Game.get(game_id)
        game.process()
    publish(redis, f"game:{game_id}:state", "state", "processed")
