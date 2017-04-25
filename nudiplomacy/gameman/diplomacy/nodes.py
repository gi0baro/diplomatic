# -*- coding: utf-8 -*-


class Nodes(object):
    def __init__(self, adjudicator):
        self._adj = adjudicator
        self._nodes = dict()

    def __getattr__(self, name):
        # if not hasattr(self, name):
        return self.get(name)
        # return object.__getattribute__(self, name)

    def new(self, oid, data):
        if data["type"] == "move":
            if data.get("viaConvoy"):
                self._nodes[oid] = MoveConv(self, oid, data)
            else:
                self._nodes[oid] = Move(self, oid, data)
        elif data["type"] == "sup_move":
            self._nodes[oid] = SupportM(self, oid, data)
        elif data["type"] == "sup_hold":
            self._nodes[oid] = SupportH(self, oid, data)
        elif data["type"] == "convoy":
            self._nodes[oid] = Convoy(self, oid, data)
        else:
            self._nodes[oid] = Hold(self, oid, data)

    def get(self, oid):
        return self._nodes.get(oid, None)

    @property
    def ids(self):
        return self._nodes.keys()

    @property
    def list(self):
        return self._nodes.values()

    def _get_deps(self, nid, dType):
        tClasses = {
            "attackers": ["Move", "MoveConv"],
            "defenders": ["SupportH"],
            "supporters": ["SupportM"]}
        tComp = {"attackers": "to", "defenders": "to", "supporters": "fr"}
        res = []
        for node in self.list:
            for tClass in tClasses[dType]:
                if node.type == tClass and getattr(node, tComp[dType]) == nid:
                    res.append(node)
        #: support move to different terr removal
        if dType == "supporters":
            nrem = []
            for node in res:
                if node.to != self.get(nid).to:
                    nrem.append(node)
            for node in nrem:
                res.remove(node)
        return res

    def _get_attackers(self, nid):
        return self._get_deps(nid, "attackers")

    def _get_defenders(self, nid):
        return self._get_deps(nid, "defenders")

    def _get_supporters(self, nid):
        return self._get_deps(nid, "supporters")

    def _get_convoyers(self, llid):
        res = []
        for lid in llid:
            l = []
            for nid in lid:
                l.append(self.get(nid))
            res.append(l)
        return res

    def log(self, msg):
        self._adj._logstack += msg+"\n"


class Node(object):
    def __init__(self, nodes, oid, data):
        self._up = nodes
        self.id = oid
        self.country = data.get("country")
        ## TEMP, remove next var in productioN!!!
        self.name = data.get("name")
        ##
        self.type = self.__class__.__name__
        self.fr = data.get("from")
        self.to = data.get("to")
        self._failed = data.get("failed") or False
        self._start()

    def _start(self):
        pass

    def _get_dependencies(self):
        return []

    def _solved_dep(self, dep=None):
        if not dep:
            self._dependencies.pop(0)
        else:
            self._dependencies.remove(dep)

    def _solved_deps_all(self):
        self._dependencies = []

    @property
    def depends(self):
        return self.dependencies[0] if self.dependencies else None

    @property
    def dependencies(self):
        if not hasattr(self, "_dependencies"):
            self._dependencies = self._get_dependencies()
        return self._dependencies

    @property
    def solved(self):
        if self._failed:
            return True
        return False if self.depends else True

    @property
    def succeeded(self):
        if self._failed:
            return False
        return self.success

    def __repr__(self):
        return '<Node %(country)s - %(id)s: %(name)s>' % dict(
            id=self.id, country=self.country, name=self.name)

    def log(self, msg):
        self._up.log(msg)


