# -*- coding: utf-8 -*-

from .nodes import World
from .chains import Chain


class Judge(object):
    def __init__(self, orders, logger=None):
        self._logger = logger
        self._logstack = []
        self.orders_db = orders
        self.chains = []
        self.chained = []
        self.init()

    def log(self, msg):
        msg = "[Judge] " + msg
        self._logstack.append(msg)

    def init(self):
        self.orders = World(self)
        for order_id, order in self.orders_db.items():
            self.orders.create_node(order_id, order)
            if 'convoy_routes' in order:
                self.orders.get(order_id).set_routes(order["convoy_routes"])

    def resolve(self, node):
        self.log("Solving {}...".format(node))
        startpoint = node.id
        if startpoint in self.chained:
            self.log("{} is already in a cahin, skipping".format(node))
            return
        chain = Chain(self)
        self.chains.append(chain)
        chain.add(node)
        chain.solve()
        for node in chain.list:
            self.chained.append(node.id)

    def process(self):
        # let's do the magic
        for node in self.orders.list:
            if node.solved:
                self.log("{} already solved".format(node))
                continue
            self.resolve(node)
        if self._logger:
            self._logger("\n".join(self._logstack))
