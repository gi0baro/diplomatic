# -*- coding: utf-8 -*-

import json

from diplomacy.constants import PHASES, ORDERS
from diplomacy.checkers import Validator, PreProcessor
from diplomacy.judge import Judge


def _load_raw_orders(group):
    with open('tests/raw/{}.txt'.format(group)) as f:
        lines = f.readlines()
    return lines


def load_map():
    with open('variants/classic/classic.json') as f:
        rv = json.load(f)
    return rv


def get_test_data(raw, mapref):
    tests, troops, mcpos, expected = [], [], [], []
    #: build inverse dict for map reference
    nameref = {}
    for k, v in mapref['names'].items():
        nameref[v] = k
    #: process
    reading = None
    i = -1
    for line in raw:
        sline = line.strip()
        if sline.startswith('Feature:'):
            i += 1
            tests.append({'data': {}, 'feature': sline.split("Feature: ")[1]})
            troops.append({})
            mcpos.append({})
            expected.append({})
        else:
            if sline == "Given":
                reading = "orders"
            elif sline == "Then":
                reading = "results"
            elif sline.endswith(':'):
                country = sline[:-1]
                tests[i]['data'][country] = {}
                troops[i][country] = {'armies': [], 'fleets': []}
            else:
                if not sline:
                    continue
                if reading == "orders":
                    lelements = sline.split(" ")
                    troop_type = lelements[0]
                    #: get the movement type
                    for word in [" holds", " moves ", " supports movement ", " supports hold ", " convoys "]:
                        if word in sline:
                            cmd = word
                            break
                    mc = None
                    troop_pos = sline.split(" in ")[1].split(cmd)[0]
                    if troop_pos.endswith(" (nc)"):
                        troop_pos = troop_pos[:-5]
                        mc = 0
                    if troop_pos.endswith(" (sc)"):
                        troop_pos = troop_pos[:-5]
                        mc = 1
                    troop_id = nameref[troop_pos]
                    if mc in [0, 1]:
                        mcpos[i][troop_id] = mc
                    if troop_type == "fleet":
                        troops[i][country]['fleets'].append(troop_id)
                    else:
                        troops[i][country]['armies'].append(troop_id)
                    order_data = sline.split(cmd)[1]
                    if cmd == " holds":
                        data = {'type': ORDERS.HOLD}
                    elif cmd == " moves ":
                        sub = order_data.split("to ")[1]
                        via_convoy = False
                        if sub.endswith(" via convoy"):
                            via_convoy = True
                            sub = sub[:-11]
                        mc = None
                        if sub.endswith(" (nc)"):
                            mc = 0
                            sub = sub[:-5]
                        if sub.endswith(" (sc)"):
                            mc = 1
                            sub = sub[:-5]
                        data = {'type': ORDERS.MOVE, 'dst': nameref[sub]}
                        if via_convoy:
                            data['through'] = True
                        if mc in [0, 1]:
                            data['mc'] = mc
                    elif cmd == " supports movement ":
                        sub = order_data.split("of ")[1]
                        sub = sub.split(" to ")
                        data = {'type': ORDERS.SUPPORT_MOVE, 'src': nameref[sub[0]], 'dst': nameref[sub[1]]}
                    elif cmd == " supports hold ":
                        sub = order_data.split("of ")[1]
                        data = {'type': ORDERS.SUPPORT_HOLD, 'dst': nameref[sub]}
                    elif cmd == " convoys ":
                        sub = order_data.split(" to ")
                        data = {'type': ORDERS.CONVOY, 'src': nameref[sub[0]], 'dst': nameref[sub[1]]}
                    tests[i]['data'][country][troop_id] = data
                else:
                    troop_pos = sline.split(" fails")[0]
                    expected[i][nameref[troop_pos]] = False
    return tests, troops, expected


