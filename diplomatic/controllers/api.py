from collections import defaultdict

from emmett import request, response, sdict
from emmett.pipeline import RequirePipe
from emmett.tools import ServicePipe

from .. import (
    ChatMember,
    ChatMessage,
    ChatReading,
    ChatRoom,
    Game,
    GamePhase,
    GameRole,
    Map,
    Order,
    app,
    auth,
    db,
    redis,
    sessions,
)
from ..diplomacy import process_order
from ..helpers.events import publish
from . import query_page


api = app.module(__name__, "api", url_prefix="api")
api.pipeline = [sessions, db.pipe, auth.pipe, ServicePipe("json")]


def access_error():
    return {"error": {"message": "Not authorized"}}


authorized = api.module(__name__, "authorized")
authorized.pipeline = [RequirePipe(auth.is_logged, access_error)]

_map_fields = [field for field in Map.table if field.name != "svg"]


@api.route("/map/<int:mid>", methods="get")
def map_get(mid):
    return Map.where(lambda m: m.id == mid).select(*_map_fields).first()


@api.route("/game/<str:gid>", methods="get")
def game_get(gid):
    game = Game.get(gid)
    if not game:
        response.status = 404
        return {"error": "not found"}
    players = game.players.current().join("user").select()
    return {
        "id": game.id,
        "created_at": game.created_at,
        "updated_at": game.updated_at,
        "name": game.name,
        "lang": game.lang,
        "players_number": game.players_number,
        "bet": game.bet,
        "pot_type": game.pot_type,
        "phase_time": game.phase_time,
        "join_time": game.join_time,
        "starts_on": game.starts_on,
        "build_everywhere": game.build_everywhere,
        "build_on_start": game.build_on_start,
        "anonymous": game.anonymous,
        "press_type": game.press_type,
        "access": game.access,
        "max_turns": game.max_turns,
        "target_sc": game.target_sc,
        "skip_processing": game.skip_processing,
        "stage": game.stage,
        "is_open": game.is_open,
        "is_ready": game.is_ready,
        "countries_assignment": game.countries_assignment,
        "processed_at": game.processed_at,
        "next_process_at": game.next_process_at,
        "countries": game.countries,
        "user": game.user,
        "map": game.map,
        "players": [
            {
                "id": player.id,
                "country": player.country,
                "name": player.user.username if not game.anonymous else None,
                "is_ready": player.is_ready,
                "is_active": player.is_active,
                "state": player.state,
            }
            for player in players
        ],
    }


@api.route("/game/<str:gid>/phases", methods="get")
def game_phases(gid):
    return {"data": GamePhase.where(lambda m: m.game == gid).select(orderby=GamePhase.created_at)}


@api.route("/phases/<str:pid>", methods="get")
def game_phase(pid):
    row, orders = GamePhase.get(id=pid), {}
    if not row:
        response.status = 404
        return {"error": "not found"}
    if row.stage == GamePhase.Stage.CLOSED:
        orders = row.orders_grouped()
    rv = row.as_dict()
    rv["orders"] = orders
    return rv


@api.route("/game/<str:gid>/phases/prev", methods="get")
def game_phase_prev(gid):
    dbset, orders = GamePhase.where(lambda m: m.game == gid), {}
    orderby = GamePhase.id
    if request.query_params.last_id:
        dbset = dbset.where(lambda m: m.id < request.query_params.last_id)
        orderby = ~GamePhase.id
    row = dbset.select(orderby=orderby, limitby=(0, 1)).first()
    if not row:
        response.status = 404
        return {"error": "not found"}
    if row.stage == GamePhase.Stage.CLOSED:
        orders = row.orders_grouped()
    rv = row.as_dict()
    rv["orders"] = orders
    return rv


@api.route("/game/<str:gid>/phases/next", methods="get")
def game_phase_next(gid):
    dbset, orders = GamePhase.where(lambda m: m.game == gid), {}
    orderby = ~GamePhase.id
    if request.query_params.last_id:
        dbset = dbset.where(lambda m: m.id > request.query_params.last_id)
        orderby = GamePhase.id
    row = dbset.select(orderby=orderby, limitby=(0, 1)).first()
    if not row:
        response.status = 404
        return {"error": "not found"}
    if row.stage == GamePhase.Stage.CLOSED:
        orders = row.orders_grouped()
    rv = row.as_dict()
    rv["orders"] = orders
    return rv


