import json
from . import rpath
from .parser import build_orders


mapf = open(rpath+'/../variants/classic/classic.json')
mapref = json.load(mapf)
mapf.close()


class TestBasic(object):
    raw = "basic"

build_orders(TestBasic, mapref)


class TestCircular(object):
    raw = "circular"

build_orders(TestCircular, mapref)


class TestSupports(object):
    raw = "supports"

build_orders(TestSupports, mapref)


class TestHead2Head(object):
    raw = "head2head"

build_orders(TestHead2Head, mapref)


class TestConvoys(object):
    raw = "convoys"

build_orders(TestConvoys, mapref)


class TestAdjacentConvoys(object):
    raw = "convoys_adjacent"

build_orders(TestAdjacentConvoys, mapref)
