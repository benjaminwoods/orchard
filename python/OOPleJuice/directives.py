from collections.abc import MutableMapping

from .abc import BaseDirective, BaseModel
from . import actions, structures

class Do(BaseDirective):
    _childType = actions.CRUD

    def validate(d):
        pass

class Defs(BaseDirective):
    _childType = object
    # !!! redo serialize method to account for $Orchard
    # !!! filter out registered objects for str()
    # !!! actually include registered objects...

    def serialize(self):
        def _listmap(l):
            for item in l:
                if isinstance(item, BaseModel):
                    yield {item.name: f'${item.__class__.__name__}'}
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

    @classmethod
    def deserialize(cls, d, validate=True, **kwargs):
        if validate:
            cls.validate(d)

        if isinstance(d, MutableMapping):
            # Get parentNode of self
            parentNode = kwargs.get('parentNode')

            # Unpack
            # {'name': items, 'type': type, ...}}
            exts = {k:d[k] for k in cls._extNames if k in d}
            for k in d:
                if k not in cls._extNames:
                    name, dikt = k, d[k]
                    break

            # Create new instance, self
            # (child's parentNode)
            self = cls.__call__(name, children=[], parentNode=parentNode, **exts)

            for k,v in dikt.items():
                if isinstance(v, str):
                    if v[0] == "$":
                        # Create an instance
                        structureType = getattr(structures, v[1:])

                        # Take care to use append to preserve the id of children
                        self.children.append(
                            structureType.__call__(
                                k,
                                children=[],
                                parentNode=self
                            )
                        )
                else:
                    self.children.append(v)

            return self
        else:
            return d

    @classmethod
    def validate(cls, d):
        pass

class Compiled(Defs):
    @classmethod
    def validate(cls, d):
        raise ValueError(
            'Invalid schema (no deserialization possible for Compiled)'
        )

    def serialize(self):
        def _listmap(tokens):
            for t in tokens:
                if isinstance(t[1], BaseModel):
                    _, _l = iter(*t[1].serialize().items())
                    yield {t[0]: _l}
                else:
                    yield {t[0]: t[1]}
        def _dictmap(d):
            for k,v in d.items():
                if isinstance(v, BaseModel):
                    yield k,v.serialize()
                else:
                    yield k,v

        d = {self.name: []}
        for da, tokens in self.children:
            d[self.name].append({da: list(_listmap(tokens))})
        d.update(dict(_dictmap(self.exts)))
        return d
