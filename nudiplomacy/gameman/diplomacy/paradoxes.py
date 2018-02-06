
from .nodes import Convoy, Move, MoveThrough
from .exceptions import ParadoxException


class Paradox(object):
    def __init__(self, chain):
        self.chain = chain

    def log(self, msg):
        msg = "[Paradox] " + msg
        self.chain.judge._logstack += msg

    @property
    def stack(self):
        return self.chain.list

    def _is_move_chain(self):
        for node in self.stack:
            if node.type not in [Move, MoveThrough]:
                return False
        for i in range(0, len(self.stack)):
            j = i + 1 if i + 1 < len(self.stack) else 0
            if self.stack[i].dst != self.stack[j].id:
                return False
        return True

    def _get_convoys_in_chain(self):
        rv = []
        for node in self.stack:
            if node.type == Convoy:
                rv.append(self.stack.index(node))
        return rv

    def resolve(self):
        self.log("solving {}".format(self.stack))
        if self._is_move_chain():
            self.log("this is a move chain, solving the first..")
            self.chain.current_node.force_resolution()
            self.chain.rem_last()
        elif self._get_convoys_in_chain():
            self.log("convoy chain detected, solving the convoy..")
            #: re-order chain
            positions = self._get_convoys_in_chain()
            min_convoy_position = min(positions)
            if min_convoy_position == 0:
                new_chain = []
            else:
                new_chain = self.stack[0:min_convoy_position]
            #: Convoy's solve force follow the "Szykman law" which states that
            #  the unit being convoyed is unsuccessful, and has no influence
            #  over the territory it is being convoyed to.
            for position in positions:
                self.chain.stack[position].force_resolution()
            self.chain.stack = new_chain
        else:
            #: We should never get this.
            self.log("ERROR: I don't know how to solve this.")
            raise ParadoxException(self)
