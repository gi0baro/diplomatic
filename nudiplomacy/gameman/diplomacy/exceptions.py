# -*- coding: utf-8 -*-


class ParadoxException(Exception):
    def __init__(self, stack):
        self.stack = stack
        Exception.__init__(self)

    def __str__(self):
        return "Uknown paradox type for chain: "+str(self.stack)


class ChainloopException(Exception):
    def __init__(self, cycle, stack):
        self.cycle = cycle
        self.stack = stack
        Exception.__init__(self)

    def __str__(self):
        return "Chain loop too slow on "+self.cycle+": "+str(self.stack)