class Hold(Node):
    def _start(self):
        self._dislodged = None

    def _get_dependencies(self):
        return self.defenders+self.attackers

    @property
    def attackers(self):
        if not hasattr(self, "_attackers"):
            self._attackers = self._up._get_attackers(self.id)
        return self._attackers

    @property
    def defenders(self):
        if not hasattr(self, "_defenders"):
            self._defenders = self._up._get_defenders(self.id)
        return self._defenders

    @property
    def strength_def(self):
        strength = (1, 1)
        for node in self.defenders:
            addmin, addmax = 0, 0
            if node.solved:
                if node.succeeded:
                    addmin += 1
                    addmax += 1
            else:
                addmax += 1
            strength = (strength[0]+addmin, strength[1]+addmax)
        return strength

    def solve(self):
        ## we just need 1 successful attack with strength > 1 to solve
        #print self.dependencies
        #dep_rem = []
        dependencies = [node for node in self.dependencies]
        for node in dependencies:
            self.log("\tHold: solving "+str(node))
            if node in self.defenders:
                #if node.solved:
                if node._attacked is not None:
                    self._solved_dep(node)
            else:
                self._dislodged = self.dislodged(node)
                if self._dislodged is not None:
                    if self._dislodged:
                        self._solved_deps_all()
                        #dep_rem = []
                        break
                    #print "removing "+str(node)
                    #dep_rem.append(node)
                    self._solved_dep(node)
        #for node in dep_rem:
        #   self._solved_dep(node)

    def dislodged(self, versus=None):
        if not versus:
            versus = self.depends
        if versus:
            if versus.type in ["Move", "MoveConv"]:
                if versus.solved:
                    self.log("\t\tDependency is solved for "+str(versus))
                    if versus.succeeded:
                        self.log(
                            "\t\t-> Other army " + str(versus) +
                            " is succesful moving to me. I'm dislodged.")
                        return True
                    self.log(
                        "\t\t-> Other army " + str(versus) +
                        " fail moving to me. I'm not dislodged.")
                    return False
                #else:
                    #return num_compare()
                self.log("\t\tDependency is not solved for "+str(versus))
                return None
        return False

    def _dislodge_u(self):
        ## teorically we load this only if order is failed
        for node in self.attackers:
            if node.succeeded:
                return True
        return False

    @property
    def success(self):
        if self._dislodged is not None:
            return not self._dislodged
        return not self.dislodged()

    @property
    def dislodged_unit(self):
        if self.type == "Hold":
            return not self.succeeded
        return self._dislodge_u()


