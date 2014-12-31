from ._glob import G

log = lambda x: G['logger']("[Paradox] "+x)


class Paradox(object):
    def __init__(self, chain, loop):
        self._chain = chain
        self._loop = loop

    @property
    def _stack(self):
        return self._chain.list

    def solve(self):
        log("solving "+str(self._stack))
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
        #if self._loop.type == "Convoy":
        #   return self._stack.index(self._loop)
        return None

    def _resolve(self):
        if self._isMoveChain():
            log("this is a move chain, solving the first..")
            self._chain.proc.solve_force()
            self._chain.rem_last()
        elif self._getConvoyInChain() is not None:
            log("convoy chain detected, solving the convoy..")
            ## re-order chain
            i = self._getConvoyInChain()
            if i == 0:
                new_chain = [self._stack[i]]
            else:
                new_chain = self._stack[0:1]
                new_chain.append(self._stack[i])
            #new_chain = []
            #for j in self._stack[:i]:
            #   new_chain.append(j)
            #for j in self._stack[i+1:]:
            #   new_chain.append(j)
            #new_chain.append(self._stack[i])
            self._chain._stack = new_chain
            ## Convoy's solve force follow the Szykman law which states that
            ## the unit being convoyed is unsuccessful, and has no influence
            ## over the territory it is being convoyed to.
            self._chain.proc.solve_force()
            self._chain.rem_last()
        else:
            log("ERROR, I don't know how to solve this.")
            self._chain._stack = []
