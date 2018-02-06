# -*- coding: utf-8 -*-


class cachedprop(object):
    pass


class World(object):
    def __init__(self, judge):
        self.judge = judge
        self.nodes = {}
        #: map types
        self._nodes_cls = {
            'hold': Hold,
            'move': Move,
            'move_through': MoveThrough,
            'support_move': SupportMove,
            'support_hold': SupportHold,
            'convoy': Convoy
        }
        self._nodes_by_type = {v: [] for v in self._nodes_cls.values()}
        self._nodes_mapper = {}
        for key in self._nodes_cls.keys():
            self._nodes_mapper[key] = lambda data: self._nodes_cls[key]
        self._nodes_mapper['move'] = lambda data: (
            self._nodes_cls['move_through'] if data.get('viaConvoy')
            else self._nodes_cls['move'])
        #: map dependencies
        self._dependency_cls = {
            'attackers': [Move, MoveThrough],
            'defenders': [SupportHold],
            'supporters': [SupportMove]
        }
        self._dependency_compare_attrs = {
            'attackers': 'dst',
            'defenders': 'dst',
            'supporters': 'src'
        }

    def __getattr__(self, name):
        return self.get(name)

    def get(self, node_id):
        return self.nodes.get(node_id)

    @property
    def ids(self):
        return self.nodes.keys()

    @property
    def list(self):
        return self.nodes.values()

    def create_node(self, node_id, data):
        node_cls = self._nodes_mapper[data['type']](data)
        self.nodes[node_id] = node_cls(self, node_id, data)
        self._nodes_by_type[node_cls].append(self.nodes[node_id])

    def get_dependencies(self, node_id, dependency_type):
        rv = []
        for node_cls in self._dependency_cls[dependency_type]:
            for node in self._nodes_by_type[node_cls]:
                if (
                    getattr(
                        node, self._dependency_compare_attrs[dependency_type]
                    ) == node_id
                ):
                    rv.append(node)
        return rv

    def get_attackers(self, node_id):
        return self.get_dependencies(node_id, "attackers")

    def get_defenders(self, node_id):
        return self.get_dependencies(node_id, "defenders")

    def get_supporters(self, node_id):
        rv = self.get_dependencies(node_id, "supporters")
        #: support move to different terr removal
        nrem = []
        for node in rv:
            if node.to != self.get(node_id).to:
                nrem.append(node)
        return list(set(rv) - set(nrem))

    def get_convoyers(self, routes):
        rv = []
        for elements in routes:
            rv.append([self.get(node_id) for node_id in elements])
        return rv

    def log(self, msg, indent=0):
        self.judge._logstack.append(" " * 2 * indent + msg)


class Node(object):
    def __init__(self, world, node_id, data):
        self.world = world
        self.id = node_id
        self.country = data.get("country")
        ## TEMP, remove next var in productioN!!!
        self.name = data.get("name")
        ##
        # self.type = self.__class__.__name__
        self.src = data.get("from")
        self.dst = data.get("to")
        self.failed = data.get("failed") or False
        self.init()

    def init(self):
        pass

    @property
    def type(self):
        return self.__class__

    def _get_dependencies(self):
        return []

    @cachedprop
    def dependencies(self):
        return self._get_dependencies()

    def remove_dependency(self, dep=None):
        if not dep:
            self.dependencies.pop(0)
        else:
            self.dependencies.remove(dep)

    def remove_all_dependencies(self):
        self.dependencies.clear()

    @property
    def depends_on(self):
        return self.dependencies[0] if self.dependencies else None

    @property
    def solved(self):
        if self.failed:
            return True
        return False if self.depends_on else True

    def compute_success(self):
        return None

    @property
    def succeeded(self):
        if self.failed:
            return False
        return self.compute_success()

    def __repr__(self):
        return '<Node %(country)s - %(id)s: %(name)s>' % dict(
            id=self.id, country=self.country, name=self.name)

    def log(self, *args, **kwargs):
        self.world.log(*args, **kwargs)