class Move(Hold):
    def _start(self):
        Hold._start(self)
        self.success_var = None

    def _get_dependencies(self):
        holder = []
        if not self.to_empty:
            holder.append(self.holder)
            attackers_others = list(self.holder.attackers)
        ## note: cannot use _up.get in next line because self.to can be empty
        else:
            attackers_others = self._up._get_attackers(self.to)
        ### TO IMPROVE: removing myself
        if self in attackers_others:
            attackers_others.remove(self)
        return self.supporters+holder+attackers_others

    @property
    def holder(self):
        if not hasattr(self, "_holder"):
            self._holder = self._up.get(self.to)
        return self._holder

    @property
    def supporters(self):
        if not hasattr(self, "_supporters"):
            self._supporters = self._up._get_supporters(self.id)
        return self._supporters

    def _strength_att(self, countrycheck=True):
        strength = (1, 1)
        vs = self._up.get(self.to)
        country = vs.country if vs else None
        for node in self.supporters:
            proc_node = True
            if countrycheck:
                proc_node = True if node.country != country else False
            if proc_node:
                addmin, addmax = 0, 0
                if node.solved:
                    if node.succeeded:
                        addmin += 1
                        addmax += 1
                else:
                    addmax += 1
                strength = (strength[0]+addmin, strength[1]+addmax)
        return strength

    @property
    def strength_att(self):
        return self._strength_att()

    @property
    def strength_ssa(self):
        return self._strength_att(False)

    @property
    def to_empty(self):
        return self.holder is None

    @property
    def holderMoving(self):
        if self.to_empty:
            return False
        return self.holder.type in ["Move", "MoveConv"]

    @property
    def swapping(self):
        if self.holderMoving:
            if self.holder.to == self.id and self.to == self.holder.id:
                if "MoveConv" in [self.type, self.holder.type]:
                    return True
        return False

    def _compare_num(self, versus, vCompare, sCompare, swap=False):
        self.log("\t\tcomparing: my "+sCompare+" - vs "+vCompare)
        s_attr = getattr(self, sCompare)
        v_attr = getattr(versus, vCompare)
        self.log("\t\tcomparing values: " + str(s_attr[0]) + "," +
                 str(s_attr[1]) + " - " + str(v_attr[0]) + "," +
                 str(v_attr[1]))
        ## we try to rapidly solve checking two easy cases:
        ## 1) my min stregth > versus max strength: I'm winning on this
        ## dependency and the versus is failed
        if s_attr[0] > v_attr[1]:
            self.log("\t\t\t-> min att > max comparing: solved")
            ## we had to check self dislodgement tries of me or versus player
            return True
        ## 2) my max strength <= versus min strength: I'm loosing at all.
        if s_attr[1] <= v_attr[0]:
            if vCompare in ["strength_att", "strength_ssa"]:
                ## my max att < versus min att
                if s_attr[1] < v_attr[0]:
                    ## convoyed unit exception
                    if versus.type == "MoveConv" and self.type != "MoveConv":
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
                if s_attr[1] == v_attr[0]:
                    ## convoyed unit exception
                    if versus.type == "MoveConv" and self.type != "MoveConv":
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

    def _compare(self, versus):
        ## we need to compare attack power, so we need to count supporters
        move = False
        if versus.type in ["Move", "MoveConv"]:
            vCompare = "strength_att"
            move = True
        else:
            vCompare = "strength_def"
        if not move:
            ## the other unit is not moving (hold or support)
            self.log("\t\t-> other unit is not moving..")
            return self._compare_num(versus, vCompare, "strength_att")
        elif move and versus.to == self.id:
            ## the other unit is moving to me
            self.log("\t\t-> other unit is moving to me..")
            if versus == self.holder and self.swapping:
                self.log("\t\t -> units are swapping..")
                vCompare = "strength_def"
                return self._compare_num(versus, vCompare, "strength_att",
                                         True)
            return self._compare_num(versus, vCompare, "strength_att")
        elif move and versus.to == self.to:
            ## the other unit is moving to the same terr I'm moving to
            self.log("\t\t-> other unit is moving to same terr..")
            ## if one of the other attackers is in 1vs1 with my holder,
            ## I had to check more stuffs
            if versus != self.holder:
                if self.holderMoving:
                    if self.holder.to == versus.id:
                        self.log(
                            "\t\t-> other unit is in 1on1 with my holder..")
                        ## I need to know if holder have succeded in the move
                        if self.holder.solved:
                            if self.holder.succeeded and not \
                                    self.holder.swapping:
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
            sCompare = "strength_att"
            ## complete strength if holder is moving and country is same
            #if self.holderMoving:
            #   if self.country == self.holder.country:
            #       print "\t\t-> holder is moving and my country is same.."
                    ## use complete strength of myself
            #       sCompare = "strength_ssa"
            #   if versus.country == self.holder.country:
            #       print "\t\t-> holder is moving and versus country is same."
                    ## use complete strength of versus
            #       vCompare = "strength_ssa"
            ## additional considerations for units swap
            if self.holderMoving:
                self.log("\t\t-> Holder is moving..")
                if self.strength_att != self.strength_ssa:
                    self.log("\t\t-> my s_att != s_ssa..")
                    if self.holder.solved:
                        self.log("\t\t\t-> Holder move is solved, continue..")
                        if self.holder.succeeded:
                            sCompare = "strength_ssa"
                        else:
                            sCompare = "strength_att"
                    else:
                        self.log(
                            "\t\t\t-> Holder move is unsolved, breaking..")
                        return None
                if versus.strength_att != versus.strength_ssa:
                    self.log("\t\t-> versus s_att != s_ssa..")
                    #if self.holder.solved:
                    #   print "\t\t\t-> Holder move is solved, continue.."
                    #   if self.holder.succeeded:
                    #       vCompare = "strength_ssa"
                    #   else:
                    #       vCompare = "strength_att"
                    #else:
                    #   print "\t\t\t-> Holder move is unsolved, breaking.."
                    #   return None
                    vCompare = "strength_ssa"
            return self._compare_num(versus, vCompare, sCompare)
        else:
            ## the other unit is moving to another terr
            self.log("\t\t-> other unit is moving to another terr..")
            if versus.solved:
                if versus.succeeded:
                    self.log("\t\t\t-> other unit moved, dependency solved.")
                    return True
                return self._compare_num(versus, "strength_def",
                                         "strength_att")
            self.log(
                "\t\t\t-> no information on other unit, dependency unsolved.")
            return None

    def solve(self):
        compare_stack = []
        check_stack = True if self.success_var is None else False
        dependencies = [node for node in self.dependencies]
        for node in dependencies:
            self.log("\tMove: comparing dependency "+str(node))
            if node in self.supporters:
                self.log("\t\tdependency is a supporter")
                if node.solved:
                    self._solved_dep(node)
                    self.log("\t\tdependency is solved for "+str(node))
            else:
                ## get success on the single dependency
                success = self._compare(node)
                if success is not False:
                    ## store in the compare stack, as we need to check every
                    ## dependency is won to move
                    compare_stack.append(success)
                if success is not None:
                    if not success:
                        ## we ended, there's someone powerful than me
                        self.log("\tMove: movement failed.")
                        self.success_var = False
                        #self._solved_deps_all()
                        ## TEST: maintaining support dependencies alive
                        #for dep in self.dependencies:
                        for dep in [d for d in self.dependencies]:
                            if dep not in self.supporters:
                                self._solved_dep(dep)
                        ##
                        check_stack = False
                        break
                    else:
                        ## I've solved this dependency
                        self._solved_dep(node)
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
                self.log("\tMove: movement succeeded.")
                self.success_var = True
                self._solved_deps_all()

    def solve_force(self, val=True):
        self.log("\tMove: forcing moving "+str(self))
        self.success_var = val
        self._solved_deps_all()

    #@property
    #def solved(self):
    #   if self._failed:
    #       return True
    #   return self.success_var is not None

    @property
    def success(self):
        if self.success_var is None:
            self.solve()
        return self.success_var


