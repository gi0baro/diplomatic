# -*- coding: utf-8 -*-

import time
from .exceptions import ChainloopException
from .paradoxes import Paradox


class Chain(object):
    def __init__(self, judge):
        self.judge = judge
        self.stack = []

    def log(self, msg):
        msg = "[Chain] " + msg
        self.judge._logstack.append(msg)

    @property
    def list(self):
        return self.stack

    @property
    def current_node(self):
        return self.stack[-1]

    def add(self, node):
        self.stack.append(node)

    def rem(self, node):
        self.stack.remove(node)

    def rem_last(self):
        self.stack.pop()

    def resolve(self):
        t_start = time.time()
        solved_node = False
        while not solved_node:
            t_sub = time.time()
            in_loop = False
            found_paradox = False
            while self.stack:
                print(self.stack)
                self.log("processing member {}".format(self.current_node))
                self.current_node.resolve()
                if not self.current_node.solved:
                    self.log("unsolved dependency for {}".format(self.current_node))
                    #: paradox-loop eval
                    if self.current_node.depends_on in self.stack:
                        if in_loop:
                            self.rem_last()
                            found_paradox = True
                            break
                        print('re-looping')
                        in_loop = True
                    else:
                        print('continuing with deps')
                        in_loop = False
                    self.add(self.current_node.depends_on)
                else:
                    self.log("{} solved.".format(self.current_node))
                    self.rem_last()
                #: This is an ultra-safe loop check (500ms time limit)
                #  We should never get this
                t_now = time.time()
                if round((t_now-t_sub)*1000) > 500:
                    self.log("ERROR: breaking SUB, too slow.")
                    raise ChainloopException('step', self)
            if found_paradox:
                paradox = Paradox(self)
                self.log("found PARADOX {}".format(self.stack))
                self.log("paradox stuck on {}".format(self.current_node.depends_on))
                paradox.resolve()
                del paradox
                in_loop = False
            else:
                solved_node = True
            #: Safe loop check (2s time limit)
            #  We should never get this
            t_now = time.time()
            if round((t_now-t_start)*1000) > 2000:
                self.log("ERROR: breaking MAIN, too slow.")
                raise ChainloopException('main', self)
