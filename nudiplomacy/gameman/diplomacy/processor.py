"""
    nuDiplomacy app

    coded by Giovanni Barillari <gi0baro@d4net.org>
    copyright (C) 2013
    distributed under GNU General Public License

    This is the orders and game processor classes file.
"""
from ._glob import G


class Processor(object):
    def _set_logger(self, logger):
        if logger is not None:
            G['logger'] = logger
        self.log = G['logger']


class OrdersProcessor(Processor):
    def __init__(self, country, game, gamemap, logger=None):
        self._set_logger(logger)
        self.orders_data = None
        self.status = None
        self.error = None
        self._loadMap(gamemap)
        self._loadGame(game, country)

    def _loadMap(self, gamemap):
        self.map = {}
        self.map["moves"] = gamemap["links"]
        self.map["seas"] = gamemap["seas"]
        self.map["coasts"] = gamemap["coasts"]
        self.map["neutrals"] = gamemap["neutrals"]
        self.map["mcoasts"] = [i for i in gamemap["mcoasts"].iterkeys()]
        self.map["supply"] = gamemap["supply"]
        self.map["home"] = gamemap["homes"]
        self.map["names"] = gamemap["names"]

    def _loadGame(self, game, pcountry):
        self.game = {}
        phase = len(game["phases"])-1
        self.game["terrs"] = game["phases"][phase]["territories"][pcountry]
        self.game["supply"] = [i for i in self.map["supply"].iterkeys()] \
            if game["buildew"] else self.map["home"][pcountry]
        self.game["armies"] = []
        self.game["fleets"] = []
        for country, troops in game["phases"][phase]["troops"].iteritems():
            for el in troops["armies"]:
                self.game["armies"].append(el)
            for el in troops["fleets"]:
                self.game["fleets"].append(el)
        self.game["troops"] = game["phases"][phase]["troops"][pcountry]
        self.game["mc_pos"] = game["phases"][phase].get("mc", {})
        self.game["phase"] = game["phases"][phase]["type"]
        self.game["centers"] = []
        for k in self.map["supply"].iterkeys():
            if k in self.game["terrs"]:
                self.game["centers"].append(k)
        self.game["prev"] = game["phases"][phase-1]

    def _validate(self):
        if not self.orders_data:
            self.status = "Error"
            self.error = "Empty orders"
            return
        #: prepare data
        gdata = dict()
        for key in ["seas", "coasts", "mcoasts", "moves", "neutrals"]:
            gdata[key] = self.map[key]
        for key in ["terrs", "supply", "centers", "troops", "armies", "fleets",
                    "mc_pos", "phase", "prev"]:
            gdata[key] = self.game[key]
        #: validate orders
        from .checker import Validator
        checker = Validator(gdata, self.orders_data, self.log)
        checker.process()
        if checker.invalids:
            self.status = "Error"
            self.error = "Validation failed"
            self.log("[OrderProc] found invalid orders: " +
                     str(checker.invalids))
        else:
            self.status = "OK"
        #: clean orders from invalid ones
        for fail_id in checker.invalids:
            #to_del = None
            if fail_id in self.orders_data.iterkeys():
                if self.game["phase"] in ["diplomacy", "builds"]:
                    self.orders_data[fail_id] = dict(type="hold")
                elif self.game["phase"] == "retreats":
                    self.orders_data[fail_id] = dict(type="disband")
                #else:
                #    to_del = fail_id
            #if to_del:
            #    del self.orders_data[fail_id]

    def process(self, orders={}):
        self.orders_data = orders
        self._validate()