class MoveConv(Move):
    def _start(self):
        Move._start(self)
        self._convoyed = None

    def set_routes(self, llid):
        self._convoy_routes = llid

    def _get_dependencies(self):
        self._convoyers = self._up._get_convoyers(self._convoy_routes)
        a = []
        for l in self._convoyers:
            for node in l:
                #a.append(node)
                if node not in a:
                    a.append(node)
        b = Move._get_dependencies(self)
        return a+b

    @property
    def strength_att(self):
        if self.convoyed is False:
            return (0, 0)
        return self._strength_att()

    @property
    def strength_ssa(self):
        if self.convoyed is False:
            return (0, 0)
        return self._strength_att(False)

    def solve(self):
        # TO IMPROVE: duplicates nodes (different routes can have common nodes)
        ## we need succesful convoy and then sove with Move class
        dep_rem = []
        ## NEED NEXT check:
        if not hasattr(self, "_convoyers"):
            #self._get_dependencies()
            self.dependencies
        move_check = False
        routes_fail = []
        for route in self._convoyers:
            self.log("\tMoveViaConvoy: Processing route "+str(route))
            convoy_succ = []
            conv_rem = []
            ## convoyers check in the route
            for convoyer in route:
                self.log("\t\tProcessing convoyer "+str(convoyer))
                #self._versus = convoyer
                #self._convoyed = self.convoyed
                #self._versus = None
                convoyed = self._solve_convoyer(convoyer)
                if convoyed is not None:
                    ## solved node, add dependency to remove list
                    conv_rem.append(convoyer)
                    if not convoyed:
                        ## fail the route and break the cycle
                        routes_fail.append(route)
                        break
                    else:
                        ## append node to success stack
                        convoy_succ.append(True)
            ## if the success stack len is the same as the route, the convoy
            ## chain is successful
            if len(convoy_succ) == len(route):
                ## IS IT ENOUGH? I THINK SO; I DON'T CONSIDER OTHER ROUTES
                for r in self._convoyers:
                    for node in r:
                        if node not in dep_rem:
                            dep_rem.append(node)
                ## proceeed to the normal moves solving
                self.log("\tMoveViaConvoy: route succeeded")
                move_check = True
                break
            ## else we just remove solved dependencies
            else:
                for node in conv_rem:
                    #self._solved_dep(node)
                    if node not in dep_rem:
                        dep_rem.append(node)
        for node in dep_rem:
            if node in self.dependencies:
                self._solved_dep(node)
        if not move_check:
            ## verify that all routes have failed
            if routes_fail == self._convoyers:
                ## the movement is failing, removing all deps
                self.log("\tMoveViaConvoy: all convoy routes failed.")
                self._convoyed = False
                self.success_var = False
                self._solved_deps_all()
            else:
                self.log("\tMoveViaConvoy: convoy routes not solved..")
                for route in routes_fail:
                    self._convoyers.remove(route)
        else:
            ## normal movement solve
            self._convoyed = True
            self.log("\tMoveViaConvoy: starting normal movement solving..")
            Move.solve(self)

    def _solve_convoyer(self, convoyer):
        if not (convoyer.type == "Convoy" and convoyer.fr == self.id):
            return False
        if convoyer._dislodged:
            return False
        if convoyer.solved:
            if convoyer.succeeded:
                return True
            return False
        return None

    @property
    def convoyed(self):
        if self._convoyed is None:
            self.solve()
        return self._convoyed