class Hold(Node):
    def init(self):
        self.dislodged_status = None

    def _get_dependencies(self):
        return self.defenders + self.attackers

    @cachedprop
    def attackers(self):
        return self.world.get_attackers(self.id)

    @property
    def defenders(self):
        return self.world.get_defenders(self.id)

    @property
    def strength_defense(self):
        strength = (1, 1)
        for node in self.defenders:
            addmin, addmax = 0, 0
            if node.solved:
                if node.succeeded:
                    addmin += 1
                    addmax += 1
            else:
                addmax += 1
            strength = (strength[0] + addmin, strength[1] + addmax)
        return strength

    def resolve(self):
        #: we just need 1 successful attack with strength > 1 to solve this
        dependencies = list(self.dependencies)
        for node in dependencies:
            self.log("Hold: solving {}".format(node), indent=1)
            if node in self.defenders:
                if node.attacked_status is not None:
                    self.remove_dependency(node)
            else:
                self.dislodged_status = self.compute_dislodgement(node)
                if self.dislodged_status is not None:
                    if self.dislodged_status:
                        self.remove_all_dependencies()
                        break
                    self.remove_dependency(node)

    def compute_dislodgement(self, versus=None):
        versus = versus or self.depends_on
        if not versus or versus.type not in [Move, MoveThrough]:
            return False
        if versus.solved:
            self.log("Dependency is solved for {}".format(versus), indent=2)
            if versus.succeeded:
                self.log(
                    "-> Other army " + str(versus) +
                    " is succesful moving to me. I'm dislodged.", indent=2)
                return True
            self.log(
                "-> Other army " + str(versus) +
                " fail moving to me. I'm not dislodged.", indent=2)
            return False
        self.log("Dependency is not solved for {}".format(versus), indent=2)
        return None

    def compute_success(self):
        if self.dislodged_status is not None:
            return not self.dislodged_status
        return not self.compute_dislodgement()

    @property
    def is_unit_dislodged(self):
        if self.type == Hold:
            return not self.succeeded
        for node in self.attackers:
            if node.succeeded:
                return True
        return False


