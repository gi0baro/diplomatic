import random
from weppy import AppModule, request, sdict
from weppy.tools import ServiceHandler, requires
from nudiplomacy import app, auth, db, mdb, Orders
from nudiplomacy.helpers.mongo import longToObjid
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
        rv.phases = game.phases
        rv.countries = [el['country'] for el in game.countries]
        #rv.countries = game.countries.keys()
        rv.buildew = game.buildew
        rv.scs = game.targetsc
        rv.presstype = game.presstype
        rv.currentPlayer = game.playercountry()
    return rv


@api.expose("/game/<int:gid>/status")
def game_status(gid):
    game = db(db.Game.id == gid).select(db.Game.status, db.Game.phases).first()
    return dict(status=game.status, phase=len(game.phases)-1)


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
    #: is the user already in game?
    poid = longToObjid(auth.user.id)
    for el in gamedata.countries:
        if el['player'] == poid:
            rv.data = "You've already joined the game"
            return rv
    #: evaluate available countries
    #app.log.debug(gamedata.countries)
    #slots = list(gamedata.phases[0]['countries'])
    #for el in gamedata.countries:
    #    slots.remove(el['country'])
    #app.log.debug(slots)
    #: does the game have available slots?
    #if not countrydict.keys():
    slots = list(gamedata.slots)
    if not slots:
        rv.data = "No slots available"
        return rv
    if gamedata.countriesassign == "random":
        #: try to pick a random country
        joined = False
        while not joined:
            #chosen = random.choice(countrydict.keys())
            chosen = random.choice(slots)
            #updated = mdb.games.fandm(
            #    {"id": gid, "countries."+chosen: None},
            #    {"$set": {"countries."+chosen: longToObjid(auth.user.id)}},
            #    fields=["countries"],
            #    new=True
            #)
            updated = mdb.games.fandm(
                {'id': gid, 'open': True,
                 'countries.country': {'$ne': chosen}},
                {'$push': {'countries': {'country': chosen, 'player': poid}},
                 '$pull': {'slots': chosen}},
                fields=['countries', 'slots'],
                new=True
            )
            if not updated:
                #: someone else has joined with chosen country in the meantime
                #del countrydict[chosen]
                slots.remove(chosen)
            else:
                joined = True
                #db(db.UserData.user == auth.user.id).update(
                #    credits=db.UserData.credits-gamedata.bet)
                playerdata.update_record(
                    credits=playerdata.credits-gamedata.bet)
                ##if all([v is not None for v in updated.countries.itervalues()]):
                #if len(updated.countries) == gamedata.phases[0]['countries']:
                if not updated.slots:
                    toset = {'open': False}
                    if gamedata.status == "pregame":
                        toset['ready'] = True
                    mdb.games.upd(
                        {"id": gid, "open": True},
                        {"$set": toset}
                    )
            if not slots:
                break
        if not joined:
            rv.data = "No slots available"
            return rv
    else:
        chosen = request.get_vars.country
        #: has the user chosen a country?
        #if not chosen:
        if chosen not in slots:
            rv.data = "You have to pick a country"
            return rv
        #updated = mdb.games.fandm(
        #    {"id": gid, "countries."+chosen: None},
        #    {"$set": {"countries."+chosen: longToObjid(auth.user.id)}},
        #    fields=["countries"],
        #    new=True
        #)
        updated = mdb.games.fandm(
            {'id': gid, 'open': True, 'countries.country': {'$ne': chosen}},
            {'$push': {'countries': {'country': chosen, 'player': poid}}},
            fields=['countries'],
            new=True
        )
        if not updated:
            #: someone else has joined with chosen country in the meantime
            rv.data = "Selected country not available"
        else:
            #db(db.UserData.user == auth.user.id).update(
            #    credits=db.UserData.credits-gamedata.bet)
            playerdata.update_record(credits=playerdata.credits-gamedata.bet)
            ##if all([v is not None for v in updated.countries.itervalues()]):
            #if len(updated.countries) == gamedata.phases[0]['countries']:
            if not updated.slots:
                toset = {'open': False}
                if gamedata.status == "pregame":
                    toset['ready'] = True
                mdb.games.upd(
                    {"id": gid, "open": True},
                    {"$set": toset}
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
        try:
            since = int(request.vars.since)
        except:
            since = 0
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
        chat = db(
            (db.Chat.id == cid) & (db.Chat.open == True)).select().first()
        if chat:
            pcountry = chat.game.playercountry()
            mdata = {'text': message, 'timeref': request.now, 'from': pcountry}
            if chat.users == ["all"]:
                players = [el['player'] for el in chat.game.countries]
                can = longToObjid(auth.user.id) in players
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
                {'id': cid, 'users': 'all',
                 'messages.'+str(mid): {'$exists': True}},
                {'$push': {'messages.'+str(mid)+'.read': pcountry}}
            )
    else:
        read = mdb.chats.upd(
            {'id': cid, 'users': uoid,
             'messages.'+str(mid): {'$exists': True}},
            {'$set': {'messages.'+str(mid)+'.read': True}}
        )
    return dict(status="Ok", data=read)
