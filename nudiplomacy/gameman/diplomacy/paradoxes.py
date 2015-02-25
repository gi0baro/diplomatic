from .exceptions import ParadoxException


class Paradox(object):
    def __init__(self, chain, loop):
        self._chain = chain
        self._loop = loop

    def log(self, msg):
        msg = "[Paradox] "+msg+"\n"
        self._chain._adj._logstack += msg

    @property
    def _stack(self):
        return self._chain.list

    def solve(self):
        self.log("solving "+str(self._stack))
        self._resolve()

    def _isMoveChain(self, getConvoy=False):
        def res(val):
            if getConvoy:
                return (val, convoy)
            return val
        convoy = None
        for node in self._stack:
            if node.type not in ["Move", "MoveConv"]:
                return res(False)
            if getConvoy:
                if node.type == "MoveConv":
                    convoy = node
        for i in range(0, len(self._stack)):
            j = i+1 if i+1 < len(self._stack) else 0
            if self._stack[i].to != self._stack[j].id:
                return res(False)
        return res(True)

    def _getConvoyInChain(self):
        for node in self._stack:
            if node.type == "Convoy":
                return self._stack.index(node)
        return None

    def _getConvoysInChain(self):
        rv = []
        for node in self._stack:
            if node.type == "Convoy":
                rv.append(self._stack.index(node))
        return rv

    def _resolve(self):
        if self._isMoveChain():
            self.log("this is a move chain, solving the first..")
            self._chain.proc.solve_force()
            self._chain.rem_last()
        #elif self._getConvoyInChain() is not None:
        elif self._getConvoysInChain():
            self.log("convoy chain detected, solving the convoy..")
            #: re-order chain
            #i = self._getConvoyInChain()
            #if i == 0:
            #    new_chain = [self._stack[i]]
            #else:
            #    new_chain = self._stack[0:i]
            #    new_chain.append(self._stack[i])
            pos = self._getConvoysInChain()
            mpos = min(pos)
            if mpos == 0:
                new_chain = []
            else:
                new_chain = self._stack[0:mpos]
            #self._chain._stack = new_chain
            #: Convoy's solve force follow the "Szykman law" which states that
            #  the unit being convoyed is unsuccessful, and has no influence
            #  over the territory it is being convoyed to.
            #self._chain.proc.solve_force()
            #self._chain.rem_last()
            for p in pos:
                self._chain._stack[p].solve_force()
            self._chain._stack = new_chain
        else:
            #: We should never get this.
            self.log("ERROR: I don't know how to solve this.")
            raise ParadoxException(self)