class Move(Hold):
    def init(self):
        super().init()
        self.success_status = None

    def _get_dependencies(self):
        holder = []
        if not self.has_empty_dst:
            holder.append(self.holder)
            attackers_others = list(self.holder.attackers)
        ## note: cannot use world.get in next line because self.dst can be empty
        else:
            attackers_others = self.world.get_attackers(self.dst)
        ### TO IMPROVE: removing myself
        if self in attackers_others:
            attackers_others.remove(self)
        return self.supporters + holder + attackers_others

    @cachedprop
    def holder(self):
        return self.world.get(self.dst)

    @cachedprop
    def supporters(self):
        return self.world.get_supporters(self.id)

    def _strength_attack(self, countrycheck=True):
        strength = (1, 1)
        vs = self.world.get(self.dst)
        country = vs.country if vs else None
        for node in self.supporters:
            skip_node = False
            if countrycheck:
                skip_node = True if node.country == country else False
            if skip_node:
                continue
            addmin, addmax = 0, 0
            if node.solved:
                if node.succeeded:
                    addmin += 1
                    addmax += 1
            else:
                addmax += 1
            strength = (strength[0] + addmin, strength[1] + addmax)
        return strength

    @property
    def strength_attack(self):
        return self._strength_attack()

    @property
    def strength_attack_ss(self):
        return self.strength_attack(False)

    @property
    def has_empty_dst(self):
        return self.holder is None

    @property
    def holder_is_moving(self):
        if self.has_empty_dst:
            return False
        return self.holder.type in [Move, MoveThrough]

    @property
    def is_swapping(self):
        if (
            self.holder_is_moving and
            self.holder.dst == self.id and self.dst == self.holder.id and
            MoveThrough in [self.type, self.holder.type]
        ):
            return True
        return False

    def compare_numerically(self, versus, vCompare, sCompare, swap=False):
        self.log("comparing: mine {} - vs {}".format(sCompare, vCompare), indent=2)
        s_attr_min, s_attr_max = getattr(self, sCompare)
        v_attr_min, v_attr_max = getattr(versus, vCompare)
        self.log(
            "comparing values: {}, {} - {}, {}".format(
                s_attr_min, s_attr_max, v_attr_min, v_attr_max), indent=2)
        ## we try to rapidly solve checking two easy cases:
        ## 1) my min stregth > versus max strength: I'm winning on this
        ## dependency and the versus is failed
        if s_attr_min > v_attr_max:
            self.log("-> min att > max comparing: solved", indent=3)
            ## we had to check self dislodgement tries of me or versus player
            return True
        ## 2) my max strength <= versus min strength: I'm loosing at all.
        if s_attr_max <= v_attr_min:
            if vCompare in ["strength_att", "strength_ssa"]:
                ## my max att < versus min att
                if s_attr_max < v_attr_min:
                    ## convoyed unit exception
                    if versus.type == MoveThrough and self.type != MoveThrough:
                        if not versus.solved:
                            self.log(
                                "\t\t\t-> max att < min comparing, but vs " +
                                "army is convoyed: waiting for more details..")
                            return None
                        #else:
                        #   if not versus.succeeded:
                        #       return True
                    self.log("\t\t\t-> max att < min comparing: solved")
                    return False
                ## my max att = versus min att
                if s_attr_max == v_attr_min:
                    ## convoyed unit exception
                    if versus.type == MoveThrough and self.type != MoveThrough:
                        if not versus.solved:
                            self.log(
                                "\t\t\t-> att is the same but vs army is " +
                                "convoyed: waiting for more details..")
                            return None
                        #else:
                        #   return not versus.succeeded
                    self.log("\t\t\t-> att is the same: solved")
                    ## same attack strength
                    return False
                self.log("\t\t\t-> numeric compare unsolved (1)")
                return None
            else:
                ## if we have a convoy swap we treat it quite differently:
                if swap:
                    if versus.solved and not versus.succeeded:
                        self.log(
                            "\t\t\t-> swap: other army failed, me failing too")
                        return False
                    self.log(
                        "\t\t\t-> swap: att is same of defense, solved as " +
                        "succeded")
                    return True
            self.log("\t\t\t-> max att <= min comparing: solved")
            return False
        self.log("\t\t\t-> numeric compare unsolved")
        return None

    def compare_attacks(self, versus):
        ## we need to compare attack power, so we need to count supporters
        move = False
        if versus.type in [Move, MoveThrough]:
            vCompare = "strength_attack"
            move = True
        else:
            vCompare = "strength_defense"
        if not move:
            ## the other unit is not moving (hold or support)
            self.log("\t\t-> other unit is not moving..")
            return self.compare_numerically(versus, vCompare, "strength_attack")
        elif move and versus.dst == self.id:
            ## the other unit is moving to me
            self.log("\t\t-> other unit is moving to me..")
            if versus == self.holder and self.is_swapping:
                self.log("\t\t -> units are swapping..")
                vCompare = "strength_defense"
                return self.compare_numerically(
                    versus, vCompare, "strength_attack", True)
            return self.compare_numerically(versus, vCompare, "strength_attack")
        elif move and versus.dst == self.dst:
            ## the other unit is moving to the same terr I'm moving to
            self.log("\t\t-> other unit is moving to same terr..")
            ## if one of the other attackers is in 1vs1 with my holder,
            ## I had to check more stuffs
            if versus != self.holder:
                if self.holder_is_moving:
                    if self.holder.dst == versus.id:
                        self.log(
                            "\t\t-> other unit is in 1on1 with my holder..")
                        ## I need to know if holder have succeded in the move
                        if self.holder.solved:
                            if (
                                self.holder.succeeded and not
                                self.holder.is_swapping
                            ):
                                self.log(
                                    "\t\t\t-> Other unit is loosing: has no " +
                                    "power against me.")
                                ## if so, I won't consider the versus because
                                ## has no strength
                                return True
                            ## else fall back to compare_num
                        else:
                            self.log(
                                "\t\t\t-> I need more information about " +
                                "this, dependency unsolved.")
                            return None
            sCompare = "strength_attack"
            ## additional considerations for units swap
            if self.holder_is_moving:
                self.log("\t\t-> Holder is moving..")
                if self.strength_attack != self.strength_attack_ss:
                    self.log("\t\t-> my s_att != s_ssa..")
                    if self.holder.solved:
                        self.log("\t\t\t-> Holder move is solved, continue..")
                        if self.holder.succeeded:
                            sCompare = "strength_attack_ss"
                        else:
                            sCompare = "strength_attack"
                    else:
                        self.log(
                            "\t\t\t-> Holder move is unsolved, breaking..")
                        return None
                if versus.strength_attack != versus.strength_attack_ss:
                    self.log("\t\t-> versus s_att != s_ssa..")
                    vCompare = "strength_attack_ss"
            return self.compare_numerically(versus, vCompare, sCompare)
        else:
            ## the other unit is moving to another terr
            self.log("\t\t-> other unit is moving to another terr..")
            if versus.solved:
                if versus.succeeded:
                    self.log("\t\t\t-> other unit moved, dependency solved.")
                    return True
                return self.compare_numerically(
                    versus, "strength_defense", "strength_attack")
            self.log(
                "\t\t\t-> no information on other unit, dependency unsolved.")
            return None

    def resolve(self):
        compare_stack = []
        check_stack = self.success_status is None
        dependencies = list(self.dependencies)
        for node in dependencies:
            self.log("Move: comparing dependency {}".format(node), indent=1)
            if node in self.supporters:
                self.log("dependency is a supporter", indent=2)
                if node.solved:
                    self.remove_dependency(node)
                    self.log(
                        "dependency is solved for {}".format(node), indent=2)
            else:
                ## get success on the single dependency
                success = self.compare_attacks(node)
                if success is not False:
                    ## store in the compare stack, as we need to check every
                    ## dependency is won to move
                    compare_stack.append(success)
                if success is not None:
                    if not success:
                        ## we ended, there's someone powerful than me
                        self.log("Move: movement failed.", indent=1)
                        self.success_status = False
                        for dep in (
                            set(list(self.dependencies)) - set(self.supporters)
                        ):
                            self.remove_dependency(dep)
                        check_stack = False
                        break
                    else:
                        ## I've solved this dependency
                        self.remove_dependency(node)
        ## check for winner on every dependency (if solved all)
        if check_stack:
            winner = True
            for success in compare_stack:
                winner = True
                if success is None:
                    ## we need further investigations
                    winner = False
                    break
            if winner:
                self.log("Move: movement succeeded.", indent=1)
                self.success_status = True
                self.remove_all_dependencies()

    def force_resolution(self, val=True):
        self.log("Move: forcing moving {}".format(self), indent=1)
        self.success_status = val
        self.remove_all_dependencies()

    def compute_success(self):
        if self.success_status is None:
            self.resolve()
        return self.success_status