@api.route("/game/<str:gid>/history", methods="get")
def game_history(gid):
    row = Game.where(lambda m: (m.id == gid) & (m.stage == Game.Stage.OVER)).select(Game.history).first()
    if not row:
        response.status = 404
        return {"error": "not found"}
    return {"phases": row.history}


@api.route("/phases/<str:pid>/orders", methods="get")
def phase_orders(pid):
    rv = []
    rows = Order.where(lambda o: (o.game_phase == pid) & (o.stage != Order.Stage.PLANNED)).join("game_role").select()
    for row in rows:
        element = row.as_dict()
        element["country"] = row.game_role.country
        rv.append(element)
    return {"data": rv}


@authorized.route("/game/<str:gid>/orders", methods="get")
def game_orders(gid):
    rv = sdict(status="error")
    game = Game.get(gid)
    if not game:
        rv.data = "no game found"
        return rv
    rv.status = "ok"
    rv.data = game.player_orders(auth.user)
    return rv


@authorized.route("/orders/<str:order_id>", methods=["put", "patch"])
async def order_save(order_id):
    rv = sdict(status="error")
    row = (
        Order.where(
            lambda m: (
                (m.id == order_id)
                & (GameRole.id == m.game_role)
                & (GameRole.user == auth.user.id)
                & (Game.id == GameRole.game)
                & (GamePhase.id == m.game_phase)
                & (GamePhase.stage == GamePhase.Stage.OPEN)
            )
        )
        .select(Order.table.ALL, GameRole.table.ALL, Game.table.ALL, GamePhase.id)
        .first()
    )
    if not row:
        response.status = 400
        rv.data = "bad request"
        return rv
    if row.games.stage != Game.Stage.GAME or row.games.is_ready:
        response.status = 400
        rv.data = "Game doesn't allow orders"
        return rv
    if not row.game_roles.is_active or row.game_roles.state not in (GameRole.State.PLAYING, GameRole.State.DISORDER):
        response.status = 400
        rv.data = "Cannot update orders in this turn"
        return rv
    #: if player is ready can't update orders
    if row.game_roles.is_ready:
        response.status = 400
        rv.data = "Cannot update orders when ready"
        return rv
    params = await request.body_params
    data = params.get("data", {})
    data["type"] = params.type
    data, errors = process_order(row.game_roles.country, row.games, row.orders.territory, data)
    order_type = data.pop("type")
    if errors:
        response.status = 422
        rv.data = errors
        return rv
    #: the writes are conditional on the phase still taking orders: a claim or a processing in the
    #: meantime makes them no-ops
    phase_id = row.game_phases.id
    res = (
        Order.in_live_phase(phase_id).where(lambda m: m.id == order_id).validate_and_update(type=order_type, data=data)
    )
    if res.errors:
        response.status = 422
        rv.data = res.errors
        return rv
    if not res.updated:
        response.status = 400
        rv.data = "Game doesn't allow orders"
        return rv
    flipped = (
        GameRole.in_live_phase(phase_id)
        .where(lambda m: (m.id == row.game_roles.id) & (m.state == GameRole.State.DISORDER))
        .update(state=GameRole.State.PLAYING)
    )
    if flipped:
        row.games.update_record(is_open=row.games.open_from_roles())
        db.commit()
        await publish(
            app.ext.Redis.client,
            f"game:{row.games.id}:players",
            "players",
            {"country": row.game_roles.country, "is_ready": False, "state": GameRole.State.PLAYING},
        )
    rv.status = "ok"
    rv.id = order_id
    rv.territory = row.orders.territory
    return rv


@authorized.route("/game/<str:gid>/ready", methods=["post", "put"])
async def player_ready(gid):
    rv = sdict(status="error")
    game = Game.get(id=gid, is_ready=False, stage=Game.Stage.GAME)
    if not game:
        return rv
    status = (await request.body_params).get("ready", False)
    if not isinstance(status, bool):
        response.status = 422
        rv.data = "invalid ready status"
        return rv
    phase = game.active_phase()
    if not phase:
        return rv
    roles = game.players.actionable().in_live_phase(phase.id).where(lambda m: m.user == auth.user.id)
    role = roles.select(GameRole.country, GameRole.state).first()
    updated = restored = False
    if role:
        updated = bool(roles.update(is_ready=status))
        restored = (
            updated
            and status
            and roles.where(lambda m: (m.state == GameRole.State.DISORDER) & (m.is_ready == True)).update(
                state=GameRole.State.PLAYING
            )
        )
        if restored:
            game.update_record(is_open=game.open_from_roles())
    db.commit()
    # claimed = game.all_ready() and game.claim(Game.Stage.GAME)
    # if claimed:
    #     game.update_record(is_ready=True)
    if game.players_all_ready():
        game.set_ready()
    db.commit()
    if updated:
        state = GameRole.State.PLAYING if restored else role.state
        await publish(
            app.ext.Redis.client,
            f"game:{gid}:players",
            "players",
            {"country": role.country, "is_ready": status, "state": state},
        )
    # if claimed:
    #     process_game.delay(game.id)
    rv.data = status
    rv.status = "ok"
    return rv


