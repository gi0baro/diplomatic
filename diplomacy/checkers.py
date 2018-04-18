# -*- coding: utf-8 -*-

from collections import defaultdict
from .constants import PHASES, ORDERS
from .helpers import registry


class ValidationPipeline(object):
    def __init__(self, *methods):
        self.methods = methods

    @staticmethod
    def _get_pipe_orders(orders, invalid):
        return {key: orders[key] for key in set(orders.keys()) - set(invalid)}

    def process(self, orders):
        rv = []
        for method in self.methods:
            rv.extend(method(self._get_pipe_orders(orders, rv)))
        return rv


class Validator(object):
    pipelines = registry()

    def __init__(
        self, map_data, allowed_supply_centers, phase_type, armies, fleets, multi_coasts_positions, player_troops,
        player_territories, previous_orders=[], logger=None
    ):
        self._logger = logger
        self._load_map(map_data)
        self.allowed_supply_centers = allowed_supply_centers
        self.armies = armies
        self.fleets = fleets
        self.multi_coasts_positions = multi_coasts_positions
        self.phase_type = phase_type
        self.troops = player_troops
        self._logger(self.troops)
        self.territories = player_territories
        self.overcome_supply_centers = set(self.all_supply_centers) & set(self.territories)
        self.available_supply_centers = set(self.allowed_supply_centers) & set(self.territories)
        self.previous_orders = previous_orders
        self.__convoy_maps = {}
        self._convoy_routes = defaultdict(lambda: list())
        self._convoy_routes_stacks = []

    def _load_map(self, data):
        self.seas = data['seas']
        self.coasts = data['coasts']
        self.neutrals = data['neutrals']
        self.multi_coasts = list(data['multi_coasts'].keys())
        self.all_supply_centers = data['supply_centers']
        self.links = data['links']

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
        return territory_id in self.multi_coasts

    # def _is_convoying(self, territory_id):
    #     return self.orders.get(territory_id, {}).get('type') == ORDERS.CONVOY

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

    def _check_neutrals(self, orders):
        invalids = []
        for territory_id, order in orders.items():
            if territory_id in self.neutrals:
                invalids.append(territory_id)
                self.log("Order " + str(territory_id) + " is made on neutral state")
                continue
            if order.get('src') in self.neutrals:
                invalids.append(territory_id)
                self.log("Order " + str(territory_id) + " is to a neutral state")
                continue
            if order.get('dst') in self.neutrals:
                invalids.append(territory_id)
                self.log("Order " + str(territory_id) + " has 'src' set to a " + "neutral state")
        return invalids

    def _check_troops(self, orders):
        invalids = []
        #: check order is on player's armies
        for territory_id in set(orders.keys()) - set(self.troops):
            invalids.append(territory_id)
            self.log("Order " + str(territory_id) + " is not in player troops")
        return invalids

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
            if order.get("type") not in {ORDERS.HOLD, ORDERS.BUILD, ORDERS.DISBAND}:
                invalids.append(territory_id)
                continue
            if order["type"] == ORDERS.BUILD and not order.get("troop"):
                invalids.append(territory_id)
                continue
            #: check build order has not a troop and disband viceversa
            if order["type"] == ORDERS.BUILD:
                if territory_id in self.troops:
                    invalids.append(territory_id)
                    continue
                if territory_id not in self.available_supply_centers:
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " is not in player supply")
                    continue
                #: verified with above
                # if territory_id not in self.territories:
                #     invalids.append(territory_id)
                #     self.log("Order " + str(territory_id) + " is not in player terrs")
                #     continue
            elif order["type"] == ORDERS.DISBAND:
                if territory_id not in self.troops:
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " is not in player troops")
                    continue
            #: check build of fleets is only on coasts supply centers
            if order["type"] == ORDERS.BUILD and order["troop"] == "fleet":
                #: need to check is a coast!
                if not self._is_coast(territory_id):
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " is not on a coast")
                    continue
                if self._is_multi_coast(territory_id) and order.get("mc") is None:
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " has no mc parameter")
        #: process builds considering country details
        if len(self.overcome_supply_centers) > len(self.troops):
            for territory_id, order in orders.items():
                if territory_id in invalids:
                    continue
                if territory_id not in self.available_supply_centers:
                    invalids.append(territory_id)
                    self.log("Order " + str(territory_id) + " is not in player supply")
                    continue
                if order["type"] == ORDERS.DISBAND:
                    invalids.append(territory_id)
                    self.log("Player must build, not disband: " + str(territory_id))
                    continue
            allowed_builds_no = len(self.overcome_supply_centers) - len(self.troops)
            build_orders = set([
                territory_id for territory_id in orders.keys() if orders[territory_id]["type"] == ORDERS.BUILD
            ]) - set(invalids)
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
                if order["type"] == ORDERS.BUILD:
                    invalids.append(territory_id)
                    self.log("Player must disband, not build: " + str(territory_id))
                    continue
            needed_disbands = len(self.troops) - len(self.overcome_supply_centers)
            build_orders = set([
                territory_id for territory_id in orders.keys() if orders[territory_id]["type"] == ORDERS.DISBAND
            ]) - set(invalids)
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
        for country, previous_orders in self.previous_orders.items():
            for territory_id, order in previous_orders.items():
                if order["type"] == ORDERS.MOVE:
                    previous_phase_movements.append(order['dst'])
        previous_phase_movements = set(previous_phase_movements)
        for territory_id, order in orders.items():
            if not order.get('dst'):
                #: we process retreats only
                if order["type"] != ORDERS.DISBAND:
                    invalids.append(territory_id)
                continue
            if self._is_fleet(territory_id) and self._is_multi_coast(order['dst']):
                if order.get("mc") not in [0, 1]:
                    invalids.append(territory_id)
                    continue
            if not self._can_move(territory_id, order['dst'], order.get("mc")):
                self.log("Order " + str(territory_id) + " is a retreat to a terr cannot move")
                invalids.append(territory_id)
                continue
            # cannot move to a terr where was a move
            if order['dst'] in previous_phase_movements:
                invalids.append(territory_id)
                continue
        return invalids

    def _validate_diplomacy(self, orders):
        #: orders should have:
        #   - id: territory where the army is located
        #   - type: type of order (ORDERS.MOVE, ORDERS.SUPPORT_MOVE, ORDERS.SUPPORT_HOLD, ORDERS.CONVOY)
        #   - (from): territory from where the order starts
        #   - (to): territory where the order ends (if not hold)
        #   - (through): True if movement is via convoy
        #   - (mc): coast to move in case of multiple coasts
        invalids = []
        for territory_id, order in orders.items():
            self._logger(order)
            if order["type"] != ORDERS.HOLD and not order.get('dst'):
                invalids.append(territory_id)
                continue
            if order["type"] in [ORDERS.SUPPORT_MOVE, ORDERS.CONVOY]:
                if not order.get('src'):
                    invalids.append(territory_id)
                    continue
            #: check basics movements rules
            if order["type"] == ORDERS.MOVE:
                if not order.get("through"):
                    #: mc parameter check
                    if self._is_fleet(territory_id) and self._is_multi_coast(order['dst']):
                        if order.get("mc") not in [0, 1]:
                            self.log("Order " + str(territory_id) + " has a bad mc")
                            invalids.append(territory_id)
                            continue
                    else:
                        if order.get("mc"):
                            del order["mc"]
                    #: check move ability
                    mc = None
                    if self._is_fleet(territory_id) and self._is_multi_coast(territory_id):
                        mc = self.multi_coasts_positions[territory_id]
                    if not self._can_move(territory_id, order['dst'], mc):
                        self.log("Order " + str(territory_id) +
                                 " is a move to a terr cannot move")
                        invalids.append(territory_id)
                else:
                    #: cannot convoy fleets
                    if self._is_fleet(territory_id):
                        self.log("Order " + str(territory_id) + " is a fleet convoyed")
                        invalids.append(territory_id)
                        continue
                    #: check convoy route present (needed for ui)
                    if not isinstance(order.get("croutes", []), list):
                        self.log("Order " + str(territory_id) + " is a move through without routes")
                        invalids.append(territory_id)
                        continue
                    #: check move via convoy ability
                    if order['dst'] not in self._convoy_maps(territory_id):
                        self.log("Order " + str(territory_id) + " is a move through to a terr cannot move")
                        invalids.append(territory_id)
                    else:
                        #: verify routes (find out orders built without ui)
                        convoy_routes = self._get_convoy_routes(territory_id, order['dst'])
                        for selected_route in order["convoy_routes"]:
                            if selected_route not in convoy_routes:
                                self.log("Order " + str(territory_id) + " is a move through with invalid route")
                                invalids.append(territory_id)
                                continue
                        #: store convoy routes (needed for processor)
                        order["convoy_routes"] = convoy_routes
            elif order["type"] == ORDERS.SUPPORT_MOVE:
                if not self._can_move(territory_id, order['dst']):
                    self.log("Order " + str(territory_id) + " is a support_move against a terr cannot move")
                    invalids.append(territory_id)
                    continue
                #: check if there's an army or ship in to terr
                if self._is_empty_territory(order['src']):
                    self.log("Order " + str(territory_id) + " is a support_move to an empty terr")
                    invalids.append(territory_id)
            elif order["type"] == ORDERS.SUPPORT_HOLD:
                if not self._can_move(territory_id, order['dst']):
                    self.log("Order " + str(territory_id) + " is a support_hold to a terr cannot move")
                    invalids.append(territory_id)
                    continue
                #: check if there's something to support
                if self._is_empty_territory(order['dst']):
                    self.log("Order " + str(territory_id) + " is a support_hold to an empty terr")
                    invalids.append(territory_id)
            elif order["type"] == ORDERS.CONVOY:
                if not self._is_fleet(territory_id):
                    self.log("Order " + str(territory_id) + " is a convoy by an army")
                    invalids.append(territory_id)
            else:
                if order["type"] != ORDERS.HOLD:
                    self.log("Order " + str(territory_id) + " is an invalid type")
                    invalids.append(territory_id)
                    continue
                if len(order) > 1:
                    order = dict(type=ORDERS.HOLD)
        return invalids

    @pipelines.register(PHASES.BUILDS)
    def process_builds(self, orders):
        return ValidationPipeline(
            self._check_neutrals,
            self._validate_builds).process(orders)

    @pipelines.register(PHASES.RETREATS)
    def process_retreats(self, orders):
        return ValidationPipeline(
            self._check_neutrals,
            self._check_troops,
            self._validate_retreats).process(orders)

    @pipelines.register(PHASES.DIPLOMACY)
    def process_diplomacy(self, orders):
        return ValidationPipeline(
            self._check_neutrals,
            self._check_troops,
            self._validate_diplomacy).process(orders)

    def process(self, orders):
        return self.pipelines.call(self.phase_type, self, orders)


