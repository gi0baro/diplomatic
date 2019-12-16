# -*- coding: utf-8 -*-

from collections import defaultdict

from emmett import request, response, sdict
from emmett.pipeline import RequirePipe
from emmett.tools import ServicePipe, requires
from .. import app, db, redis, auth, Map, Game, Order, GameRole, GamePhase, ChatRoom, ChatMember, ChatReading, ChatMessage
# from nudiplomacy import app, auth, db, mdb, Map, Orders, NObject, NSubscription
# from nudiplomacy.helpers.mongo import longToObjid
from ..gameman.validation import process_order
# from nudiplomacy.gameman import process_order
from ..tasks import start_game, process_game


# from emmett.pipeline import Pipe

# class FuckCors(Pipe):
#     async def open(self):
#         response.headers['Access-Control-Allow-Origin'] = '*'


api = app.module(__name__, 'api', url_prefix='api')
api.pipeline = [ServicePipe('json')]
# api.pipeline = [ServicePipe('json'), FuckCors()]


def access_error():
    return {'error': {'message': "Not authorized"}}


authorized = api.module(__name__, 'authorized')
authorized.pipeline = [RequirePipe(auth.is_logged, access_error)]


@api.route("/map/<int:mid>")
def map_get(mid):
    return Map.get(mid)


@api.route("/game/<int:gid>")
def game_get(gid):
    game = Game.get(gid)
    # game = db(db.Game.id == gid).select(
    #     db.Game.phases, db.Game.countries, db.Game.build_ew,
    #     db.Game.target_sc, db.Game.press_type).first()
    # rv = sdict()
    # if game:
    #     rv.phases = game.phases
    #     rv.countries = [el['country'] for el in game.countries]
    #     rv.buildew = game.build_ew
    #     rv.scs = game.target_sc
    #     rv.presstype = game.press_type
    #     rv.currentPlayer = game.player_country()
    rv = game.as_dict()
    players = game.players.join('user').select()
    rv['players'] = [
        {
            'id': player.id,
            'country': player.country,
            'name': player.user.username if not game.anonymous else None
        } for player in players
    ]
    return rv


@api.route("/game/<int:gid>/phases")
def game_phases(gid):
    return {'data': GamePhase.where(lambda m: m.game == gid).select(orderby=GamePhase.created_at)}


@api.route('/phases/<int:pid>')
def game_phase(pid):
    row, orders = GamePhase.get(id=pid), {}
    if not row:
        response.status = 404
        return {'error': 'not found'}
    if row.stage == GamePhase.STAGES['closed']:
        orders = row.orders_grouped()
    rv = row.as_dict()
    rv['orders'] = orders
    return rv


@api.route('/game/<int:gid>/phases/prev')
def game_phase_prev(gid):
    dbset, orders = GamePhase.where(lambda m: m.game == gid), {}
    orderby = GamePhase.id
    if request.query_params.last_id:
        dbset = dbset.where(lambda m: m.id < request.query_params.last_id)
        orderby = ~GamePhase.id
    row = dbset.select(orderby=orderby, limitby=(0, 1)).first()
    if not row:
        response.status = 404
        return {'error': 'not found'}
    if row.stage == GamePhase.STAGES['closed']:
        orders = row.orders_grouped()
    rv = row.as_dict()
    rv['orders'] = orders
    return rv


@api.route('/game/<int:gid>/phases/next')
def game_phase_next(gid):
    dbset, orders = GamePhase.where(lambda m: m.game == gid), {}
    orderby = ~GamePhase.id
    if request.query_params.last_id:
        dbset = dbset.where(lambda m: m.id > request.query_params.last_id)
        orderby = GamePhase.id
    row = dbset.select(orderby=orderby, limitby=(0, 1)).first()
    if not row:
        response.status = 404
        return {'error': 'not found'}
    if row.stage == GamePhase.STAGES['closed']:
        orders = row.orders_grouped()
    rv = row.as_dict()
    rv['orders'] = orders
    return rv


# @api.route("/game/<int:gid>/status")
# def game_status(gid):
#     game = db(db.Game.id == gid).select(db.Game.status, db.Game.phases).first()
#     return dict(status=game.status, phase=len(game.phases) - 1)


