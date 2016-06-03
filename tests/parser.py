from __future__ import print_function
from diplomacy.checker import Validator, PreProcessor
from diplomacy.adjudicator import Adjudicator
from . import rpath


def _get_raw_data(fname):
    f = open(rpath+'/raw/'+fname+".txt")
    lines = f.readlines()
    f.close()
    return lines


def _parse_raw_data(raw, mapref, tests, troops, mcpos, expected):
    #: build inverse dict for map reference
    nameref = {}
    for k, v in mapref['names'].iteritems():
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
                    for word in [" holds", " moves ", " supports movement ",
                                 " supports hold ", " convoys "]:
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
                        data = {'type': 'hold'}
                    elif cmd == " moves ":
                        sub = order_data.split("to ")[1]
                        viaConvoy = False
                        if sub.endswith(" via convoy"):
                            viaConvoy = True
                            sub = sub[:-11]
                        mc = None
                        if sub.endswith(" (nc)"):
                            mc = 0
                            sub = sub[:-5]
                        if sub.endswith(" (sc)"):
                            mc = 1
                            sub = sub[:-5]
                        data = {'type': 'move', 'to': nameref[sub]}
                        if viaConvoy:
                            data['viaConvoy'] = True
                        if mc in [0, 1]:
                            data['mc'] = mc
                    elif cmd == " supports movement ":
                        sub = order_data.split("of ")[1]
                        sub = sub.split(" to ")
                        data = {'type': 'sup_move', 'from': nameref[sub[0]],
                                'to': nameref[sub[1]]}
                    elif cmd == " supports hold ":
                        sub = order_data.split("of ")[1]
                        data = {'type': 'sup_hold', 'to': nameref[sub]}
                    elif cmd == " convoys ":
                        sub = order_data.split(" to ")
                        data = {'type': 'convoy', 'from': nameref[sub[0]],
                                'to': nameref[sub[1]]}
                    tests[i]['data'][country][troop_id] = data
                else:
                    troop_pos = sline.split(" fails")[0]
                    expected[i][nameref[troop_pos]] = False


def _convoys_fixture(mapref, tests, troops):
    i = 0
    for test in tests:
        gdata = dict()
        for key in ["seas", "coasts", "multi_coasts", "neutrals"]:
            gdata[key] = mapref[key]
        gdata["mcoasts"] = gdata['multi_coasts']
        gdata["moves"] = mapref["links"]
        for key in ["terrs", "supply", "centers", "phase", "prev", "mc_pos"]:
            gdata[key] = None
        gdata["troops"] = {'armies': [], 'fleets': []}
        gdata["armies"] = []
        gdata["fleets"] = []
        for country, tdata in troops[i].iteritems():
            for troop in tdata["armies"]:
                gdata["armies"].append(troop)
            for troop in tdata["fleets"]:
                gdata["fleets"].append(troop)
        validator = Validator(gdata, test['data'])
        for country, cdata in test['data'].iteritems():
            for k, order in cdata.iteritems():
                if order['type'] == "move":
                    if k in troops[i][country]['armies']:
                        make_convoy = False
                        if order.get('viaConvoy'):
                            make_convoy = True
                        if not make_convoy:
                            for kc, orderc in cdata.iteritems():
                                if orderc['type'] == "convoy" and \
                                        orderc.get('from', 0) == k:
                                    make_convoy = True
                        if make_convoy or order['to'] not in \
                                mapref['links']['armies'].get(k, []):
                            if order['to'] in validator._convoy_maps(k):
                                routes = validator._get_convoy_routes(
                                    k, order['to'])
                                order['viaConvoy'] = True
                                order['convoy_routes'] = routes
        i += 1


def _test_f(obj, testn):
    test = obj.data[testn]
    print("Orders:\n"+str(test['data']))
    checker = PreProcessor(test['data'], lambda m: print(m))
    checker.process("diplomacy")
    print("[GameProc:Pre] failed: "+str(checker.fails))
    for fail_tup in checker.fails:
        test['data'][fail_tup[0]][fail_tup[1]]['failed'] = True
    adjOrders = dict()
    for country, order in test['data'].iteritems():
        for tid, data in order.iteritems():
            adjOrders[tid] = data
            adjOrders[tid]['country'] = country
            adjOrders[tid]['name'] = obj.mapref["names"][tid]
    adj = Adjudicator(adjOrders, lambda m: print(m))
    print("Feature: "+test['feature'])
    adj.adjudicate()
    for node in adj.orders.list:
        assert node.succeeded == obj.expected[testn].get(node.id, True)


def build_orders(tclass, mapdata):
    rawdata = _get_raw_data(tclass.raw)
    tests = []
    troops = []
    mcpos = []
    expected = []
    _parse_raw_data(rawdata, mapdata, tests, troops, mcpos, expected)
    _convoys_fixture(mapdata, tests, troops)
    print(troops)
    print(mcpos)
    print(tests)
    print(expected)
    tclass.mapref = mapdata
    tclass.data = tests
    tclass.expected = expected
    i = 0
    for test in tests:
        setattr(tclass, 'test_'+str(i), lambda c, n=i: _test_f(c, n))
        i += 1