def apply_convoys_fixture(mapref, tests, troops):
    for _, test in enumerate(tests):
        game_data = {}
        for key in ["terrs", "supply", "centers", "phase", "prev", "mc_pos"]:
            game_data[key] = None
        game_data["troops"] = {'armies': [], 'fleets': []}
        game_data["armies"] = []
        game_data["fleets"] = []
        for country, tdata in troops[_].items():
            for troop in tdata["armies"]:
                game_data["armies"].append(troop)
            for troop in tdata["fleets"]:
                game_data["fleets"].append(troop)
        for country, orders in test['data'].items():
            validator = Validator(
                mapref, troops[_][country]['armies'] + troops[_][country]['fleets'], {}, game_data['armies'],
                game_data['fleets'], {}, 'diplomacy', {}, _prnt)
            for territory_id, order in orders.items():
                if order['type'] == ORDERS.MOVE:
                    if territory_id in troops[_][country]['armies']:
                        make_convoy = False
                        if order.get('through'):
                            make_convoy = True
                        if not make_convoy:
                            for other_order in orders.values():
                                if other_order['type'] == ORDERS.CONVOY and other_order.get('src', 0) == territory_id:
                                    make_convoy = True
                        if make_convoy or order['dst'] not in mapref['links']['armies'].get(territory_id, []):
                            if order['dst'] in validator._convoy_maps(territory_id):
                                routes = validator._get_convoy_routes(territory_id, order['dst'])
                                order['through'] = True
                                order['convoy_routes'] = routes


def _prnt(*args):
    print(*args)


def _test_game(obj, testn):
    test = obj.data[testn]
    print("Orders:\n" + str(test['data']))
    preproc = PreProcessor(test['data'], _prnt)
    failed_orders = preproc.process("diplomacy")
    print("[GameProc:Pre] failed: " + str(preproc.fails))
    for fail_tup in failed_orders:
        test['data'][fail_tup[0]][fail_tup[1]]['failed'] = True
    adjOrders = dict()
    for country, order in test['data'].items():
        for tid, data in order.items():
            adjOrders[tid] = data
            adjOrders[tid]['country'] = country
            adjOrders[tid]['name'] = obj.mapref["names"][tid]
    adj = Judge(adjOrders, _prnt)
    print("Feature: " + test['feature'])
    adj.adjudicate()
    for node in adj.orders.list:
        assert node.succeeded == obj.expected[testn].get(node.id, True)


def pytest_generate_tests(metafunc):
    raw_name = "_".join(metafunc.function.__name__.split("_")[1:])
    raw_data = _load_raw_orders(raw_name)
    tests, troops, expected = get_test_data(raw_data, metafunc.cls.mapref)
    apply_convoys_fixture(metafunc.cls.mapref, tests, troops)
    idlist = []
    argvalues = []
    for _, test in enumerate(tests):
        idlist.append(test['feature'])
        argvalues.append((test['data'], expected[_]))
    metafunc.parametrize(['orders', 'expected'], argvalues, ids=idlist, scope="class")


class TestClass(object):
    mapref = load_map()

    def _run_tests(self, orders, expected):
        preproc = PreProcessor(orders, _prnt)
        failed_orders = preproc.process(PHASES.DIPLOMACY)
        print("[GameProc:Pre] failed: {}".format(failed_orders))
        for fail_tup in failed_orders:
            orders[fail_tup[0]][fail_tup[1]]['failed'] = True
        judge_orders = {}
        for country, order in orders.items():
            for tid, data in order.items():
                judge_orders[tid] = data
                judge_orders[tid]['country'] = country
                judge_orders[tid]['name'] = self.mapref["names"][tid]
        adj = Judge(judge_orders, _prnt)
        # print("Feature: " + test['feature'])
        adj.process()
        for node in adj.orders.list:
            try:
                assert node.succeeded == expected.get(node.id, True)
            except AssertionError as exc:
                raise Exception(f'Check failed over node {node.id}: succeeded {node.succeeded} expected {expected.get(node.id, True)}')

    def test_basic(self, orders, expected):
        self._run_tests(orders, expected)

    def test_circular(self, orders, expected):
        self._run_tests(orders, expected)

    def test_supports(self, orders, expected):
        self._run_tests(orders, expected)

    def test_head2head(self, orders, expected):
        self._run_tests(orders, expected)

    def test_convoys(self, orders, expected):
        self._run_tests(orders, expected)

    def test_convoys_adjacent(self, orders, expected):
        self._run_tests(orders, expected)
