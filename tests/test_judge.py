# -*- coding: utf-8 -*-

from diplomatico.constants import OrderType, Phase, Season

from diplomatic.variants import load
from diplomatico import Board, Turn, process


def _load_raw_orders(group):
    with open("tests/raw/{}.txt".format(group)) as f:
        lines = f.readlines()
    return lines


def load_map():
    return load("variants/classic/classic.yaml")


def get_test_data(raw, mapref):
    tests, troops, mcpos, expected, dislodged = [], [], [], [], []
    #: build inverse dict for map reference
    nameref = {}
    for k, v in mapref["names"].items():
        nameref[v] = k
    #: process
    reading = None
    i = -1
    for line in raw:
        sline = line.strip()
        if sline.startswith("Feature:"):
            i += 1
            tests.append({"data": {}, "feature": sline.split("Feature: ")[1]})
            troops.append({})
            mcpos.append({})
            expected.append({})
            dislodged.append(set())
        else:
            if sline == "Given":
                reading = "orders"
            elif sline == "Then":
                reading = "results"
            elif sline.endswith(":"):
                country = sline[:-1]
                tests[i]["data"][country] = {}
                troops[i][country] = {"armies": [], "fleets": []}
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
                        troops[i][country]["fleets"].append(troop_id)
                    else:
                        troops[i][country]["armies"].append(troop_id)
                    order_data = sline.split(cmd)[1]
                    if cmd == " holds":
                        data = {"type": OrderType.HOLD}
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
                        data = {"type": OrderType.MOVE, "dst": nameref[sub]}
                        if via_convoy:
                            data["through"] = True
                        if mc in [0, 1]:
                            data["coast"] = mc
                    elif cmd == " supports movement ":
                        sub = order_data.split("of ")[1]
                        sub = sub.split(" to ")
                        data = {"type": OrderType.SUPPORT_MOVE, "src": nameref[sub[0]], "dst": nameref[sub[1]]}
                    elif cmd == " supports hold ":
                        sub = order_data.split("of ")[1]
                        data = {"type": OrderType.SUPPORT_HOLD, "dst": nameref[sub]}
                    elif cmd == " convoys ":
                        sub = order_data.split(" to ")
                        data = {"type": OrderType.CONVOY, "src": nameref[sub[0]], "dst": nameref[sub[1]]}
                    tests[i]["data"][country][troop_id] = data
                elif sline.endswith(" fails"):
                    expected[i][nameref[sline[: -len(" fails")]]] = False
                elif sline.endswith(" is dislodged"):
                    dislodged[i].add(nameref[sline[: -len(" is dislodged")]])
    return tests, troops, mcpos, expected, dislodged


def apply_convoys_fixture(mapref, tests, troops, coasts):
    for test, test_troops, test_coasts in zip(tests, troops, coasts):
        board = Board(mapref, test_troops, test_coasts)
        for country, orders in test["data"].items():
            for territory_id, order in orders.items():
                if order["type"] != OrderType.MOVE or territory_id not in test_troops[country]["armies"]:
                    continue
                convoyed = order.get("through") or any(
                    other["type"] == OrderType.CONVOY and other.get("src") == territory_id for other in orders.values()
                )
                if convoyed or order["dst"] not in mapref["links"]["armies"].get(territory_id, []):
                    if board.convoy_routes(territory_id, order["dst"]):
                        order["through"] = True


def pytest_generate_tests(metafunc):
    raw_name = "_".join(metafunc.function.__name__.split("_")[1:])
    raw_data = _load_raw_orders(raw_name)
    tests, troops, coasts, expected, dislodged = get_test_data(raw_data, metafunc.cls.mapref)
    apply_convoys_fixture(metafunc.cls.mapref, tests, troops, coasts)
    idlist = []
    argvalues = []
    for _, test in enumerate(tests):
        idlist.append(test["feature"])
        argvalues.append((test["data"], troops[_], coasts[_], expected[_], dislodged[_]))
    metafunc.parametrize(["orders", "troops", "coasts", "expected", "dislodged"], argvalues, ids=idlist, scope="class")


class TestClass(object):
    mapref = load_map()

    def _run_tests(self, orders, troops, coasts, expected, dislodged):
        territories = {country: [] for country in troops}
        turn = Turn(
            Phase.DIPLOMACY, 1901, Season.SPRING, territories, self.mapref["home_centers"], self.mapref["scs_to_win"]
        )
        outcome = process(Phase.DIPLOMACY, orders, Board(self.mapref, troops, coasts), turn)
        succeeded = {territory for _, territory in outcome.succeeded}
        dislodged_out = {territory for territories in outcome.dislodged.values() for territory in territories}
        for country_orders in orders.values():
            for territory in country_orders:
                name = self.mapref["names"][territory]
                assert (territory in succeeded) == expected.get(territory, True), f"{name}: succeeded"
                assert (territory in dislodged_out) == (territory in dislodged), f"{name}: dislodged"

    def test_basic(self, orders, troops, coasts, expected, dislodged):
        self._run_tests(orders, troops, coasts, expected, dislodged)

    def test_circular(self, orders, troops, coasts, expected, dislodged):
        self._run_tests(orders, troops, coasts, expected, dislodged)

    def test_supports(self, orders, troops, coasts, expected, dislodged):
        self._run_tests(orders, troops, coasts, expected, dislodged)

    def test_head2head(self, orders, troops, coasts, expected, dislodged):
        self._run_tests(orders, troops, coasts, expected, dislodged)

    def test_convoys(self, orders, troops, coasts, expected, dislodged):
        self._run_tests(orders, troops, coasts, expected, dislodged)

    def test_convoys_adjacent(self, orders, troops, coasts, expected, dislodged):
        self._run_tests(orders, troops, coasts, expected, dislodged)