class PreProcessor(object):
    pipelines = registry()

    def __init__(self, phase_orders, logger=lambda *args: None):
        self.orders = phase_orders
        self._logger = logger

    def log(self, *msg):
        # self._logger(msg)
        print(msg)

    def _is_moving(self, territory_id):
        for orders_set in self.orders.values():
            if orders_set.get(territory_id, {}).get('type') == 'move':
                return True
        return False

    def _is_moving_to(self, territory_id, dst):
        for orders_set in self.orders.values():
            order = orders_set.get(territory_id, {})
            if order.get('type') == 'move' and order.get('dst') == dst:
                return True
        return False

    def _is_convoying_between(self, territory_id, src, dst):
        for orders_set in self.orders.values():
            order = orders_set.get(territory_id, {})
            if order.get('type') == 'convoy' and order.get('src') == src and order.get('dst') == dst:
                return True
        return False

    @pipelines.register(PHASES.RETREATS)
    def _process_retreats(self):
        failed = []
        retreats = dict()
        for player, orders_set in self.orders.items():
            for territory_id, order in orders_set.items():
                if order["type"] == "retreat":
                    if not retreats.get(order['dst']):
                        retreats[order['dst']] = dict(count=0, data=[])
                    retreats[order['dst']]["count"] += 1
                    retreats[order['dst']]["data"].append((player, territory_id))
        for retreat in retreats.values():
            if retreat["count"] > 1:
                #: fail all
                for el in retreat["data"]:
                    failed.append(el)
        return failed

    @pipelines.register(PHASES.DIPLOMACY)
    def _process_diplomacy(self):
        failed = []
        for player, orders_set in self.orders.items():
            for territory_id, order in orders_set.items():
                if order["type"] == ORDERS.SUPPORT_HOLD:
                    #: support holding moving units fails
                    if self._is_moving(order['dst']):
                        self.log(territory_id, 'other is moving', order['dst'])
                        failed.append((player, territory_id))
                elif order["type"] == ORDERS.SUPPORT_MOVE:
                    #: support moving not moving units fails
                    if not self._is_moving(order['src']):
                        self.log(territory_id, 'not_moving', order['src'])
                        failed.append((player, territory_id))
                        continue
                    #: support moving units moving to different territories fails
                    if not self._is_moving_to(order['src'], order['dst']):
                        self.log(order['src'], 'not_moving to', order['dst'])
                        failed.append((player, territory_id))
                elif order["type"] == ORDERS.CONVOY:
                    #: convoying unit not moving or moving to another territory fails
                    if not self._is_moving_to(order['src'], order['dst']):
                        self.log(order['src'], 'convoy not_moving to', order['dst'])
                        failed.append((player, territory_id))
                        continue
                    #: is the army moving trough a convoy?
                    for other_player, other_orders_set in self.orders.items():
                        other_order = other_orders_set.get(order['src'], {})
                        if other_order:
                            if not other_order.get("through"):
                                self.log(territory_id, 'other order not moving through convoy')
                                failed.append((player, territory_id))
                            break
                ## add check for convoy route (move + through)
                elif order["type"] == ORDERS.MOVE:
                    if order.get("through"):
                        bad_routes = []
                        succeeded = False
                        for route in order["convoy_routes"]:
                            route_succeeded = True
                            for fleet in route:
                                if not self._is_convoying_between(fleet, territory_id, order['dst']):
                                    route_succeeded = False
                                    break
                            if route_succeeded:
                                #: we need to process every route
                                succeeded = True
                            else:
                                #: we have to remove the route from list
                                bad_routes.append(route)
                        if not succeeded:
                            self.log(territory_id, 'convoy failure')
                            failed.append((player, territory_id))
                        else:
                            for route in bad_routes:
                                order["convoy_routes"].remove(route)
        self.log('ZIOCAN')
        return failed

    def process(self, phase_type):
        return self.pipelines.call(phase_type, self)
