from datetime import datetime, timedelta
from weppy import sdict
from nudiplomacy import app, db, mdb, queue
from nudiplomacy.helpers.mongo import objidToLong, longToObjid
from .diplomacy import OrdersProcessor, GameProcessor


def manage():
    now = datetime.utcnow()
    app.log.debug("Manager: start run at "+str(now))
    db._adapter.reconnect()
    # start ready-asap pregames
    toStart = db(
        (db.Game.status == "pregame") & (db.Game.ready == True) &
        (db.Game.starton == "asap")
    ).select()
    app.log.debug(toStart)
    for game in toStart:
        game.update_record(status="processing", ready=False)
        # enqueue
        queue.save(open_game, 'open', gid=game.id)
    # start ready pregames
    toStart = db(
        (db.Game.status == "pregame") & (db.Game.ready == True) &
        (db.Game.starton == "ontime") & (db.Game.next <= now)
    ).select()
    app.log.debug(toStart)
    for game in toStart:
        game.update_record(status="processing", ready=False)
        # enqueue
        queue.save(open_game, 'open', gid=game.id)
    # cancel expired pregames
    toCancel = db(
        (db.Game.status == "pregame") & (db.Game.ready == False) &
        (db.Game.next <= now)
    ).select()
    for game in toCancel:
        game.update_record(status="processing", open=False)
        queue.save(cancel_game, 'open', gid=game.id)
    # process new phases
    toProcess = db(
        (db.Game.status == "ingame") & (db.Game.ready == True)).select()
    app.log.debug(toProcess)
    for game in toProcess:
        game.update_record(status="processing", ready=False)
        #enqueue
        queue.save(process_game, 'proc', gid=game.id)
    toProcess = db(
        (db.Game.status == "ingame") & (db.Game.ready == False) &
        (db.Game.next <= now)
    ).select()
    app.log.debug(toProcess)
    for game in toProcess:
        game.update_record(status="processing")
        #enqueue
        queue.save(process_game, 'proc', gid=game.id)


def process_orders(country, game, orders):
    gamemap = game.map.as_dict()
    game = game.as_dict()
    # temp workaround for str->int conversion
    ch = ["neutrals", "seas", "coasts"]
    for c in ch:
        for i in range(0, len(gamemap[c])):
            gamemap[c][i] = str(gamemap[c][i])
    #
    proc = OrdersProcessor(country, game, gamemap, app.log.warning)
    proc.process(orders)
    return sdict(error=proc.error, orders=proc.orders_data)


def open_game(gid):
    db._adapter.reconnect()
    game = db.Game(id=gid)
    #: init orders
    for el in game.countries:
        orders = {}
        if game.buildonstart:
            for ttype in ["armies", "fleets"]:
                for t in game.map.init["troops"][el['country']][ttype]:
                    if ttype == "armies":
                        orders[t] = {"type": "build", "troop": "army"}
                    elif ttype == "fleets":
                        orders[t] = {"type": "build", "troop": "fleet"}
                        if game.map.init["mc"].get(t) is not None:
                            orders[t]["mc"] = game.map.init["mc"][t]
        else:
            for ttype in ["armies", "fleets"]:
                for t in game.map.init["troops"][el['country']][ttype]:
                    orders[t] = {"type": "hold"}
        db.Orders.insert(
            game=game.id, player=objidToLong(el['player']), data=orders)
    #: init chats
    presstype = game.presstype
    if presstype == "all":
        plist = [el['player'] for el in game.countries]
        for i in range(0, len(plist)-1):
            for j in range(i+1, len(plist)):
                #db.Chat.insert(game=gid, users=[plist[i], plist[j]])
                mdb.chats.save(
                    {'game': longToObjid(gid), 'users': [plist[i], plist[j]],
                     'open': True, 'messages': []}
                )
    #: init game
    orders = {}
    territories = {}
    countriesk = [el['country'] for el in game.countries]
    for k in countriesk:
        orders[k] = {}
        territories[k] = game.map.init['territories'][k]
    nphase = {
        "territories": territories,
        "mc": {},
        "dislodged": {},
        "orders": {},
        "countries": countriesk
    }
    if game.buildonstart:
        troops = {}
        for k in countriesk:
            troops[k] = {"armies": [], "fleets": []}
        nphase.update(
            year=game.map.year-1,
            type="builds",
            troops=troops
        )
    else:
        troops = {}
        for k in countriesk:
            troops[k] = game.map.init["troops"][k]
        nphase.update(
            year=game.map.year,
            type="diplomacy",
            season="spring",
            troops=troops
        )
        if game.map.init["mc"]:
            nphase.update(mc=game.map.init["mc"])
    nextrun = datetime.utcnow()+timedelta(minutes=game.phasetime)
    mdb.games.upd(
        {"id": gid},
        {"$set": {
            "active": True, "status": "ingame", "ready": False,
            "next": nextrun, "processed": datetime.utcnow()},
         "$push": {"phases": nphase}}
    )
    app.log.warning("Opened game "+str(gid))


