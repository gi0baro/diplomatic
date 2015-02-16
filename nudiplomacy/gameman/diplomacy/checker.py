from ._glob import G


class Validator(object):
    def __init__(self, gdata, orders, logger=None):
        self._logger = logger or G['logger']
        self.log = lambda x: self._logger("[Validator] "+x)
        self.log(str(gdata))
        self.orders = orders
        self.seas = gdata["seas"]
        self.coasts = gdata["coasts"]
        self.mcoasts = gdata["mcoasts"]
        self.neutrals = gdata["neutrals"]
        self.moves = gdata["moves"]
        self.troops = gdata["troops"]["armies"]+gdata["troops"]["fleets"]
        self.terrs = gdata["terrs"]
        self.supply = gdata["supply"]
        self.centers = gdata["centers"]
        self.armies = gdata["armies"]
        self.fleets = gdata["fleets"]
        self.mc_pos = gdata["mc_pos"]
        self.phase = gdata["phase"]
        self.prev = gdata["prev"]
        self.__convoy_maps = {}
        self._convoy_routes = {}
        self._convoy_routes_stacks = []
        self.invalids = []

    def _canMove(self, From, To, mc=None):
        if self._isFleet(From):
            if mc:
                return To in self.moves["mc"][From][mc]
            return To in self.moves["fleets"][From]
        else:
            return To in self.moves["armies"][From]

    def _isEmptyTerr(self, Id):
        if Id not in self.armies:
            if Id not in self.fleets:
                return True
        return False

    def _isFleet(self, Id):
        return Id in self.fleets

    def _isSea(self, Id):
        return Id in self.seas

    def _isCoast(self, Id):
        return Id in self.coasts

    def _isMCoast(self, Id):
        return Id in self.mcoasts

    def _isConvoying(self, Id):
        for orders_set in self.orders.itervalues():
            for order_id, order in orders_set.iteritems():
                if order_id == Id and order["type"] == "convoy":
                    return True
        return False

    def _set_convoy_route(self, fr, to, stack):
        key = fr+"-"+to
        if self._convoy_routes.get(key) is None:
            self._convoy_routes[key] = []
        self._convoy_routes[key].append(stack)

    def _get_convoy_map(self, Id):
        res = []
        procstack = []
        #nears_o = self.moves["armies"].get(Id)
        flinks = self.moves["fleets"].get(Id, [])
        for terr in flinks:
            if self._isFleet(terr) and self._isSea(terr):
                #nears_f[terr] = dict(step=1, pre=None)
                procstack.append((terr, 1))
        step = 1
        index = 0
        _routes = [[]]
        while len(procstack) > 0:
            node, nstep = procstack.pop()
            ntype = "fleet"
            if not (self._isFleet(node) and self._isSea(node)):
                if self._isCoast(node):
                    ntype = "coast"
                else:
                    continue
            if ntype is "fleet":
                if nstep > step:
                    step += 1
                if nstep < step:
                    index += 1
                    _routes.append(_routes[-1][0:step])
                    step = nstep
                #: add node to processing list
                _routes[index].append(node)
                node_links = self.moves["fleets"].get(node, [])
                for chnode in node_links:
                    procstack.insert((chnode, step))
            else:
                #: close the route
                self._set_convoy_route(Id, node, _routes[index])
                if node not in res:
                    res.append(node)
        return res

    def _convoy_maps(self, Id):
        if self.__convoy_maps.get(Id) is None:
            self.__convoy_maps[Id] = self._get_convoy_map(Id)
        return self.__convoy_maps[Id]

    #def _ver_convoy_route_stack(self, index):
    #   for fleet in self._convoy_routes_stacks[index]:
    #       if not self._isConvoying(fleet):
    #           return False
    #   return True

    def _get_convoy_routes(self, fr, to):
        return self._convoy_routes.get(fr+"-"+to, [])

    def _check_neutrals(self):
        for order_id, order in self.orders.iteritems():
            if order_id in self.neutrals:
                self.invalids.append(order_id)
                self.log("Order "+str(order_id)+" is made on neutral state")
                continue
            if order.get('to') in self.neutrals:
                self.invalids.append(order_id)
                self.log("Order "+str(order_id)+" is to a neutral state")
                continue
            if order.get('from') in self.neutrals:
                self.invalids.append(order_id)
                self.log("Order "+str(order_id)+" has 'from' set to a " +
                         "neutral state")

    def _check_troops(self):
        for order_id in self.orders.iterkeys():
            ## check order is on player's armies
            if order_id not in self.troops:
                self.invalids.append(order_id)
                self.log("Order "+str(order_id)+" is not in player troops")

    """
    def _check_supplCent(self):
        for order_id in self.orders.iterkeys():
            ## check order is on player's armies
            if order_id not in self.supply:
                self.invalids.append(order_id)
                self.log("Order "+str(order_id)+" is not in player supply")
                continue
            if order_id not in self.terrs:
                self.invalids.append(order_id)
                self.log("Order "+str(order_id)+" is not in player terrs")
                #continue
    """

    def _process_base(self):
        ## this should check order integrity
        #if self.phase == "builds":
        #    self._check_supplCent()
        #else:
        self._check_neutrals()
        if self.phase != "builds":
            self._check_troops()
        for order in self.invalids:
            del self.orders[order]

    def _process_builds(self):
        ## process builds
        for order_id, order in self.orders.iteritems():
            ## check order integrity
            if order.get("type") not in ["hold", "build", "disband"]:
                self.invalids.append(order_id)
                continue
            if order["type"] == "build" and not order.get("troop"):
                self.invalids.append(order_id)
                continue
            ## check build order has not a troop and disband viceversa
            if order["type"] == "build":
                if order_id in self.troops:
                    self.invalids.append(order_id)
                    continue
                if order_id not in self.supply:
                    self.invalids.append(order_id)
                    self.log("Order "+str(order_id)+" is not in player supply")
                    continue
                if order_id not in self.terrs:
                    self.invalids.append(order_id)
                    self.log("Order "+str(order_id)+" is not in player terrs")
                    continue
            elif order["type"] == "disband":
                if order_id not in self.troops:
                    self.invalids.append(order_id)
                    continue
            ## check build of fleets is only on coasts supply centers
            if order["type"] == "build" and order["troop"] == "fleet":
                ## need to check is a coast!
                if not self._isCoast(order_id):
                    self.invalids.append(order_id)
                    self.log("Order "+str(order_id)+" is not on a coast")
                    continue
                if self._isMCoast(order_id) and order.get("mc") is None:
                    self.invalids.append(order_id)
                    self.log("Order "+str(order_id)+" has no mc parameter")
        #: process builds considering country details
        if len(self.centers) > len(self.troops):
            realsupply = [i for i in self.supply if i in self.terrs and
                          i not in self.troops]
            for order_id, order in self.orders.iteritems():
                if order_id in self.invalids:
                    continue
                if order_id not in realsupply:
                    self.invalids.append(order_id)
                    continue
                if order["type"] == "disband":
                    self.invalids.append(order_id)
                    continue
            allowedn = len(self.centers) - len(self.troops)
            buildorders = [i for i in self.orders.keys()
                           if i not in self.invalids and
                           self.orders[i]["type"] == "build"]
            if len(buildorders) > allowedn:
                #: remove exceeding orders
                diff = len(buildorders) - allowedn
                to_rem = buildorders[:diff]
                for i in to_rem:
                    self.invalids.append(i)
        else:
            for order_id, order in self.orders.iteritems():
                if order_id in self.invalids:
                    continue
                if order["type"] == "build":
                    self.invalids.append(order_id)
                    continue
            disbandn = len(self.troops) - len(self.centers)
            buildorders = [i for i in self.orders.keys()
                           if i not in self.invalids]
            if len(buildorders) > disbandn:
                #: remove exceeding orders
                diff = len(buildorders) - disbandn
                to_rem = buildorders[:diff]
                for i in to_rem:
                    self.invalids.append(i)

    def _process_retreats(self):
        prevmoveorders = []
        for c, d in self.prev["orders"].iteritems():
            for tid, tdata in d.iteritems():
                if tdata["type"] == "move":
                    prevmoveorders.append(tdata["to"])
        for order_id, order in self.orders.iteritems():
            if not order.get("to"):
                ## we process only retreats
                #self.invalids.append(order_id)
                if order["type"] != "disband":
                    self.invalids.append(order_id)
                continue
            if self._isFleet(order_id) and self._isMCoast(order["to"]):
                if order.get("mc") not in [0, 1]:
                    self.invalids.append(order_id)
                    continue
            if not self._canMove(order_id, order["to"], order.get("mc")):
                self.log("Order " + str(order_id) +
                         " is a retreat to a terr cannot move")
                self.invalids.append(order_id)
                continue
            # cannot move to a terr where was a move
            if order["to"] in prevmoveorders:
                self.invalids.append(order_id)
                continue

    def _process_diplomacy(self):
        for order_id, order in self.orders.iteritems():
            ## order should have:
            ##      - id: terr in which the army is
            ##      - type: type of order (should be in
            ##              ["move", "sup_move", "sup_hold", "convoy"])
            ##      - (from): id of terr in which the order starts
            ##      - (to): id of terr in which the order ends (if not hold)
            ##      - (viaConvoy): True if is a move via convoy
            ##      - (mc): id of multi coast to move (if needed)
            if order["type"] != "hold" and not order.get("to"):
                self.invalids.append(order_id)
                continue
            if order["type"] in ["sup_move", "convoy"]:
                if not order.get("from"):
                    self.invalids.append(order_id)
                    continue
            ## check basics movements rules
            if order["type"] == "move":
                if not order.get("viaConvoy"):
                    ## mc parameter check
                    if self._isFleet(order_id) and self._isMCoast(order["to"]):
                        #if not order.get("mc"):
                        #   self.invalids.append(order_id)
                        #   continue
                        if order.get("mc") not in [0, 1]:
                            self.log("Order "+str(order_id)+" has a bad mc")
                            self.invalids.append(order_id)
                            continue
                    else:
                        if order.get("mc"):
                            del order["mc"]
                    ## check move ability
                    mc = None
                    if self._isFleet(order_id) and self._isMCoast(order_id):
                        mc = self.mc_pos[order_id]
                    if not self._canMove(order_id, order["to"], mc):
                        self.log("Order " + str(order_id) +
                                 " is a move to a terr cannot move")
                        self.invalids.append(order_id)
                else:
                    ## cannot convoy fleets
                    if self._isFleet(order_id):
                        self.log("Order "+str(order_id)+" is a fleet convoyed")
                        self.invalids.append(order_id)
                        continue
                    ## check convoy route present (needed for ui)
                    if not order.get("convoy_route"):
                        self.log("Order " + str(order_id) +
                                 " is a move viaConvoy without route")
                        self.invalids.append(order_id)
                        continue
                    ## check move via convoy ability
                    if order["to"] not in self._convoy_maps(order_id):
                        self.log("Order " + str(order_id) +
                                 " is a move viaConvoy to a terr cannot move")
                        self.invalids.append(order_id)
                    else:
                        ## verify routes (find out orders built without ui)
                        convoy_routes = self._get_convoy_routes(order_id,
                                                                order["to"])
                        if order["convoy_route"] not in convoy_routes:
                            self.log("Order " + str(order_id) +
                                     " is a move viaConvoy with invalid route")
                            self.invalids.append(order_id)
                            continue
                        ## store convoy routes (needed for proc)
                        order["convoy_routes"] = convoy_routes
            elif order["type"] == "sup_move":
                if not self._canMove(order_id, order["to"]):
                    self.log("Order " + str(order_id) +
                             " is a sup_move against a terr cannot move")
                    self.invalids.append(order_id)
                    continue
                ## check if there's an army or ship in to terr
                if self._isEmptyTerr(order["from"]):
                    self.log("Order " + str(order_id) +
                             " is a sup_move to an empty terr")
                    self.invalids.append(order_id)
            elif order["type"] == "sup_hold":
                if not self._canMove(order_id, order["to"]):
                    self.log("Order " + str(order_id) +
                             " is a sup_hold to a terr cannot move")
                    self.invalids.append(order_id)
                    continue
                ## check if there's an army or ship in to terr
                if self._isEmptyTerr(order["to"]):
                    self.log("Order " + str(order_id) +
                             " is a sup_hold to an empty terr")
                    self.invalids.append(order_id)
            elif order["type"] == "convoy":
                if not self._isFleet(order_id):
                    self.log("Order "+str(order_id)+" is a convoy by an army")
                    self.invalids.append(order_id)
            else:
                if order["type"] != "hold":
                    self.log("Order "+str(order_id)+" is an invalid type")
                    self.invalids.append(order_id)
                    continue
                if len(order) > 1:
                    order = dict(type="hold")

    def process(self):
        self._process_base()
        self.__getattribute__("_process_"+self.phase)()
        return self.invalids