@authorized.route('/game/<int:gid>/join', methods=['post'])
async def game_join(gid):
    rv = sdict(status='error')
    game = Game.get(gid)
    if not game:
        rv.data = 'no game found'
        return rv
    params = await request.body_params
    if game.player_country(auth.user) is not None:
        rv.data = 'already in game'
        return rv
    if auth.user.vault().balance < game.bet:
        rv.data = "Not enough credits"
        return rv
    if game.players.count() == game.players_number:
        rv.data = "no slots available"
        return rv
    if game.access == Game.ACCESS_MODES['password']:
        if params.password != game.password:
            rv.data = 'wrong password'
            return rv
    chosen_country = params.country
    try:
        with db.atomic():
            role = game.add_player(auth.user, chosen_country)
    except Exception as e:
        app.log.exception(e)
        role = None
    if not role:
        rv.data = "Cannot join game"
        return rv
    if game.players.count() == game.players_number:
        game.update_record(is_ready=True, is_open=False)
        start_game.delay(game.id)
    rv.status = 'ok'
    rv.data = 'joined successfully'
    return rv


@api.route('/phases/<int:pid>/orders')
def phase_orders(pid):
    rv = []
    rows = Order.where(
        lambda o: (o.game_phase == pid) & (o.stage != Order.STAGES['planned'])
    ).join('game_role').select()
    for row in rows:
        element = row.as_dict()
        element['country'] = row.game_role.country
        rv.append(element)
    return {'data': rv}


@authorized.route('/game/<int:gid>/orders', methods=['get'])
def game_orders(gid):
    rv = sdict(status='error')
    game = Game.get(gid)
    if not game:
        rv.data = 'no game found'
        return rv
    rv.status = 'ok'
    rv.data = game.player_orders(auth.user)
    return rv


@authorized.route("/orders/<int:order_id>", methods=["put", "patch"])
async def order_save(order_id):
    rv = sdict(status="error")
    row = Order.where(
        lambda m:
            (m.id == order_id) & (GameRole.id == m.game_role) &
            (GameRole.user == auth.user.id) & (Game.id == GameRole.game)
    ).select(Order.table.ALL, GameRole.table.ALL, Game.table.ALL).first()
    if not row:
        response.status = 400
        rv.data = "bad request"
        return rv
    if row.games.stage != Game.STAGES['game'] or row.games.is_ready:
        response.status = 400
        rv.data = "Game doesn't allow orders"
        return rv
    #: if player is not active can't update orders
    if not row.game_roles.is_active:
        response.status = 400
        rv.data = "Cannot update orders in this turn"
        return rv
    #: if player is ready can't update orders
    if row.game_roles.is_ready:
        response.status = 400
        rv.data = "Cannot update orders when ready"
        return rv
    params = await request.body_params
    data = params.get('data', {})
    data['type'] = params.type
    data, errors = process_order(row.game_roles.country, row.games, row.orders.territory, data)
    order_type = data.pop('type')
    if errors:
        response.status = 422
        rv.data = errors
        return rv
    res = Order.where(lambda m: m.id == order_id).validate_and_update(type=order_type, data=data)
    if res.errors:
        response.status = 422
        rv.data = res.errors
        return rv
    rv.status = 'ok'
    rv.id = order_id
    rv.territory = row.orders.territory
    return rv


@authorized.route('/game/<int:gid>/ready', methods=['post', 'put'])
async def player_ready(gid):
    rv = sdict(status='error')
    game = Game.get(id=gid, is_ready=False, stage=Game.STAGES['game'])
    if not game:
        return rv
    status = (await request.body_params).get('ready', False)
    game.players.where(
        lambda p:
            (p.user == auth.user.id) &
            (p.is_active == True)
    ).update(is_ready=status)
    if game.players.where(lambda p: p.is_ready == True).count() == game.players_number:
        game.update_record(is_ready=True)
        process_game.delay(game.id)
    rv.data = status
    rv.status = 'ok'
    return rv


