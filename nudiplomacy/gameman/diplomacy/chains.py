import time
from .exceptions import ChainloopException
from .paradoxes import Paradox


class Chain(object):
    def __init__(self, adjudicator):
        self._adj = adjudicator
        self._stack = []
        self._paradox = None

    def log(self, msg):
        msg = "[Chain] "+msg+"\n"
        self._adj._logstack += msg

    @property
    def list(self):
        return self._stack

    @property
    def proc(self):
        return self._stack[-1]

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
            t_sub = time.time()
            paradox = (False, None)
            while self.list:
                self.log("processing member "+str(self.proc))
                self.proc.solve()
                if not self.proc.solved:
                    self.log("unsolved dependency for "+str(self.proc))
                    #: paradox-loop eval
                    if self.proc.depends in self.list:
                        paradox = (True, self.proc.depends)
                        break
                    self.add(self.proc.depends)
                else:
                    self.log(str(self.proc)+" solved.")
                    self.rem_last()
                #: This is an ultra-safe loop check (500ms time limit)
                #  We should never get this
                t_now = time.time()
                if round((t_now-t_sub)*1000) > 500:
                    self.log("ERROR: breaking SUB, too slow.")
                    raise ChainloopException('step', self)
            if paradox[0]:
                self._paradox = Paradox(self, paradox[1])
                self.log("found PARADOX "+str(self.list))
                self.log("paradox stuck on "+str(self.proc.depends))
                self._paradox.solve()
                self._paradox = None
            else:
                solvedNode = True
            #: Safe loop check (2s time limit)
            #  We should never get this
            t_now = time.time()
            if round((t_now-t_start)*1000) > 2000:
                self.log("ERROR: breaking MAIN, too slow.")
                raise ChainloopException('main', self)