class MoveThrough(Move):
    def init(self):
        super().init()
        self.convoy_status = None

    def set_routes(self, routes):
        self._convoy_routes = routes

    @cachedprop
    def convoyers(self):
        return self.world.get_convoyers(self._convoy_routes)

    def _get_dependencies(self):
        move_deps = super()._get_dependencies()
        deps = []
        for route in self.convoyers:
            avoid_set = set(deps) & set(route)
            for node in route:
                if node in avoid_set:
                    continue
                deps.append(node)
        return deps + move_deps

    @property
    def strength_attack(self):
        if self.convoyed is False:
            return (0, 0)
        return self.strength_attack()

    @property
    def strength_attack_ss(self):
        if self.convoyed is False:
            return (0, 0)
        return self.strength_attack(False)

    def resolve(self):
        ## we need succesful convoy and then sove with Move class
        dep_rem = []
        move_check = False
        failed_routes = []
        for route in self.convoyers:
            self.log(
                "MoveViaConvoy: Processing route {}".format(route), indent=1)
            succeeded_convoyers = 0
            conv_rem = []
            ## convoyers check in the route
            for convoyer in route:
                self.log("Processing convoyer {}".format(convoyer), indent=2)
                convoyed = self._solve_convoyer(convoyer)
                if convoyed is not None:
                    ## solved node, add dependency to remove list
                    conv_rem.append(convoyer)
                    if not convoyed:
                        ## fail the route and break the cycle
                        failed_routes.append(route)
                        break
                    else:
                        ## append node to success stack
                        succeeded_convoyers += 1
            ## if the success stack len is the same as the route, the convoy
            ## chain is successful
            if succeeded_convoyers == len(route):
                ## IS IT ENOUGH? I THINK SO; I DON'T CONSIDER OTHER ROUTES
                for route in self.convoyers:
                    for node in route:
                        dep_rem.append(node)
                ## proceeed to the normal moves solving
                self.log("MoveViaConvoy: route succeeded", indent=1)
                move_check = True
                break
            ## else we just remove solved dependencies
            else:
                for node in conv_rem:
                    dep_rem.append(node)
        for node in set(dep_rem) & set(self.dependencies):
            self.remove_dependency(node)
        if not move_check:
            ## verify that all routes have failed
            if failed_routes == self.convoyers:
                ## the movement is failing, removing all deps
                self.log("MoveViaConvoy: all convoy routes failed.", indent=1)
                self.convoy_status = False
                self.success_status = False
                self.remove_all_dependencies()
            else:
                self.log("MoveViaConvoy: convoy routes not solved..", indent=1)
                for route in failed_routes:
                    self.convoyers.remove(route)
        else:
            ## normal movement solve
            self.convoy_status = True
            self.log(
                "MoveViaConvoy: starting normal movement solving..", indent=1)
            super().resolve(self)

    def _solve_convoyer(self, convoyer):
        if not (convoyer.type == Convoy and convoyer.src == self.id):
            return False
        if convoyer.dislodged_status:
            return False
        if convoyer.solved:
            if convoyer.succeeded:
                return True
            return False
        return None

    @property
    def convoyed(self):
        if self.convoy_status is None:
            self.resolve()
        return self.convoy_status