class Convoy(Hold):
    def _start(self):
        Hold._start(self)
        #self._versus = None

    def _solve_force(self):
        #dep_rem = []
        compare_stack = []
        dependencies = [node for node in self.dependencies]
        for node in dependencies:
            self.log("\tConvoy: force solving "+str(node))
            self._versus = node
            #self._dislodged = self.dislodged_fake
            att = self.dislodged_fake(node)
            #self._versus = None
            #if self._dislodged is not None:
            if att is not None:
                #if self._dislodged:
                #   self._solved_deps_all()
                    #dep_rem = []
                #   break
                #dep_rem.append(node)
                self._solved_dep(node)
                compare_stack.append(att)
            else:
                self.log("\tConvoy: cannot force solve node "+str(node))
        m_att = max(compare_stack)
        m_count = 0
        for att in compare_stack:
            if att == m_att:
                m_count += 1
        if m_count == 1 and m_att > 1:
            self._dislodged = True
            self._solved_deps_all()
        else:
            self._dislodged = False
        #for node in dep_rem:
        #   self._solved_dep(node)

    #@property
    def dislodged_fake(self, by=None):
        if not by:
            by = self.depends
        if by.type == "Move":
            #if by.strength_att[1] > 1:
            #   return True
            #return False
            return by.strength_att[1]
        return None

    def solve_force(self):
        self.log("\tConvoy: force solving "+str(self))
        #self._solved_deps_all()
        dependencies = [node for node in self.dependencies]
        for node in dependencies:
            if node not in self.defenders:
                self._solved_dep(node)
        self._dislodged = True


class Support(Hold):
    def _start(self):
        Hold._start(self)
        self._attacked = None

    #def _get_dependencies(self):
    #    return self._up._get_attackers(self.id)

    def solve(self):
        #dep_rem = []
        ## we just need 1 attack to have this solved
        #dependencies = [node for node in self.dependencies]
        #for node in dependencies:
        dep_rem = []
        attackers = [k for k in self.attackers if k in self.dependencies]
        fail_attacks = 0
        for node in attackers:
            self.log("\tSupport: solving dependency "+str(node))
            #self._attacked = self.attacked(node)
            _attacked = self.attacked(node)
            #if self._attacked is not None:
            print('attacked', _attacked)
            if _attacked is not None:
                #if self._attacked:
                if _attacked:
                    self._attacked = True
                    self.log("\tSupport: I'm attacked. Support failed.")
                    #self._solved_deps_all()
                    dep_rem = attackers
                    #dep_rem = []
                    break
                else:
                    self.log("\tSupport: attacker failed, still supporting.")
                    fail_attacks += 1
                self._solved_dep(node)
            else:
                self.log("\tSupport: dependency "+str(node)+" unsolved.")
        for node in dep_rem:
            if node in self.dependencies:
                self._solved_dep(node)
        if fail_attacks == len(self.attackers):
            self._attacked = False
        #: proc defenders!
        Hold.solve(self)

    @property
    def success(self):
        if self._attacked is not None:
            return not self._attacked
        return not self.attacked()


class SupportM(Support):
    def attacked(self, versus=None):
        if not versus:
            versus = self.depends
        if versus:
            ## the army I'm supporting against cannot cut my support
            if versus.id == self.to:
                ## only if the army have stregth 1
                if self._up.get(self.to).strength_att[1] == 1:
                    return False
                ## or is not a dislodge case
                disl = self.dislodged(versus)
                return disl
            ## an army of my country cannot cut my support
            if versus.country == self.country:
                return False
            if versus.type == "MoveConv":
                if versus.solved:
                    #if versus.succeeded:
                    if versus.convoyed:
                        return True
                    return False
                return None
            return True
        return False


class SupportH(Support):
    def attacked(self, versus=None):
        ## load a defined versus or first dependency
        if not versus:
            versus = self.depends
        if versus:
            ## if move is via convoy we should check if succeeded
            if versus.type == "MoveConv":
                ## if not solved we should process it
                if versus.solved:
                    ## return the result of the movement,
                    ## a faied move via convoy should not cut the support
                    #if versus.succeeded:
                    if versus.convoyed:
                        return True
                    return False
                return None
            ## if move is not via convoy the support is cut
            return True
        return False
