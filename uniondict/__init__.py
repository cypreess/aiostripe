# coding: utf8

_missing = object()


class uniondict(dict):
    def __init__(self, *targets, overlay=None, whiteouts=None):
        super().__init__()

        if len(targets) == 0:
            raise ValueError('must provide at least one target')

        for target in targets:
            if not isinstance(target, dict):
                raise TypeError('targets should be dicts')

        if overlay is None:
            overlay = {}

        if whiteouts is None:
            whiteouts = set()

        if not isinstance(overlay, dict):
            raise TypeError('overlay should be dict')

        if not isinstance(whiteouts, set):
            raise TypeError('whiteouts should be set')

        self.targets = targets
        self.__reversed_targets = tuple(reversed(targets))
        self.overlay = overlay
        self.whiteouts = whiteouts

    def __locate_key(self, key):
        if key in self.whiteouts:
            return 'whiteouts'

        if key in self.overlay:
            return 'overlay'

        for target in self.__reversed_targets:
            if key in target:
                return 'target'

        return None

    def __getitem__(self, key):
        value = self.get(key, _missing)

        if value is _missing:
            raise KeyError(key)

        return value

    def __setitem__(self, key, value):
        self.whiteouts.discard(key)
        self.overlay[key] = value

    def __delitem__(self, key):
        location = self.__locate_key(key)
        if location == 'whiteouts':
            raise KeyError(key)
        elif location == 'overlay':
            del self.overlay[key]
            return
        elif location == 'target':
            self.whiteouts.add(key)
            return
        else:
            raise KeyError(key)

    def __contains__(self, key):
        location = self.__locate_key(key)

        if location == 'whiteouts':
            return False
        elif location == 'overlay':
            return True
        elif location == 'target':
            return True
        else:
            return False

    def __eq__(self, other):
        if not isinstance(other, dict):
            return False

        if set(self.keys()) != set(other.keys()):
            return False

        for k, v in self.items():
            if v != other[k]:
                return False

        return True

    __hash__ = None

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(set(self.keys()))

    def __repr__(self):
        targets = '+'.join(map(repr, self.targets))
        return '%r+%r-%r' % (targets, self.overlay, self.whiteouts)

    def __str__(self):
        return repr(self.copy())

    def update(self, other=None, **kwargs):
        if other is not None:
            if isinstance(other, dict):
                other = other.items()

            for key, value in other:
                self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def clear(self):
        self.overlay.clear()
        self.whiteouts.clear()

    def copy(self):
        res = {}
        for target in self.targets:
            res.update(target)

        res.update(self.overlay)

        for x in self.whiteouts:
            del res[x]

        return res

    def get(self, key, default=None):
        if key in self.whiteouts:
            return default

        value = self.overlay.get(key, _missing)
        if value is not _missing:
            return value

        for target in self.__reversed_targets:
            value = target.get(key, _missing)
            if value is not _missing:
                return value

        return default

    def keys(self):
        keys = set()

        for target in self.targets:
            keys.update(target.keys())

        keys.update(self.overlay.keys())
        for key in self.whiteouts:
            keys.discard(key)

        yield from keys

    def values(self):
        for k in self.keys():
            yield self[k]

    def items(self):
        for k in self.keys():
            yield k, self[k]

    def setdefault(self, key, default=None):
        value = self.get(key, _missing)

        if value is _missing:
            value = self[key] = default

        return value

    def pop(self, key, default=_missing):
        value = self.get(key, _missing)

        if value is not _missing:
            del self[key]
            return value

        if default is _missing:
            raise KeyError(key)

        return default

    def popitem(self):
        if not len(self):
            raise KeyError('popitem(): union dictionary is empty')

        key = set(self.keys()).pop()
        value = self.pop(key)

        return key, value

__all__ = ['uniondict']
