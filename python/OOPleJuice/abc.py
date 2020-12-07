from abc import ABC, abstractmethod
import json
from collections.abc import MutableMapping
from copy import deepcopy

from ..util import classproperty, Children

# !!! Register in Plan if a plan exists when deserializing
# !!! Check for unique in defs
# !!! Prevent modifying children in weird ways (currently you can add one
# !!!   which is not of the child type)

class BaseModel(ABC):
    _extNames = []
    def __init__(self, name, children, parentNode=None, **exts):
        self.name = name
        self.children = Children(children, self._childType)
        self.parentNode = parentNode
        self.exts = exts

    def serialize(self):
        def _listmap(l):
            for item in l:
                if isinstance(item, BaseModel):
                    yield item.serialize()
                else:
                    yield item
        def _dictmap(d):
            for k,v in d.items():
                if isinstance(v, BaseModel):
                    yield k,v.serialize()
                else:
                    yield k,v

        d = {self.name: list(_listmap(self.children))}
        d.update(dict(_dictmap(self.exts)))
        return d

    @property
    def fqn(self):
        """Fully qualified name."""
        name = self.name
        parentNode = self.parentNode
        while True:
            if parentNode is not None:
                name = '.'.join((parentNode.name, name))
                parentNode = parentNode.parentNode
            else:
                return name

    @classmethod
    def deserialize(cls, d, validate=True, **kwargs):
        if validate:
            cls.validate(d)

        if isinstance(d, MutableMapping):
            # Get parentNode of self
            parentNode = kwargs.get('parentNode')

            # Unpack exts, name, items
            # {'name': items, **exts}
            exts = {k:d[k] for k in cls._extNames if k in d}
            for k in d:
                if k not in cls._extNames:
                    name, items = k, d[k]
                    break

            # Create new instance, self
            # (child's parentNode)
            self = cls.__call__(name, children=[], parentNode=parentNode, **exts)

            # !!! Add polymorphic handling for [] or {'items': items, ...}
            if issubclass(self._childType, BaseModel):
                for item in items:
                    # Take care to use append to preserve the id of children

                    # linking up obj as the parentNode
                    self.children.append(
                        self._childType.deserialize(
                            item,
                            validate=False,
                            parentNode=self
                        )
                    )
            else:
                self.children.extend(items)

            return self
        else:
            return d

    @classmethod
    @abstractmethod
    def validate(cls, d):
        pass

    def __str__(self):
        return json.dumps(self.serialize())

    def __eq__(self, other):
        if type(self) == type(other):
            return self.children == self.children
        else:
            return super().__eq__(other)

    def __repr__(self):
        cls = self.__class__
        name = self.name
        parentNode = self.parentNode.name if self.parentNode is not None else None
        return f"{cls.__name__}(name={name}, parentNode={parentNode})"

    @classproperty
    @abstractmethod
    def _childType(cls):
        pass

    def __getitem__(self, item):
        spl = item.split('.')
        for c in self.children:
            if isinstance(c, BaseModel):
                if c.name == spl[0]:
                    if len(spl) == 1:
                        return c
                    else:
                        return c['.'.join(spl[1:])]
        raise KeyError(f'item {item} not found in {self.fqn}')

class BaseStructure(BaseModel):
    @classproperty
    def _extNames(cls):
        return BaseModel._extNames + ['type', 'properties']

    def _getplan(self, maxdepth=10):
        p = self.parentNode
        for i in range(maxdepth):
            if isinstance(p, BasePlan):
                return p
            else:
                p = p.parentNode
        raise Exception(f'maxdepth ({maxdepth}) exceeded.')

    def register(self):
        plan = self._getplan()
        plan.defs[self.fqn] = self
        print(plan.defs)

    def __repr__(self):
        cls = self.__class__
        name = self.name
        parentNode = self.parentNode.name if self.parentNode is not None else None
        return f"{cls.__name__}(name={name}, parentNode={parentNode})"

class BaseAction(BaseModel):
    _childType = BaseStructure

    @classproperty
    def _extNames(cls):
        return BaseModel._extNames + ['parent']

    @classmethod
    @abstractmethod
    def deserialize(cls, d, validate=True, **kwargs):
        # Needs to be subclassed as Action uses Defs, but this is
        # extensible
        pass


class BaseDirective(BaseModel):
    pass

class BasePlan(BaseModel):
    _cache = {}

    def __getattr__(self, attr):
        # Caching for speed
        if (self.children == self._cache.get('children', None)
            and self._cache.get(attr, None) is not None):
            # Do an identity equality check against cache
            return self._cache[attr]
        else:
            # If the children have been modified,
            # cache the new children and update all attr in the cache.
            self._cache['children'] = self.children
            for c in self.children:
                self._cache[c.name] = c

            return self._cache[attr]

    @abstractmethod
    def serialize(self):
        # Serialization depends on directives
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, d, validate=True, **kwargs):
        # Needs to be subclassed as BasePlan has a different JuiceON
        # metastructure
        pass

    def __repr__(self):
        cls = self.__class__
        name = self.name
        return f"{cls.__name__}(name={name})"

    def run(self):
        pass
