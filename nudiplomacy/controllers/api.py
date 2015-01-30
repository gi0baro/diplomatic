import random
from weppy import AppModule, request, sdict
from weppy.tools import ServiceHandler, requires
from nudiplomacy import app, auth, db, mdb, Orders
from nudiplomacy.helpers.mongo import longToObjid, objidToLong
from nudiplomacy.gameman import process_orders

api = AppModule(app, "api", __name__, url_prefix="api")
api.common_handlers = [ServiceHandler('json')]


def access_error():
    return dict(status="Error", data="Not authorized")


@api.expose("/map/<int:mid>")
def map_get(mid):
    mapdata = db(db.Map.id == mid).select().first().as_dict()
    if not mapdata:
        return dict()
    # temp workaround for str->int conversion
    ch = ["neutrals", "seas", "coasts"]
    for c in ch:
        for i in range(0, len(mapdata[c])):
            mapdata[c][i] = str(mapdata[c][i])
    #
    return mapdata


@api.expose("/game/<int:gid>")
def game_get(gid):
    game = db(db.Game.id == gid).select(
        db.Game.phases, db.Game.countries, db.Game.buildew,
        db.Game.targetsc, db.Game.presstype).first()
    rv = sdict()
    if game:
        rv.currentPlayer = None
        rv.phases = game.phases
        rv.countries = game.countries.keys()
        rv.buildew = game.buildew
        rv.scs = game.targetsc
        rv.presstype = game.presstype
        if auth.user:
            for k, v in game.countries.items():
                if objidToLong(v) == auth.user.id:
                    rv.currentPlayer = k
                    break
    return rv


@api.expose("/join/<int:gid>")
@requires(auth.is_logged_in, access_error)
def game_join(gid):
    rv = sdict(status="Error")
    gamedata = db.Game(id=gid)
    #: do we have a game?
    if not gamedata:
        rv.data = "No such game found"
        return rv
    playerdata = db.UserData(user=auth.user.id)
    #: does player have enough credits?
    if playerdata.credits < gamedata.bet:
        rv.data = "You have not enough credits"
        return rv
    #: evaluate available countries
    countrydict = {}
    app.log.debug(gamedata.countries)
    for k, v in gamedata.countries.items():
        if v is None:
            countrydict[k] = v
        #: is the user already in game?
        elif v == longToObjid(auth.user.id):
            rv.data = "You've already joined the game"
            return rv
    app.log.debug(countrydict)
    #: does the game have available slots?
    if not countrydict.keys():
        rv.data = "No slots available"
        return rv
    if gamedata.countriesassign == "random":
        #: try to pick a random country
        joined = False
        while not joined:
            chosen = random.choice(countrydict.keys())
            updated = mdb.games.fandm(
                {"id": gid, "countries."+chosen: None},
                {"$set": {"countries."+chosen: longToObjid(auth.user.id)}},
                fields=["countries"],
                new=True
            )
            if not updated:
                #: someone else has joined with chosen country in the meantime
                del countrydict[chosen]
            else:
                joined = True
                #db(db.UserData.user == auth.user.id).update(
                #    credits=db.UserData.credits-gamedata.bet)
                playerdata.update_record(credits=playerdata.credits-gamedata.bet)
                if all([v is not None for v in updated.countries.itervalues()]):
                    mdb.games.upd(
                        {"id": gid, "ready": False},
                        {"$set": {"ready": True}}
                    )
            if not countrydict:
                break
        if not joined:
            rv.data = "No slots available"
            return rv
    else:
        chosen = request.get_vars.country
        #: has the user chosen a country?
        if not chosen:
            rv.data = "You have to pick a country"
            return rv
        updated = mdb.games.fandm(
            {"id": gid, "countries."+chosen: None},
            {"$set": {"countries."+chosen: longToObjid(auth.user.id)}},
            fields=["countries"],
            new=True
        )
        if not updated:
            #: someone else has joined with chosen country in the meantime
            rv.data = "Selected country not available"
        else:
            #db(db.UserData.user == auth.user.id).update(
            #    credits=db.UserData.credits-gamedata.bet)
            playerdata.update_record(credits=playerdata.credits-gamedata.bet)
            if all([v is not None for v in updated.countries.itervalues()]):
                mdb.games.upd(
                    {"id": gid, "ready": False},
                    {"$set": {"ready": True}}
                )
    rv.status = "Ok"
    rv.data = "Joined successfully"
    return rv


@api.expose("/orders/<int:gid>", methods=["get"])
@requires(auth.is_logged_in, access_error)
def orders_get(gid):
    return Orders.owned(gid)