class Convoy(Hold):
    def _force_resolution(self):
        compare_stack = []
        dependencies = list(self.dependencies)
        for node in dependencies:
            self.log("Convoy: force solving {}".format(node), indent=1)
            self._versus = node
            vs_attack_strength = self.get_fake_dislodgement(node)
            if vs_attack_strength is not None:
                self.remove_dependency(node)
                compare_stack.append(vs_attack_strength)
            else:
                self.log(
                    "Convoy: cannot force solve node {}".format(node),
                    indent=1)
        max_attack_strength = max(compare_stack)
        max_count = 0
        for attack_strength in compare_stack:
            if attack_strength == max_attack_strength:
                max_count += 1
        if max_count == 1 and max_attack_strength > 1:
            self.dislodged_status = True
            self.remove_all_dependencies()
        else:
            self.dislodged_status = False

    def get_fake_dislodgement(self, by=None):
        if not by:
            by = self.depends_on
        if by.type == Move:
            return by.strength_attack[1]
        return None

    def force_resolution(self):
        self.log("Convoy: force solving {}".format(self), indent=1)
        for node in set(self.dependencies) - set(self.defenders):
            self.remove_dependency(node)
        self.dislodged_status = True


class Support(Hold):
    def init(self):
        super().init()
        self.attacked_status = None

    #def solve(self):
        ## we just need 1 attack to have this solved
        dep_rem = []
        attackers = [k for k in self.attackers if k in self.dependencies]
        failed_attacks = 0
        for node in attackers:
            self.log("Support: solving dependency {}".format(node), indent=1)
            attacked_status = self.is_attacked(node)
            if attacked_status is not None:
                if attacked_status:
                    self.attacked_status = True
                    self.log("Support: I'm attacked. Support failed.", indent=1)
                    dep_rem = attackers
                    break
                else:
                    self.log("Support: attacker failed, still supporting.", indent=1)
                    failed_attacks += 1
                self.remove_dependency(node)
            else:
                self.log("Support: dependency {} unsolved.".format(node), indent=1)
        for node in set(dep_rem) & set(self.dependencies):
            self.remove_dependency(node)
        if failed_attacks == len(self.attackers):
            self.attacked_status = False
        #: proc defenders!
        Hold.resolve(self)

    @property
    def success(self):
        if self.attacked_status is not None:
            return not self.attacked_status
        return not self.is_attacked()


class SupportMove(Support):
    def is_attacked(self, versus=None):
        if not versus:
            versus = self.depends_on
        if not versus:
            return False
        ## the army I'm supporting against cannot cut my support
        if versus.id == self.dst:
            ## only if the army have stregth 1
            if self.world.get(self.dst).strength_attack[1] == 1:
                return False
            ## or is not a dislodge case
            disl = self.compute_dislodgement(versus)
            return disl
        ## an army of my country cannot cut my support
        if versus.country == self.country:
            return False
        if versus.type == MoveThrough:
            if versus.solved:
                if versus.convoyed:
                    return True
                return False
            return None
        return True


class SupportHold(Support):
    def is_attacked(self, versus=None):
        ## load a defined versus or first dependency
        if not versus:
            versus = self.depends_on
        if not versus:
            return False
        ## if move is via convoy we should check if succeeded
        if versus.type == MoveThrough:
            ## if not solved we should process it
            if versus.solved:
                ## return the result of the movement,
                ## a faied move via convoy should not cut the support
                if versus.convoyed:
                    return True
                return False
            return None
        ## if move is not via convoy the support is cut
        return True