@authorized.route("/game/<str:gid>/rooms", methods="get")
def chat_rooms(gid):
    player = GameRole.where(lambda m: (m.user == auth.user) & (m.game == gid)).select().first()
    if not player:
        return {"data": []}
    rows = ChatRoom.where(lambda m: m.game == gid).accessible_by_user(auth.user).select(ChatRoom.table.ALL)
    rooms_id = rows.column("id")
    all_members = ChatMember.where(lambda m: m.room.belongs(rooms_id)).select()
    members = defaultdict(list)
    for member in all_members:
        members[member.room].append(member)
    # for row in rows:
    #    row.members = members[row.id]
    # return {"data": rows}
    return {"data": [{**row.as_dict(), "members": members[row.id]} for row in rows]}


@authorized.route("/game/<str:gid>/readings", methods="get")
async def chat_readings(gid):
    rows = ChatReading.accessible_by_user(auth.user).of_game(gid).select(ChatReading.table.ALL)
    return {"data": rows}


@authorized.route("/room/<str:rid>/messages", methods="get")
def chat_messages(rid):
    room = ChatRoom.accessible_by_user(auth.user).where(lambda m: m.id == rid).select(ChatRoom.table.ALL).first()
    if not room:
        return {"data": []}
    page = query_page()
    rows = room.messages(orderby=~ChatMessage.created_at | ~ChatMessage.id, paginate=(page, 25))
    return {"data": rows}


@api.route("/game/<str:gid>/chat", methods="get")
def chat_public_messages(gid):
    game = Game.where(lambda m: m.id == gid).select(Game.stage, Game.press_type, Game.chat_history).first()
    if not game:
        response.status = 404
        return {"error": "not found"}
    if game.press_type == Game.Press.NONE:
        return {"data": []}
    page = query_page()
    if game.stage == Game.Stage.OVER:
        return {"data": (game.chat_history or [])[(page - 1) * 25 : page * 25]}
    return {"data": ChatMessage.public_for_game(gid, page)}


@authorized.route("/game/<str:gid>/messages", methods="post")
async def new_chat_message(gid):
    response.status = 201
    params = await request.body_params
    member = (
        ChatMember.where(
            lambda m: (
                (m.room == params.room)
                & (m.player == GameRole.id)
                & (GameRole.user == auth.user)
                & (GameRole.game == gid)
            )
        )
        .select(ChatMember.table.ALL)
        .first()
    )
    if not member:
        response.status = 403
        return {"error": "no member"}
    params = await request.body_params
    room = (
        ChatRoom.accessible_by_user(auth.user).where(lambda m: m.id == params.room).select(ChatRoom.table.ALL).first()
    )
    res = ChatMessage.create(room=room.id, sender=member.id, text=params.text)
    if res.errors:
        response.status = 422
        return {"error": res.errors.as_dict()}
    row = ChatMessage.get(res.id)
    row.publish_on_relevant_channels(redis)
    return row


@authorized.route("/game/<str:gid>/readings/<str:rid>", methods="put")
async def chat_read_message(gid, rid):
    row = ChatReading.get(rid)
    if not row:
        response.status = 404
        return {"error": "not found"}
    member = (
        ChatMember.where(
            lambda m: (
                (m.room == row.room) & (m.player == GameRole.id) & (GameRole.user == auth.user) & (GameRole.game == gid)
            )
        )
        .select(ChatMember.table.ALL)
        .first()
    )
    if not member:
        response.status = 403
        return {"error": "no member"}
    params = await request.body_params
    if not ChatMessage.where(lambda m: (m.id == params.message) & (m.room == row.room)).count():
        response.status = 422
        return {"error": {"message": "invalid"}}
    res = ChatReading.where(lambda m: (m.id == rid) & (m.member == member.id)).validate_and_update(
        message=params.message
    )
    if res.errors:
        response.status = 422
        return {"error": res.errors.as_dict()}
    row = ChatReading.get(id=rid)
    return row