# @api.route("/join/<int:gid>", methods=['post'])
# @requires(auth.is_logged_in, access_error)
# def game_join(gid):
#     rv = sdict(status="Error")
#     gamedata = db.Game(id=gid)
#     #: do we have a game?
#     if not gamedata:
#         rv.data = "No such game found"
#         return rv
#     playerdata = db.UserData(user=auth.user.id)
#     #: does player have enough credits?
#     if playerdata.credits < gamedata.bet:
#         rv.data = "You have not enough credits"
#         return rv
#     #: is the user already in game?
#     poid = longToObjid(auth.user.id)
#     for el in gamedata.countries:
#         if el['player'] == poid:
#             rv.data = "You've already joined the game"
#             return rv
#     #: has the game any available slots?
#     slots = list(gamedata.slots)
#     if not slots:
#         rv.data = "No slots available"
#         return rv
#     #: is game password protected?
#     if gamedata.access == "password":
#         upass = request.body_params.password
#         if upass != gamedata.password:
#             rv.data = "Wrong password"
#             return rv
#     if gamedata.countries_assign == "random":
#         #: try to pick a random country
#         joined = False
#         while not joined:
#             chosen = random.choice(slots)
#             updated = mdb.games.fandm(
#                 {'id': gid, 'is_open': True, 'countries.country': {'$ne': chosen}},
#                 {'$push': {'countries': {'country': chosen, 'player': poid}}, '$pull': {'slots': chosen}},
#                 fields=['countries', 'slots'],
#                 new=True
#             )
#             if not updated:
#                 #: someone else has joined with chosen country in the meantime
#                 slots.remove(chosen)
#             else:
#                 joined = True
#                 #: update credits
#                 playerdata.update_record(credits=playerdata.credits - gamedata.bet)
#                 #: notifications
#                 nobj = NObject.get_one("game_" + str(gid), "game_process")
#                 NSubscription.subscribe(auth.user.id, "game_" + str(gid), nobj)
#                 nobj = NObject.get_one("game_" + str(gid), "msg_all")
#                 NSubscription.subscribe(auth.user.id, "game_" + str(gid), nobj)
#                 nid = db.NObject.insert(channel="game_" + str(gid), type="msg_" + chosen)
#                 NSubscription.subscribe(auth.user.id, "game_" + str(gid), nid=nid)
#                 #: set game to ready if needed
#                 if not updated.slots:
#                     toset = {'is_open': False}
#                     if gamedata.status == "pregame":
#                         toset['is_ready'] = True
#                     mdb.games.upd({"id": gid, "is_open": True}, {"$set": toset})
#             if not slots:
#                 break
#         if not joined:
#             rv.data = "No slots available"
#             return rv
#     else:
#         chosen = request.body_params.country
#         #: has the user chosen a country?
#         if chosen not in slots:
#             rv.data = "You have to pick a country"
#             return rv
#         updated = mdb.games.fandm(
#             {'id': gid, 'is_open': True, 'countries.country': {'$ne': chosen}},
#             {'$push': {'countries': {'country': chosen, 'player': poid}}},
#             fields=['countries'],
#             new=True
#         )
#         if not updated:
#             #: someone else has joined with chosen country in the meantime
#             rv.data = "Selected country not available"
#         else:
#             #: credits
#             playerdata.update_record(credits=playerdata.credits - gamedata.bet)
#             #: notifications
#             nobj = NObject.get_one("game_" + str(gid), "game_process")
#             NSubscription.subscribe(auth.user.id, "game_" + str(gid), nobj)
#             nobj = NObject.get_one("game_" + str(gid), "msg_all")
#             NSubscription.subscribe(auth.user.id, "game_" + str(gid), nobj)
#             nid = db.NObject.insert(channel="game_" + str(gid), type="msg_" + chosen)
#             NSubscription.subscribe(auth.user.id, "game_" + str(gid), nid=nid)
#             #: set game to ready if needed
#             if not updated.slots:
#                 toset = {'is_open': False}
#                 if gamedata.status == "pregame":
#                     toset['is_ready'] = True
#                 mdb.games.upd(
#                     {"id": gid, "is_open": True},
#                     {"$set": toset}
#                 )
#     rv.status = "Ok"
#     rv.data = "Joined successfully"
#     return rv


# @api.route("/orders/<int:gid>", methods=["get"])
# @requires(auth.is_logged_in, access_error)
# def orders_get(gid):
#     return Orders.owned(gid)


