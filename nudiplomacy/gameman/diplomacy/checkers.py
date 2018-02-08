# -*- coding: utf-8 -*-

from collections import defaultdict
from .helpers import registry


class ValidationPipeline(object):
    def __init__(self, *methods):
        self.methods = methods

    @staticmethod
    def _get_pipe_orders(orders, invalid):
        return {key: orders[key] for key in set(orders.keys()) - invalid}

    def process(self, orders):
        rv = []
        for method in self.methods:
            rv.extend(method(self._get_pipe_orders(orders, rv)))
        return rv


class Validator(object):
    processors = registry()

    def __init__(
        self, map_data, player_troops, territories, armies, fleets,
        multi_coasts_positions, phase_type, previous_phase, logger=None
    ):
        self._logger = logger
        self._load_map(map_data)
        self.player_troops = player_troops
        self.territories = territories
        self.armies = armies
        self.fleets = fleets
        self.multi_coasts_positions = multi_coasts_positions
        self.phase_type = phase_type
        self.previous_phase = previous_phase
        self.__convoy_maps = {}
        self._convoy_routes = defaultdict(lambda: list())
        self._convoy_routes_stacks = []

    def _load_map(self, data):
        self.seas = data["seas"]
        self.coasts = data["coasts"]
        self.neutrals = data["neutrals"]
        self.multi_coasts = list(data["multi_coasts"].keys())
        self.supply_centers = data["supply_centers"]
        self.home_centers = data["home_centers"]
        self.links = data["links"]

    def log(self, msg):
        if not self._logger:
            return
        self._logger(msg)

    def _can_move(self, src, dst, mc=None):
        if self._is_fleet(src):
            if mc is not None:
                return dst in self.links["mc"][src][mc]
            return dst in self.links["fleets"][src]
        return dst in self.links["armies"][src]

    def _is_empty_territory(self, territory_id):
        if (
            territory_id not in self.armies and territory_id not in self.fleets
        ):
            return True
        return False

    def _is_fleet(self, territory_id):
        return territory_id in self.fleets

    def _is_sea(self, territory_id):
        return territory_id in self.seas

    def _is_coast(self, territory_id):
        return territory_id in self.coasts

    def _is_multi_coast(self, territory_id):
        return territory_id in self.mcoasts

    # def _is_convoying(self, territory_id):
    #     return self.orders.get(territory_id, {}).get('type') == "convoy"

    @staticmethod
    def _convoy_route_key(src, dst):
        return "-".join([src, dst])

    def _set_convoy_route(self, src, dst, stack):
        self._convoy_routes[self._convoy_route_key(src, dst)].append(stack)

    def _get_convoy_map(self, territory_id):
        rv = []
        procstack = []
        flinks = self.links["fleets"].get(territory_id, [])
        for terr in flinks:
            if self._is_fleet(terr) and self._is_sea(terr):
                procstack.append((terr, 1))
        step = 1
        index = 0
        _routes = [[]]
        while len(procstack) > 0:
            node, nstep = procstack.pop(0)
            ntype = "fleet"
            if not (self._is_fleet(node) and self._is_sea(node)):
                if self._is_coast(node):
                    ntype = "coast"
                else:
                    if procstack:
                        index += 1
                        _routes.append(_routes[-1][0:procstack[0][1] - 1])
                    continue
            if node in _routes[index]:
                if procstack:
                    index += 1
                    _routes.append(_routes[-1][0:procstack[0][1] - 1])
                continue
            if nstep > step:
                step += 1
            if nstep < step:
                index += 1
                _routes.append(_routes[-1][0:nstep - 1])
                step = nstep
            if ntype is "fleet":
                #: add node to processing list
                _routes[index].append(node)
                node_links = self.links["fleets"].get(node, [])
                for chnode in node_links:
                    if chnode not in [node, territory_id]:
                        procstack.insert(0, (chnode, step + 1))
            else:
                #: close the route
                self._set_convoy_route(territory_id, node, _routes[index])
                if node not in rv:
                    rv.append(node)
                if procstack and procstack[0][1] == step:
                    index += 1
                    _routes.append(_routes[-1][0:step - 1])
        return rv

    def _convoy_maps(self, territory_id):
        if self.__convoy_maps.get(territory_id) is None:
            self.__convoy_maps[territory_id] = self._get_convoy_map(territory_id)
        return self.__convoy_maps[territory_id]

    def _get_convoy_routes(self, src, dst):
        return self._convoy_routes.get(self._convoy_route_key(src, dst), [])

    def _check_neutrals(self):
        for territory_id, order in self.orders.items():
            if territory_id in self.neutrals:
                self.invalids.append(territory_id)
                self.log("Order " + str(territory_id) + " is made on neutral state")
                continue
            if order.get('src') in self.neutrals:
                self.invalids.append(territory_id)
                self.log("Order " + str(territory_id) + " is to a neutral state")
                continue
            if order.get('dst') in self.neutrals:
                self.invalids.append(territory_id)
                self.log("Order " + str(territory_id) + " has 'from' set to a " + "neutral state")

    def _check_troops(self):
        #: check order is on player's armies
        for territory_id in set(self.orders.keys()) - set(self.player_troops):
            self.invalids.append(territory_id)
            self.log("Order " + str(territory_id) + " is not in player troops")

    def _process_base(self):
        #: this should check order integrity
        self._check_neutrals()
        if self.phase_type != "builds":
            self._check_troops()
        for order in self.invalids:
            del self.orders[order]

    def _validate_builds(self, orders):
        invalids = []
        #: process builds
        for territory_id, order in orders.items():
            #: check order integrity
            if order.get("type") not in {"hold", "build", "disband"}:
                invalids.append(territory_id)
                continue
            if order["type"] == "build" and not order.get("troop"):
                invalids.append(territory_id)
                continue
            #: check build order has not a troop and disband viceversa
            if order["type"] == "build":
                if territory_id in self.troops:
                    invalids.append(territory_id)
                    continue
                if territory_id not in self.supply_centers:
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " is not in player supply")
                    continue
                if territory_id not in self.territories:
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " is not in player terrs")
                    continue
            elif order["type"] == "disband":
                if territory_id not in self.troops:
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " is not in player troops")
                    continue
            #: check build of fleets is only on coasts supply centers
            if order["type"] == "build" and order["troop"] == "fleet":
                #: need to check is a coast!
                if not self._is_coast(territory_id):
                    invalids.append(territory_id)
                    self.log("Order "+str(territory_id)+" is not on a coast")
                    continue
                if self._is_multi_coast(territory_id) and order.get("mc") is None:
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " has no mc parameter")
        #: process builds considering country details
        if len(self.centers) > len(self.troops):
            available_supply_centers = (set(self.supply_centers) & set(self.territories)) - set(self.troops)
            for territory_id, order in orders.items():
                if territory_id in invalids:
                    continue
                if territory_id not in available_supply_centers:
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " is not in player supply")
                    continue
                if order["type"] == "disband":
                    invalids.append(territory_id)
                    self.log("Player must build, not disband: " + str(territory_id))
                    continue
            allowed_builds_no = len(self.centers) - len(self.troops)
            build_orders = set([territory_id for territory_id in orders.keys() if orders[territory_id]["type"] == "build"]) - set(invalids)
            if len(build_orders) > allowed_builds_no:
                #: remove exceeding orders
                diff = len(build_orders) - allowed_builds_no
                to_rem = build_orders[:diff]
                for element in to_rem:
                    invalids.append(element)
                    self.log("Order " + str(element) + " is exceeding quota")
        else:
            for territory_id, order in self.orders.items():
                if territory_id in invalids:
                    continue
                if order["type"] == "build":
                    invalids.append(territory_id)
                    self.log("Player must disband, not build: " + str(territory_id))
                    continue
            needed_disbands = len(self.troops) - len(self.centers)
            build_orders = set([territory_id for territory_id in orders.keys() if orders[territory_id]["type"] == "disband"]) - set(invalids)
            if len(build_orders) > needed_disbands:
                #: remove exceeding orders
                diff = len(build_orders) - needed_disbands
                to_rem = build_orders[:diff]
                for element in to_rem:
                    invalids.append(element)
                    self.log("Order " + str(element) + " is exceeding quota")
        return invalids

    def _validate_retreats(self, orders):
        invalids = []
        previous_phase_movements = []
        for country, previous_orders in self.prev["orders"].items():
            for territory_id, order in previous_orders.items():
                if order["type"] == "move":
                    previous_phase_movements.append(order["to"])
        previous_phase_movements = set(previous_phase_movements)
        for territory_id, order in orders.items():
            if not order.get("to"):
                #: we process retreats only
                if order["type"] != "disband":
                    invalids.append(territory_id)
                continue
            if self._is_fleet(territory_id) and self._is_multi_coast(order["to"]):
                if order.get("mc") not in [0, 1]:
                    invalids.append(territory_id)
                    continue
            if not self._can_move(territory_id, order["to"], order.get("mc")):
                self.log("Order " + str(territory_id) + " is a retreat to a terr cannot move")
                invalids.append(territory_id)
                continue
            # cannot move to a terr where was a move
            if order["to"] in previous_phase_movements:
                invalids.append(territory_id)
                continue
        return invalids

    def _process_diplomacy(self):
        for territory_id, order in self.orders.items():
            ## order should have:
            ##      - id: terr in which the army is
            ##      - type: type of order (should be in
            ##              ["move", "sup_move", "sup_hold", "convoy"])
            ##      - (from): id of terr in which the order starts
            ##      - (to): id of terr in which the order ends (if not hold)
            ##      - (viaConvoy): True if is a move via convoy
            ##      - (mc): id of multi coast to move (if needed)
            if order["type"] != "hold" and not order.get("to"):
                self.invalids.append(territory_id)
                continue
            if order["type"] in ["sup_move", "convoy"]:
                if not order.get("from"):
                    self.invalids.append(territory_id)
                    continue
            ## check basics movements rules
            if order["type"] == "move":
                if not order.get("viaConvoy"):
                    ## mc parameter check
                    if self._is_fleet(territory_id) and self._is_multi_coast(order["to"]):
                        #if not order.get("mc"):
                        #   self.invalids.append(territory_id)
                        #   continue
                        if order.get("mc") not in [0, 1]:
                            self.log("Order "+str(territory_id)+" has a bad mc")
                            self.invalids.append(territory_id)
                            continue
                    else:
                        if order.get("mc"):
                            del order["mc"]
                    ## check move ability
                    mc = None
                    if self._is_fleet(territory_id) and self._is_multi_coast(territory_id):
                        mc = self.mc_pos[territory_id]
                    if not self._can_move(territory_id, order["to"], mc):
                        self.log("Order " + str(territory_id) +
                                 " is a move to a terr cannot move")
                        self.invalids.append(territory_id)
                else:
                    ## cannot convoy fleets
                    if self._is_fleet(territory_id):
                        self.log("Order "+str(territory_id)+" is a fleet convoyed")
                        self.invalids.append(territory_id)
                        continue
                    ## check convoy route present (needed for ui)
                    if not isinstance(order.get("croutes", []), list):
                        self.log("Order " + str(territory_id) +
                                 " is a move viaConvoy without routes")
                        self.invalids.append(territory_id)
                        continue
                    ## check move via convoy ability
                    if order["to"] not in self._convoy_maps(territory_id):
                        self.log("Order " + str(territory_id) +
                                 " is a move viaConvoy to a terr cannot move")
                        self.invalids.append(territory_id)
                    else:
                        ## verify routes (find out orders built without ui)
                        convoy_routes = self._get_convoy_routes(territory_id,
                                                                order["to"])
                        for selected_route in order["croutes"]:
                            if selected_route not in convoy_routes:
                                self.log("Order " + str(territory_id) + " is a " +
                                         "move viaConvoy with invalid route")
                                self.invalids.append(territory_id)
                                continue
                        ## store convoy routes (needed for proc)
                        order["convoy_routes"] = convoy_routes
            elif order["type"] == "sup_move":
                if not self._can_move(territory_id, order["to"]):
                    self.log("Order " + str(territory_id) +
                             " is a sup_move against a terr cannot move")
                    self.invalids.append(territory_id)
                    continue
                ## check if there's an army or ship in to terr
                if self._is_empty_territory(order["from"]):
                    self.log("Order " + str(territory_id) +
                             " is a sup_move to an empty terr")
                    self.invalids.append(territory_id)
            elif order["type"] == "sup_hold":
                if not self._can_move(territory_id, order["to"]):
                    self.log("Order " + str(territory_id) +
                             " is a sup_hold to a terr cannot move")
                    self.invalids.append(territory_id)
                    continue
                ## check if there's an army or ship in to terr
                if self._is_empty_territory(order["to"]):
                    self.log("Order " + str(territory_id) +
                             " is a sup_hold to an empty terr")
                    self.invalids.append(territory_id)
            elif order["type"] == "convoy":
                if not self._is_fleet(territory_id):
                    self.log("Order "+str(territory_id)+" is a convoy by an army")
                    self.invalids.append(territory_id)
            else:
                if order["type"] != "hold":
                    self.log("Order "+str(territory_id)+" is an invalid type")
                    self.invalids.append(territory_id)
                    continue
                if len(order) > 1:
                    order = dict(type="hold")

    @processors.register('builds')
    def process_builds(self, orders):
        return ValidationPipeline(
            self._check_neutrals,
            self._validate_builds).process(orders)

    @processors.register('retreats')
    def process_retreats(self, orders):
        return ValidationPipeline(
            self._check_neutrals,
            self._check_troops,
            self._validate_retreats).process(orders)

    @processors.register('diplomacy')
    def process_diplomacy(self, orders):
        return ValidationPipeline(
            self._check_neutrals,
            self._check_troops,
            self._validate_diplomacy).process(orders)

    def process(self, orders):
        return self.processors.call(self.phase_type, orders)