def cancel_game(gid):
    db._adapter.reconnect()
    game = db.Game(id=gid)
    #: give credits back to users
    for el in game.countries:
        player = objidToLong(el['player'])
        db(db.Userdata.user == player).update(
            credits=db.Userdata.credits+game.bet
        )
    #: set as canceled
    game.update_record(status="canceled")


def process_game(gid):
    db._adapter.reconnect()
    game = db.Game(id=gid)
    gamemap = game.map.as_dict()
    gamedata = game.as_dict()
    # temp workaround for str->int conversion
    ch = ["neutrals", "seas", "coasts"]
    for c in ch:
        for i in range(0, len(gamemap[c])):
            gamemap[c][i] = str(gamemap[c][i])
    #
    #: get game orders
    ordersrows = db(db.Orders.game == gid).select()
    porders = {}
    orders = {}
    for row in ordersrows:
        porders[row.player] = row.data
    for el in game.countries:
        if el['country'] in game.phases[-1]['countries']:
            orders[el['country']] = porders[objidToLong(el['player'])]
    app.log.info(orders)
    gamedata['phases'][-1]['orders'] = orders
    #: process the game
    proc = GameProcessor(gamedata, gamemap, app.log.info)
    proc.process()
    app.log.info(proc.phase_new)
    print proc.phase_new
    #game.update_record(status="ingame")
    #: last orders become public
    last_phase = str(len(gamedata['phases'])-1)
    mdb.games.upd(
        {"id": gid},
        {"$set": {"phases."+last_phase+".orders": proc.orders_data}}
    )
    #: store new phase, update game status
    if proc.end:
        nextstatus = 'win'
        nextrun = None
        #: clean orders collection
        db(db.Orders.game == gid).delete()
    else:
        nextstatus = 'ingame'
        nextrun = datetime.utcnow()+timedelta(minutes=game.phasetime)
        #: store new empty orders
        orders_new = dict(proc.phase_new['orders'])
        for el in game.countries:
            co = orders_new.get(el['country'], {})
            pid = objidToLong(el['player'])
            db((db.Orders.game == gid) & (db.Orders.player == pid)).update(
                ready=False, data=co)
    proc.phase_new['orders'] = {}
    mdb.games.upd(
        {"id": gid},
        {"$set": {
            "status": nextstatus, "next": nextrun,
            "processed": datetime.utcnow()},
         "$push": {"phases": proc.phase_new}}
    )
    #: finalize game end if needed
    if proc.end:
        game.update_record(active=False)
        #: close chats
        db(db.Chat.game == gid).update(open=False)
        #: credits
        for el in game.countries:
            if el['country'] == proc.winner:
                winner = objidToLong(el['player'])
                break
        if game.pottype == "wta":
            won = game.bet * game.nplayers
            db(db.Userdata.user == winner).update(
                credits=db.Userdata.credits+won)
        else:
            pass
        #: give back original bet to all players
        for el in game.countries:
            player = objidToLong(el['player'])
            db(db.Userdata.user == player).update(
                credits=db.Userdata.credits+game.bet)
    app.log.warning("Processed game "+str(gid))
