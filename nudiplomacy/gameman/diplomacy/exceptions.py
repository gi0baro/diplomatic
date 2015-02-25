# -*- coding: utf-8 -*-


class ParadoxException(Exception):
    def __init__(self, paradox):
        self.stack = paradox._stack
        self.logstack = paradox._chain._adj._logstack
        Exception.__init__(self)

    def __str__(self):
        return "Uknown paradox type for chain: " + str(self.stack) + \
            "\nLog stack: \n" + self.logstack


class ChainloopException(Exception):
    def __init__(self, cycle, chain):
        self.cycle = cycle
        self.stack = chain._stack
        self.logstack = chain._adj._logstack
        Exception.__init__(self)

    def __str__(self):
        return "Chain loop too slow on "+self.cycle+": "+str(self.stack) + \
            "\nLog stack: \n"+self.logstack