class PreProcessor(object):
    def __init__(self, orders, logger=None):
        self._logger = logger
        self.orders = orders
        self.fails = []

    def log(self, msg):
        if not self._logger:
            return
        self._logger(msg)

    def _isMoving(self, territory_id):
        for orders_set in self.orders.values():
            for territory_id, order in orders_set.items():
                if territory_id == territory_id and order["type"] == "move":
                    return True
        return False

    def _isMovingTo(self, territory_id, To):
        for orders_set in self.orders.values():
            for territory_id, order in orders_set.items():
                if territory_id == territory_id and order["type"] == "move" and \
                        order["to"] == To:
                    return True
        return False

    def _is_convoyingFT(self, territory_id, fr, to):
        for orders_set in self.orders.values():
            for territory_id, order in orders_set.items():
                if territory_id == territory_id:
                    if order["type"] == "convoy" and order["to"] == to and \
                            order["from"] == fr:
                        return True
                    break
        return False

    def _process_retreats(self):
        fails = []
        retreats = dict()
        for player, orders_set in self.orders.items():
            for territory_id, order in orders_set.items():
                if order["type"] == "retreat":
                    if not retreats.get(order["to"]):
                        retreats[order["to"]] = dict(count=0, data=[])
                    retreats[order["to"]]["count"] += 1
                    retreats[order["to"]]["data"].append((player, territory_id))
        for retreat in retreats.values():
            if retreat["count"] > 1:
                ## fails all
                for el in retreat["data"]:
                    fails.append(el)
        return fails

    def _process_diplomacy(self):
        for player, orders_set in self.orders.items():
            for territory_id, order in orders_set.items():
                #territory_id = player+":"+order["id"]
                if order["type"] == "sup_hold":
                    ## support hold to moving units fails
                    if self._isMoving(order["to"]):
                        self.fails.append((player, territory_id))
                elif order["type"] == "sup_move":
                    ## support move to unit not moving or moving to another
                    ## terr fails
                    if not self._isMoving(order["from"]):
                        self.fails.append((player, territory_id))
                        continue
                    if not self._isMovingTo(order["from"], order["to"]):
                        self.fails.append((player, territory_id))
                elif order["type"] == "convoy":
                    ## convoy unit which is not moving or moving to another
                    ## terr fails
                    if not self._isMovingTo(order["from"], order["to"]):
                        self.fails.append((player, territory_id))
                        continue
                    #: is the army moving viaConvoy?
                    for otherp, otherordersset in self.orders.items():
                        otherfound = False
                        for otheroid, otherorder in otherordersset.items():
                            if otheroid == order["from"]:
                                if not otherorder.get("viaConvoy"):
                                    self.fails.append((player, territory_id))
                                otherfound = True
                                break
                        if otherfound:
                            break
                ## add check for convoy route (move + viaConvoy)
                elif order["type"] == "move":
                    if order.get("viaConvoy"):
                        bad_routes = []
                        succ = False
                        for route in order["convoy_routes"]:
                            route_succ = True
                            for fleet in route:
                                if not self._is_convoyingFT(fleet, territory_id,
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
                            self.fails.append((player, territory_id))
                        else:
                            for route in bad_routes:
                                order["convoy_routes"].remove(route)

    def process(self, phase):
        if phase == "retreats":
            ## we have to verify conflicts (retreats to same terrs fails both)
            self._process_retreats()
        else:
            self._process_diplomacy()
