import time
from ._glob import G
from .paradoxes import Paradox

log = lambda x: G['logger']("[Chain] "+x)


class Chain(object):
    def __init__(self):
        self._stack = []
        self._paradox = None

    @property
    def list(self):
        return self._stack

    @property
    def proc(self):
        return self._stack[-1]

    #@property
    #def has_paradox(self):
    #   return self._paradox is not None

    #@property
    #def paradox(self):
    #   return self._paradox

    def new(self, start):
        self.add(start)

    def add(self, node):
        self._stack.append(node)

    def rem(self, node):
        self._stack.remove(node)

    def rem_last(self):
        self._stack.pop()

    def solve(self):
        t_start = time.time()
        solvedNode = False
        while not solvedNode:
            paradox = (False, None)
            while self.list:
                log("processing member "+str(self.proc))
                self.proc.solve()
                if not self.proc.solved:
                    log("unsolved dependency for "+str(self.proc))
                    ## looping failure check
                    if self.proc.depends in self.list:
                        paradox = (True, self.proc.depends)
                        break
                    self.add(self.proc.depends)
                else:
                    log(str(self.proc)+" solved.")
                    self.rem_last()
                ## ultra-safe loop check
                ## we shouldn't need this
                t_now = time.time()
                if round((t_now-t_start)*1000) > 500:
                    log("ERROR: breaking SUB, too slow.")
                    break
            if paradox[0]:
                self._paradox = Paradox(self, paradox[1])
                log("found PARADOX "+str(self.list))
                log("paradox stuck on "+str(self.proc.depends))
                self._paradox.solve()
                self._paradox = None
            else:
                #self._paradox = None
                solvedNode = True
            ## safe loop check
            t_now = time.time()
            if round((t_now-t_start)*1000) > 500:
                log("ERROR: breaking MAIN, too slow.")
                break
