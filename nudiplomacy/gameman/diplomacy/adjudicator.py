from ._glob import G
from .nodes import Nodes
from .chains import Chain


class Adjudicator(object):
    def __init__(self, orders, logger=None):
        self._logger = logger or G['logger']
        self.log = lambda x: self._logger("[Adjudicator] "+x)
        self.orders_db = orders
        self.chains = []
        self.chained = []
        self._start()

    def _start(self):
        self.orders = Nodes()
        for order_id, order in self.orders_db.iteritems():
            self.orders.new(order_id, order)
            if order.get('convoy_routes') is not None:
                self.orders.get(order_id).set_routes(order["convoy_routes"])

    def _solve(self, node):
        self.log("Solving "+str(node)+"..")
        #paradox = (False, None)
        startpoint = node.id
        if startpoint not in self.chained:
            chain = Chain()
            self.chains.append(chain)
            chain.new(node)
            chain.solve()
            for node in chain.list:
                self.chained.append(node.id)
        else:
            self.log(str(node)+" is yet in a chain, skipping.")

    def adjudicate(self):
        ## let's do the magic
        for node in self.orders.list:
            if not node.solved:
                self._solve(node)
            else:
                self.log(str(node)+" already solved.")
