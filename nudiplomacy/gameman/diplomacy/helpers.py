

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
        self.registry[name](*args, **kwargs)
