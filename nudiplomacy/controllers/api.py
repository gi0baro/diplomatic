# -*- coding: utf-8 -*-

import random
from weppy import request, sdict
from weppy.pipeline import RequirePipe
from weppy.tools import ServicePipe, requires
from .. import app, db, auth, Map, Game
# from nudiplomacy import app, auth, db, mdb, Map, Orders, NObject, NSubscription
# from nudiplomacy.helpers.mongo import longToObjid
# from nudiplomacy.gameman import process_orders

api = app.module(__name__, 'api', url_prefix='api')
api.pipeline = [ServicePipe('json')]


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
    return game


# @api.route("/game/<int:gid>/status")
# def game_status(gid):
#     game = db(db.Game.id == gid).select(db.Game.status, db.Game.phases).first()
#     return dict(status=game.status, phase=len(game.phases) - 1)


@authorized.route('/game/<int:gid>/join', methods=['post'])
def game_join(gid):
    rv = sdict(status='error')
    game = Game.get(gid)
    if not game:
        rv.data = 'no game found'
        return rv
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
        if request.body_params.password != game.password:
            rv.data = 'wrong password'
            return rv
    chosen_country = request.body_params.country
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
    rv.status = 'ok'
    rv.data = 'joined successfully'
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


# @api.route("/chat/<int:cid>", methods=["get"])
# @requires(auth.is_logged_in, access_error)
# def chat_get(cid):
#     rv = sdict(status="Ok", data=[])
#     chat = db.Chat(id=cid)
#     if chat:
#         try:
#             since = int(request.params.since)
#         except:
#             since = 0
#         if chat.users == ["all"]:
#             rv.data = chat.messages[since:]
#         else:
#             ingame = longToObjid(auth.user.id) in chat.users
#             if ingame:
#                 rv.data = chat.messages[since:]
#     return rv


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
