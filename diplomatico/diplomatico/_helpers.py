class Registry:
    __slots__ = ["_entries"]

    def __init__(self):
        self._entries = {}

    def register(self, key):
        def wrap(target):
            self._entries[key] = target
            return target
        return wrap

    def __call__(self, key, *args, **kwargs):
        return self._entries[key](*args, **kwargs)