@api.expose("/orders/<int:gid>", methods=["post"])
@requires(auth.is_logged_in, access_error)
def orders_save(gid):
    rv = sdict(status="Error")
    #app.log.debug(request.post_vars)
    if not request.post_vars.orders:
        rv.data = "Bad request"
        return rv
    game = db.Game(id=gid)
    if not game:
        rv.data = "Bad game"
        return rv
    if game.status != "ingame":
        rv.data = "Game doesn't allow orders"
        return rv
    country = game.playercountry()
    if not country:
        rv.data = "Not in the game"
        return rv
    if country not in game.phases[-1]["countries"]:
        rv.data = "Not allowed in phase"
        return rv
    row = Orders.owned(game.id)
    #: if player is ready can't update orders
    if row.ready:
        rv.data = "Cannot update orders when ready"
        return rv
    validated = process_orders(country, game, request.post_vars.orders)
    if validated.orders:
        #: avoid to store invalid orders
        for k, v in validated.orders.items():
            row.data[k] = v
        #: update in db
        db((db.Orders.game == game.id) &
           (db.Orders.player == auth.user.id)).update(data=row.data)
    if validated.error:
        rv.data = validated.error
        return rv
    rv.status = "Ok"
    rv.data = validated.orders
    return rv


@api.expose("/ready/<int:gid>", methods=["get"])
@requires(auth.is_logged_in, access_error)
def orders_ready(gid):
    game = db.Game(id=gid)
    if not game:
        return dict(status="Error", data="Bad game")
    if game.status != "ingame":
        return dict(status="Error", data="Game doesn't allow orders")
    country = game.playercountry()
    if not country:
        return dict(status="Error", data="Not in the game")
    if country not in game.phases[-1]["countries"]:
        return dict(status="Error", data="Not allowed in phase")
    enabled = request.get_vars.set == "1"
    db((db.Orders.game == game.id) &
        (db.Orders.player == auth.user.id)).update(ready=enabled)
    if enabled:
        readycount = db(
            (db.Orders.game == game.id) & (db.Orders.ready == True)).count()
        if readycount == len(game.phases[-1]["countries"]):
            mdb.games.fandm(
                {"id": game.id, "ready": False},
                {"$set": {"ready": True}}
            )
    return dict(status="Ok", data=enabled)


@api.expose("/chat/<int:cid>", methods=["get"])
@requires(auth.is_logged_in, access_error)
def chat_get(cid):
    rv = sdict(status="Ok", data=[])
    chat = db.Chat(id=cid)
    if chat:
        since = request.vars.since or 0
        if chat.users == ["all"]:
            rv.data = chat.messages[since:]
        else:
            ingame = longToObjid(auth.user.id) in chat.users
            if ingame:
                rv.data = chat.messages[since:]
    return rv


@api.expose("/chat/<int:cid>", methods=["post"])
@requires(auth.is_logged_in, access_error)
def chat_post(cid):
    rv = sdict(status="Error")
    message = request.post_vars.msg
    if message:
        chat = db.Chat(id=cid)
        if chat:
            pcountry = chat.game.playercountry()
            mdata = {'text': message, 'timeref': request.now, 'from': pcountry}
            if chat.users == ["all"]:
                can = longToObjid(auth.user.id) in chat.game.countries.values()
                mdata['read'] = [pcountry]
            else:
                can = longToObjid(auth.user.id) in chat.users
                mdata['read'] = False
            if can:
                mdb.chats.upd(
                    {'id': cid},
                    {'$push': {'messages': mdata}}
                )
                rv.status = "Ok"
                rv.data = mdata
            else:
                rv.data = "Not authorized"
        else:
            rv.data = "Invalid chat"
    else:
        rv.data = "Empty message"
    return rv


@api.expose("/chat/read/<int:cid>/<int:mid>", methods=["get"])
@requires(auth.is_logged_in, access_error)
def chat_read(cid, mid):
    uoid = longToObjid(auth.user.id)
    if request.get_vars.all:
        chat = db(db.Chat.id == cid).select().first()
        pcountry = chat.game.playercountry()
        if pcountry:
            read = mdb.chats.upd(
                {'id': cid, 'users': {'$in': 'all'},
                 'messages': {'$size': {'$gt': mid}}},
                {'$push': {'messages.'+str(mid)+'.read': pcountry}}
            )
    else:
        read = mdb.chats.upd(
            {'id': cid, 'users': {'$in': uoid},
             'messages': {'$size': {'$gt': mid}}},
            {'$set': {'messages.'+str(mid)+'.read': True}}
        )
    return dict(status="Ok", data=read)
