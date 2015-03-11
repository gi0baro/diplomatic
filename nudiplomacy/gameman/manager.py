from time import time
from datetime import datetime, timedelta
from weppy import sdict
from nudiplomacy import app, db, mdb, queue, Map
from nudiplomacy.helpers.mongo import objidToLong, longToObjid
from nudiplomacy.helpers.system import isAppOnline
from .diplomacy import OrdersProcessor, GameProcessor


def manage():
    now = datetime.utcnow()
    app.log.debug("Manager: start run at "+str(now))
    db._adapter.reconnect()
    if not isAppOnline():
        app.log.debug("Manager: skipping due to maintainance.")
        return
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
    #: add participation points and update participation data
    for el in game.countries:
        player = objidToLong(el['player'])
        db(db.UserData.user == player).update(
            points=db.UserData.points+(1*game.nplayers),
            played=db.UserData.played+1
        )
    #: stats
    moid = longToObjid(game.map.id)
    dkey = '{:%m.%d}'.format(datetime.utcnow())
    mdb.stats_time.ioru(
        {'map': moid, 'year': datetime.utcnow().year},
        {'$inc': {
            'data.'+dkey.split(".")[0]: 1,
            'data.'+dkey: 1
        }}
    )
    mdb.stats_games.ioru(
        {'map': moid},
        {'$inc': {
            'lang.'+game.lang: 1,
            'nplayers.'+str(game.nplayers): 1,
            'pot.'+game.pottype: 1
        }}
    )
    ckeys = {}
    for k in countriesk:
        ckeys["played."+k] = 1
    mdb.stats_countries.upd({'map': moid}, {'$inc': countriesk})
    app.log.warning("Opened game "+str(gid))


def cancel_game(gid):
    from nudiplomacy.helpers.notifications import game_canceled
    db._adapter.reconnect()
    game = db.Game(id=gid)
    #: give credits back to users
    for el in game.countries:
        player = objidToLong(el['player'])
        db(db.UserData.user == player).update(
            credits=db.UserData.credits+game.bet
        )
    game_canceled(game)
    #: set as canceled
    #game.update_record(status="canceled")
    #: delete the game record
    del db.Game[game.id]


def process_game(gid):
    _days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                  "Saturday", "Sunday"]
    t0 = time()
    db._adapter.reconnect()
    game = db.Game(id=gid)
    #: do we have to skip processing today?
    if game.skipproc:
        _now = datetime.utcnow()
        _cur_day = _days_list[_now.weekday()]
        if _cur_day in game.skipproc:
            _next_proc = datetime(_now.year, _now.month, _now.day) + \
                timedelta(hours=24)
            game.update_record(status="ingame", next=_next_proc)
            return
    gamemap = Map.get_data(row=game.map)
    gamedata = game.as_dict()
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
    try:
        proc.process()
    except:
        app.log.exception("Game "+str(gid)+" processing failed.")
        game.update_record(status="crashed")
        return
    #: last orders become public
    last_phase = str(len(gamedata['phases'])-1)
    mdb.games.upd(
        {"id": gid},
        {"$set": {"phases."+last_phase+".orders": proc.finalOrders}}
    )
    #: store new phase, update game status
    if proc.end:
        nextstatus = 'win'
        nextrun = None
        #: clean orders collection
        db(db.Orders.game == gid).delete()
        #: notify game won
    else:
        nextstatus = 'ingame'
        nextrun = datetime.utcnow()+timedelta(minutes=game.phasetime)
        #: store new empty orders
        orders_new = dict(proc.phase_new['orders'])
        for el in game.countries:
            co = orders_new.get(el['country'], {})
            pid = objidToLong(el['player'])
            db((db.Orders.game == gid) & (db.Orders.player == pid)).update(
                ready=False, raw=True, data=co)
        #: notify new phase
        from nudiplomacy.helpers.notifications import game_new_phase
        game_new_phase(game)
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
        supply = gamemap['supply'].keys()
        for el in game.countries:
            if el['country'] == proc.winner:
                winner = objidToLong(el['player'])
                break
        if game.pottype == "wta":
            won = game.bet * game.nplayers
            db(db.UserData.user == winner).update(
                credits=db.UserData.credits+won)
        else:
            rel = game.bet * game.nplayers
            for el in game.countries:
                scs = [i for i in game.phases[-1]['territories'][el['country']]
                       if i in supply]
                if scs:
                    uid = objidToLong(el['player'])
                    to_add = int(round(scs*float(rel)/len(supply)))
                    db(db.UserData.user == uid).update(
                        credits=db.UserData.credits+to_add)
        #: give back original bet to all players
        for el in game.countries:
            player = objidToLong(el['player'])
            db(db.UserData.user == player).update(
                credits=db.UserData.credits+game.bet)
        #: points and stats
        db(db.UserData.user == winner).update(
            points=db.UserData.points+(2*game.nplayers),
            won=db.UserData.won+1)
        moid = longToObjid(gamemap['id'])
        for el in game.countries:
            if el['country'] == proc.winner:
                mdb.stats_countries.upd(
                    {'map': moid},
                    {'$inc': {'won.'+el['country']: 1}})
                continue
            uid = objidToLong(el['player'])
            scs = [i for i in game.phases[-1]['territories'][el['country']]
                   if i in supply]
            if not scs:
                #: defeated
                db(db.UserData.user == uid).update(
                    points=db.UserData.points-(1*game.nplayers),
                    defeated=db.UserData.defeated+1)
                mdb.stats_countries.upd(
                    {'map': moid},
                    {'$inc': {'defeated.'+el['country']: 1}})
            else:
                #: survived
                db(db.UserData.user == uid).update(
                    survived=db.UserData.survived+1)
                mdb.stats_countries.upd(
                    {'map': moid},
                    {'$inc': {'survived.'+el['country']: 1}})
        nturns = proc.phase_new['year']-gamemap['year']
        mdb.stats_games.ioru(
            {'map': moid}, {'$inc': {'turns.'+str(nturns): 1}}
        )
    dt = time() - t0
    app.log.warning("Processed game "+str(gid)+" in "+str(dt))