# @api.route("/orders/<int:gid>", methods=["post"])
# @requires(auth.is_logged_in, access_error)
# def orders_save(gid):
#     rv = sdict(status="Error")
#     if not request.body_params.orders:
#         rv.data = "Bad request"
#         return rv
#     game = db.Game(id=gid)
#     if not game:
#         rv.data = "Bad game"
#         return rv
#     if game.status != "ingame":
#         rv.data = "Game doesn't allow orders"
#         return rv
#     country = game.player_country()
#     if not country:
#         rv.data = "Not in the game"
#         return rv
#     if country not in game.phases[-1]["countries"]:
#         rv.data = "Not allowed in phase"
#         return rv
#     row = Orders.owned(game.id)
#     #: if player is ready can't update orders
#     if row.is_player_ready:
#         rv.data = "Cannot update orders when ready"
#         return rv
#     validated = process_orders(country, game, request.body_params.orders)
#     if validated.orders:
#         #: avoid to store invalid orders
#         for k, v in validated.orders.items():
#             row.data[k] = v
#         #: update in db
#         db((db.Orders.game == game.id) &
#            (db.Orders.player == auth.user.id)).update(data=row.data, are_raw=False)
#     if validated.error:
#         rv.data = validated.error
#         return rv
#     rv.status = "Ok"
#     rv.data = validated.orders
#     return rv


# @api.route("/ready/<int:gid>", methods=["get"])
# @requires(auth.is_logged_in, access_error)
# def orders_ready(gid):
#     game = db.Game(id=gid)
#     if not game:
#         return dict(status="Error", data="Bad game")
#     if game.status != "ingame":
#         return dict(status="Error", data="Game doesn't allow orders")
#     country = game.player_country()
#     if not country:
#         return dict(status="Error", data="Not in the game")
#     if country not in game.phases[-1]["countries"]:
#         return dict(status="Error", data="Not allowed in phase")
#     enabled = request.query_params.set == "1"
#     db((db.Orders.game == game.id) &
#         (db.Orders.player == auth.user.id)).update(is_player_ready=enabled)
#     if enabled:
#         readycount = db(
#             (db.Orders.game == game.id) & (db.Orders.is_player_ready == True)).count()
#         if readycount == len(game.phases[-1]["countries"]):
#             mdb.games.fandm(
#                 {"id": game.id, "is_ready": False},
#                 {"$set": {"is_ready": True}}
#             )
#     return dict(status="Ok", data=enabled)


# @api.route('/game/<int:gid>/rooms', methods=['get'])
@authorized.route('/game/<int:gid>/rooms', methods=['get'])
def chat_rooms(gid):
    # user = 1
    # auth.user
    player = ChatMember.where(
        lambda m: (m.player == GameRole.id) & (GameRole.user == auth.user)
    ).select(GameRole.table.ALL).first()
    if not player:
        return {'data': []}
    rows = ChatRoom.where(lambda m: m.game == gid).accessible_by_user(auth.user).select(ChatRoom.table.ALL)
    rooms_id = rows.column('id')
    all_members = ChatMember.where(lambda m: m.room.belongs(rooms_id) & (m.player != player.id)).select()
    members = defaultdict(list)
    for member in all_members:
        members[member.room].append(member)
    for row in rows:
        row.members = members[row.id]
    return {'data': rows}


@authorized.route('/game/<int:gid>/readings', methods=['get'])
async def chat_readings(gid):
    rows = ChatReading.accessible_by_user(auth.user).of_game(gid).select(ChatReading.table.ALL)
    return {'data': rows}


@authorized.route('/room/<int:rid>/messages', methods=['get'])
def chat_messages(rid):
    room = ChatRoom.accessible_by_user(auth.user).where(lambda m: m.id == rid).select(ChatRoom.table.ALL).first()
    if not room:
        return {'data': []}
    page = request.query_params.page or 1
    rows = room.messages(orderby=~ChatMessage.created_at, paginate=(page, 25))
    return {'data': rows}


@authorized.route('/game/<int:gid>/messages', methods=['post'])
async def new_chat_message(gid):
    response.status = 201
    member = ChatMember.where(
        lambda m: (m.player == GameRole.id) & (GameRole.user == auth.user) & (GameRole.game == gid)
    ).select(ChatMember.table.ALL).first()
    if not member:
        response.status = 403
        return {'error': 'no member'}
    params = await request.body_params
    room = ChatRoom.accessible_by_user(auth.user).where(lambda m: m.id == params.room).select(ChatRoom.table.ALL).first()
    res = ChatMessage.create(room=room, sender=member, text=params.text)
    if res.errors:
        response.status = 422
        return {'error': res.errors.as_dict()}
    row = ChatMessage.get(res.id)
    row.publish_on_relevant_channels(redis)
    return row


