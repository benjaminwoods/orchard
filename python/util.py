class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super().__get__(objtype)
    def __set__(self, obj, value):
        super().__set__(type(obj), value)
    def __delete__(self, obj):
        super().__delete__(type(obj))

class Children(list):
    def __init__(self, iterable=(), childType=None):
        supercls = self.__class__.__mro__[1]

        l = supercls.__call__(iterable)

        for i in l:
            if not isinstance(l, childType):
                raise TypeError('Children not all of compatible type.')

        super().__init__(l)
        self._childType = childType

    def __setitem__(self, key, value):
        self._verify(value)
        super().__setitem__(key, value)

    def append(self, object):
        self._verify(object)
        super().append(object)

    def extend(self, iterable):
        def _genr(iterable):
            # Generator to save a bit off memory
            for i in iterable:
                self._verify(i)
                yield i

        super().extend(_genr(iterable))

    def insert(self, index, object):
        self._verify(object)
        super().insert(index, object)

    def _verify(self, value):
        if not isinstance(value, self._childType):
            raise TypeError(
                f'Value {value} not of compatible type {self._childType}.'
            )
