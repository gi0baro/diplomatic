# -*- coding: utf-8 -*-


class adict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class cachedprop(object):
    #: a read-only @property that is only evaluated once.
    def __init__(self, fget, doc=None, name=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = name or fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result


class registry(object):
    __slots__ = ('registry')

    def __init__(self):
        self.registry = {}

    def register(self, name):
        def wrap(method):
            self.registry[name] = method
            return method
        return wrap

    def call(self, name, *args, **kwargs):
        return self.registry[name](*args, **kwargs)