class PreProcessor(object):
    def __init__(self, orders, logger=None):
        self._logger = logger or G['logger']
        self.log = lambda x: self._logger("[PreProc] "+x)
        self.orders = orders
        self.fails = []

    def _isMoving(self, Id):
        for orders_set in self.orders.itervalues():
            for order_id, order in orders_set.iteritems():
                if order_id == Id and order["type"] == "move":
                    return True
        return False

    def _isMovingTo(self, Id, To):
        for orders_set in self.orders.itervalues():
            for order_id, order in orders_set.iteritems():
                if order_id == Id and order["type"] == "move" and \
                        order["to"] == To:
                    return True
        return False

    def _isConvoyingFT(self, Id, fr, to):
        for orders_set in self.orders.itervalues():
            for order_id, order in orders_set.iteritems():
                if order_id == Id:
                    if order["type"] == "convoy" and order["to"] == to and \
                            order["from"] == fr:
                        return True
                    break
        return False

    def _process_retreats(self):
        fails = []
        retreats = dict()
        for player, orders_set in self.orders.iteritems():
            for order_id, order in orders_set.iteritems():
                if order["type"] == "retreat":
                    if not retreats.get(order["to"]):
                        retreats[order["to"]] = dict(count=0, data=[])
                    retreats[order["to"]]["count"] += 1
                    retreats[order["to"]]["data"].append((player, order_id))
        for retreat in retreats.itervalues():
            if retreat["count"] > 1:
                ## fails all
                for el in retreat["data"]:
                    fails.append(el)
        return fails

    def _process_diplomacy(self):
        for player, orders_set in self.orders.iteritems():
            for order_id, order in orders_set.iteritems():
                #order_id = player+":"+order["id"]
                if order["type"] == "sup_hold":
                    ## support hold to moving units fails
                    if self._isMoving(order["to"]):
                        self.fails.append((player, order_id))
                elif order["type"] == "sup_move":
                    ## support move to unit not moving or moving to another
                    ## terr fails
                    if not self._isMoving(order["from"]):
                        self.fails.append((player, order_id))
                        continue
                    if not self._isMovingTo(order["from"], order["to"]):
                        self.fails.append((player, order_id))
                elif order["type"] == "convoy":
                    ## convoy unit which is not moving or moving to another
                    ## terr fails
                    if not self._isMovingTo(order["from"], order["to"]):
                        self.fails.append((player, order_id))
                ## add check for convoy route (move + viaConvoy)
                elif order["type"] == "move":
                    if order.get("viaConvoy"):
                        bad_routes = []
                        succ = False
                        for route in order["convoy_routes"]:
                            route_succ = True
                            for fleet in route:
                                if not self._isConvoyingFT(fleet, order_id,
                                                           order["to"]):
                                    route_succ = False
                                    break
                            if route_succ:
                                succ = True
                                ## we need to process every route
                            else:
                                ## here we have to remove the route from list
                                bad_routes.append(route)
                        if not succ:
                            self.fails.append((player, order_id))
                        else:
                            for route in bad_routes:
                                order["convoy_routes"].remove(route)

    def process(self, phase):
        if phase == "retreats":
            ## we have to verify conflicts (retreats to same terrs fails both)
            self._process_retreats()
        else:
            self._process_diplomacy()