@authorized.route('/game/<int:gid>/readings/<int:rid>', methods=['put'])
async def chat_read_message(gid, rid):
    member = ChatMember.where(
        lambda m: (m.player == GameRole.id) & (GameRole.user == auth.user) & (GameRole.game == gid)
    ).select(ChatMember.table.ALL).first()
    if not member:
        response.status = 403
        return {'error': 'no member'}
    params = await request.body_params
    res = ChatReading.where(
        lambda m: (m.id == rid) & (m.member == member.id)
    ).validate_and_update(message=params.message)
    if res.errors:
        response.status = 422
        return {'error': res.errors.as_dict()}
    row = ChatReading.get(id=rid)
    return row


@authorized.route("/chat/<int:cid>", methods="get")
def chat_get(cid):
    return sdict(status="Ok", data=[])
    # chat = db.Chat(id=cid)
    # if chat:
    #     try:
    #         since = int(request.params.since)
    #     except:
    #         since = 0
    #     if chat.users == ["all"]:
    #         rv.data = chat.messages[since:]
    #     else:
    #         ingame = longToObjid(auth.user.id) in chat.users
    #         if ingame:
    #             rv.data = chat.messages[since:]
    # return rv


# @api.route("/chat/<int:cid>", methods=["post"])
# @requires(auth.is_logged_in, access_error)
# def chat_post(cid):
#     rv = sdict(status="Error")
#     message = request.body_params.msg
#     if message:
#         chat = db(
#             (db.Chat.id == cid) & (db.Chat.is_open == True)).select().first()
#         if chat:
#             pcountry = chat.game.player_country()
#             mdata = {'text': message, 'timeref': request.now, 'from': pcountry}
#             if chat.users == ["all"]:
#                 players = [el['player'] for el in chat.game.countries]
#                 can = longToObjid(auth.user.id) in players
#                 mdata['read'] = [pcountry]
#             else:
#                 can = longToObjid(auth.user.id) in chat.users
#                 mdata['read'] = False
#             if can:
#                 mdb.chats.upd(
#                     {'id': cid},
#                     {'$push': {'messages': mdata}}
#                 )
#                 from nudiplomacy.helpers.notifications import game_new_message
#                 if chat.users == ["all"]:
#                     game_new_message(chat.game, "all", {'id': auth.user.id,
#                                      'country': pcountry})
#                 else:
#                     chat.users.remove(longToObjid(auth.user.id))
#                     #touser = longToObjid(chat.users[0])
#                     #for el in chat.game.countries:
#                     #    if el['player'] == touser:
#                     #        tocountry = el['country']
#                     #        break
#                     game_new_message(
#                         chat.game,
#                         chat.game.player_country(uoid=chat.users[0]),
#                         {'id': auth.user.id, 'country': pcountry})
#                 rv.status = "Ok"
#                 rv.data = mdata
#             else:
#                 rv.data = "Not authorized"
#         else:
#             rv.data = "Invalid chat"
#     else:
#         rv.data = "Empty message"
#     return rv


# @api.route("/chat/read/<int:cid>/<int:mid>", methods=["get"])
# @requires(auth.is_logged_in, access_error)
# def chat_read(cid, mid):
#     uoid = longToObjid(auth.user.id)
#     if request.query_params.all:
#         chat = db(db.Chat.id == cid).select().first()
#         pcountry = chat.game.player_country()
#         if pcountry:
#             read = mdb.chats.upd(
#                 {'id': cid, 'users': 'all',
#                  'messages.'+str(mid): {'$exists': True}},
#                 {'$push': {'messages.'+str(mid)+'.read': pcountry}}
#             )
#     else:
#         read = mdb.chats.upd(
#             {'id': cid, 'users': uoid,
#              'messages.'+str(mid): {'$exists': True}},
#             {'$set': {'messages.'+str(mid)+'.read': True}}
#         )
#     return dict(status="Ok", data=read)