class GameProcessor(Processor):
    def __init__(self, game, gamemap, logger=None):
        self._set_logger(logger)
        self._loadMap(gamemap)
        self._loadGame(game)
        self.orders = dict(self.orders_data)
        self.end = False

    def _loadMap(self, gamemap):
        self.map = dict()
        self.map["seas"] = gamemap["seas"]
        self.map["names"] = gamemap["names"]
        self.map["supply"] = gamemap["supply"]
        self.map["home"] = gamemap["homes"]
        self.map["scstowin"] = gamemap["scstowin"]

    def _loadGame(self, game):
        self.game = dict()
        phase = len(game["phases"])-1
        self.game["countries"] = [country for country in
                                  game["countries"].iterkeys()]
        self.game["terrs"] = game["phases"][phase]["territories"]
        #self.game["supply"] = [i for i in self.map["supply"].iterkeys()] \
        #    if game["build_ew"] else self.map["home"]
        self.game["troops"] = game["phases"][phase]["troops"]
        self.game["armies"] = []
        self.game["fleets"] = []
        for country, troops in self.game["troops"].iteritems():
            for el in troops["armies"]:
                self.game["armies"].append(el)
            for el in troops["fleets"]:
                self.game["fleets"].append(el)
        self.game["mc_pos"] = game["phases"][phase].get("mc", {})
        self.game["phase"] = game["phases"][phase]["type"]
        self.game["season"] = game["phases"][phase].get("season")
        self.game["year"] = game["phases"][phase]["year"]
        self.game["dislodged"] = game["phases"][phase].get("dislodged", {})
        self.game["buildew"] = game["buildew"]
        self.game["scstowin"] = game["targetsc"] or self.map["scstowin"]
        self.orders_data = game["phases"][phase]["orders"]

    def _preproc(self):
        if self.game["phase"] == "builds":
            return
        from .checker import PreProcessor
        checker = PreProcessor(self.orders, self.log)
        checker.process(self.game["phase"])
        self.log("[GameProc:Pre] failed: "+str(checker.fails))
        for fail_tup in checker.fails:
            self.orders[fail_tup[0]][fail_tup[1]]['failed'] = True

    def _adjudicate(self):
        from .adjudicator import Adjudicator
        adjOrders = dict()
        for country, order in self.orders.iteritems():
            for tid, data in order.iteritems():
                adjOrders[tid] = data
                adjOrders[tid]['country'] = country
                ## remove next line in production?
                adjOrders[tid]['name'] = self.map["names"][tid]
        adj = Adjudicator(adjOrders)
        adj.adjudicate()
        self.dislodged = []
        self.log("[GameProc:Adj] --- Analysis summary:")
        for order in adj.orders.list:
            if order.succeeded:
                self.orders_data[order.country][order.id]["success"] = True
                self.log(order.name+" order succeeded.")
            else:
                if order.dislodged_unit:
                    self.dislodged.append((order.id, order.country))
                self.log(order.name+" order failed.")
        self.log("[GameProc:Adj] Dislodged units: "+str(self.dislodged))

    def _proc_builds(self):
        # if country has to disband and not enough orders are set to disband,
        # randomly add disbands
        for country, orders in self.orders_data.iteritems():
            supplyc = [i for i in self.map["supply"]
                       if i in self.game["terrs"][country]]
            troops = self.game["troops"][country]["armies"] + \
                self.game["troops"][country]["fleets"]
            if len(troops) > len(supplyc):
                disbandn = len(troops) - len(supplyc)
                disbanding = []
                others = []
                for oid, odata in orders.iteritems():
                    if odata["type"] == "disband":
                        disbanding.append(oid)
                    else:
                        others.append(oid)
                if len(disbanding) < disbandn:
                    diff = disbandn - len(disbanding)
                    todisband = others[:diff]
                    for i in todisband:
                        self.orders_data[country][i] = {'type': 'disband'}

    def _proc_retreats(self):
        for country, orders in self.orders_data.iteritems():
            for oid, odata in orders.iteritems():
                if odata["type"] == "hold":
                    odata["type"] = "disband"

    def _proc_diplomacy(self):
        self._adjudicate()

    def process(self):
        self._preproc()
        self.__getattribute__("_proc_"+self.game["phase"])()
        self._buildNewPhase()

    def _updateTroops(self, action, troops):
        self.phase_new["dislodged"] = dict()
        if action == "delete":
            for troop, country in troops:
                if troop in self._troops[country]["fleets"]:
                    self._troops[country]["fleets"].remove(troop)
                    ## remove multi-coast position if no-longer necessary
                    #if troop in self.phase_new["mc_pos"].iterkeys():
                    #   del self.phase_new["mc_pos"][troop]
                else:
                    self._troops[country]["armies"].remove(troop)
        elif action == "build":
            #for country, orders in troops.iteritems():
            #    for troop_id, troop_data in orders.iteritems():
            #        if troop_data["troop"] == "fleet":
            #            self._troops[country]["fleets"].append(troop_id)
            #        else:
            #            self._troops[country]["armies"].append(troop_id)
            for tid, country, ttype in troops:
                if ttype == "fleet":
                    self._troops[country]["fleets"].append(tid)
                    mc = self.orders_data[country][tid].get("mc")
                    if mc is not None:
                        self.phase_new["mc"][tid] = mc
                else:
                    self._troops[country]["armies"].append(tid)
        else:
            ## dislodge
            #self.phase_new["dislodged"] = dict()
            for tid, country in self.dislodged:
                if not self.phase_new["dislodged"].get(country):
                    self.phase_new["dislodged"][country] = []
                self.phase_new["dislodged"][country].append(tid)

    def _updatePositions(self, troops):
        for troop, newp, country, mc in troops:
            if troop in self._troops[country]["fleets"]:
                self._troops[country]["fleets"].remove(troop)
                self._troops[country]["fleets"].append(newp)
                ## remove multi-coast position if no-longer necessary
                #if troop in self.phase_new["mc_pos"].iterkeys():
                #   del self.phase_new["mc_pos"][troop]
                ## add multi-coast position if needed
                if mc is not None:
                    self.phase_new["mc"][newp] = mc
            else:
                self._troops[country]["armies"].remove(troop)
                self._troops[country]["armies"].append(newp)

    def _updateTerrs(self):
        for country, troops in self._troops.iteritems():
            alltroops = troops["armies"]+troops["fleets"]
            #for tid in troops["armies"]:
            for tid in alltroops:
                if tid in self.map["seas"]:
                    continue
                if self.game["season"] == "spring" and \
                        tid in self.map["supply"]:
                    continue
                if tid not in self._terrs[country]:
                    self._terrs[country].append(tid)
                    ## delete in others countries' terrs
                    for country_other, terrs in self._terrs.iteritems():
                        if country_other != country:
                            if tid in terrs:
                                self._terrs[country_other].remove(tid)

    def _setActivePlayers(self):
        country_list = []
        if self.phase_new["type"] == "diplomacy":
            country_list = [country for country in self._troops.iterkeys()]
        elif self.phase_new["type"] == "builds":
            for country, troops in self._troops.iteritems():
                supplyc = [i for i in self.map["supply"]
                           if i in self._terrs[country]]
                troop_n = len(troops["armies"])+len(troops["fleets"])
                if troop_n != len(supplyc):
                    country_list.append(country)
        else:
            #: retreats
            for country in self.phase_new["dislodged"].iterkeys():
                country_list.append(country)
        #if country_list:
        self.phase_new["countries"] = country_list

    def _removeOldMc(self):
        fleets = []
        for country, troops in self._troops.iteritems():
            fleets += troops["fleets"]
        todel = []
        for tid in self.phase_new["mc"].iterkeys():
            if tid not in fleets and tid not in todel:
                todel.append(tid)
        for tid in todel:
            del self.phase_new["mc"][tid]

    def _setEmptyOrders(self):
        self.phase_new["orders"] = dict()
        for country in self.phase_new["countries"]:
            self.phase_new["orders"][country] = dict()
            if self.phase_new["type"] == "diplomacy":
                for troops in self.phase_new["troops"][country].itervalues():
                    for troop in troops:
                        self.phase_new["orders"][country][troop] = \
                            dict(type="hold")
            elif self.phase_new["type"] == "retreats":
                for troop in self.phase_new["dislodged"][country]:
                    self.phase_new["orders"][country][troop] = \
                        dict(type="disband")
            else:
                supplyc = [i for i in self.map["supply"]
                           if i in self._terrs[country]]
                troops = self._troops[country]["armies"] + \
                    self._troops[country]["fleets"]
                if len(supplyc) > len(troops):
                    realsupply = supplyc if self.game["buildew"] else \
                        [i for i in self.map["home"][country] if
                         i in self._terrs[country]]
                    supplyorders = [i for i in realsupply if i not in troops]
                    for i in supplyorders:
                        self.phase_new["orders"][country][i] = {'type': 'hold'}
                else:
                    for i in troops:
                        self.phase_new["orders"][country][i] = {'type': 'hold'}

    def _buildPhaseData(self):
        def afterRetreats():
            if self.game["season"] == "spring":
                self.phase_new["type"] = "diplomacy"
                self.phase_new["season"] = "autumn"
            else:
                self.phase_new["type"] = "builds"
                #self.phase_new["season"] = self.game["season"]
            ## set countries' territories
            self._updateTerrs()

        ## update troops dict for defeated players
        for country in self.game["countries"]:
            if self._troops.get(country):
                if len(self._troops[country]["armies"]) == 0 and \
                   len(self._troops[country]["fleets"]) == 0:
                    ## player defeated
                    del self._troops[country]
        ## set next phase type, season and year
        if self.game["phase"] == "builds":
            self.phase_new["type"] = "diplomacy"
            self.phase_new["season"] = "spring"
            self.phase_new["year"] = self.game["year"]+1
        elif self.game["phase"] == "retreats":
            self.phase_new["year"] = self.game["year"]
            afterRetreats()
        else:
            self.phase_new["year"] = self.game["year"]
            if self.phase_new.get("dislodged"):
                self.phase_new["type"] = "retreats"
                self.phase_new["season"] = self.game["season"]
            else:
                afterRetreats()
        ## set active players in next phase
        self._setActivePlayers()
        ## set countries' troops
        self.phase_new["troops"] = self._troops
        #: update mc data
        self._removeOldMc()
        ## set empty orders
        self._setEmptyOrders()

    def _checkWin(self):
        if self.phase_new["type"] != "builds":
            return
        gotSCs = []
        for country, troops in self._troops.iteritems():
            supplyc = [i for i in self.map["supply"]
                       if i in self._terrs[country]]
            if len(supplyc) >= self.game["scstowin"]:
                gotSCs.append((country, len(supplyc)))
        if gotSCs:
            higher = max(gotSCs, key=lambda el: el[1])
            maxCount = 0
            for country, scs in gotSCs:
                if scs == higher[1]:
                    maxCount += 1
            #: if we have a draw, we must continue
            if maxCount == 1:
                self.end = True
                self.winner = higher[0]
                self.phase_new['countries'] = []
                self.phase_new['winner'] = higher[0]
                self.phase_new['type'] = 'end'

    def _buildNewPhase(self):
        ## TODO: set next phase enabled countries
        self.phase_new = dict()
        self._troops = self.game["troops"]
        self._terrs = self.game["terrs"]
        self.phase_new["mc"] = self.game["mc_pos"]
        if self.game["phase"] == "builds":
            disbands = []
            builds = []
            for country, orders in self.orders_data.iteritems():
                for order_id, order in orders.iteritems():
                    if order["type"] == "build":
                        builds.append((order_id, country, order["troop"]))
                    if order["type"] == "disband":
                        disbands.append((order_id, country))
            #self._updateTroops("build", self.orders_data)
            self._updateTroops("build", builds)
            self._updateTroops("delete", disbands)
        elif self.game["phase"] == "retreats":
            ## disband units
            disbands = []
            moves = []
            for country, tlist in self.game["dislodged"].iteritems():
                for troop in tlist:
                    disband = True
                    orders = self.orders_data[country]
                    order = orders[troop]
                    if order["type"] == "retreat":
                        if not order.get('failed', False):
                            order["success"] = True
                            disband = False
                            moves.append(
                                [troop, order["to"], country, order.get("mc")]
                            )
                    if disband:
                        disbands.append((troop, country))
            self._updateTroops("delete", disbands)
            ## update troops' positions
            self._updatePositions(moves)
        else:
            ## update troops
            self._updateTroops("dislodge", self.dislodged)
            ## make moves
            moves = []
            for country, orders in self.orders_data.iteritems():
                for order_id, order in orders.iteritems():
                    if order["type"] == "move" and order.get("success", False):
                        moves.append(
                            [order_id, order["to"], country, order.get("mc")]
                        )
            ## update troops' positions
            self._updatePositions(moves)
        self._buildPhaseData()
        self.phase_new["territories"] = self._terrs
        self._checkWin()
