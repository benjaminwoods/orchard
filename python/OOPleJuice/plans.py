from collections.abc import MutableMapping

from .abc import BasePlan, BaseStructure, BaseDirective
from . import directives

class Plan(BasePlan):
    _childType = BaseDirective

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Defs is always defined
        isdefs = False
        for c in self.children:
            if isinstance(c, directives.Defs):
                isdefs = True
                break
        if not isdefs:
            self.children.append(directives.Defs('defs', []))

        # Compiled is always defined
        iscompiled = False
        for c in self.children:
            if isinstance(c, directives.Compiled):
                iscompiled = True
                break
        if not isdefs:
            self.children.append(directives.Compiled('compiled', []))

    @classmethod
    def validate(cls, d):
        pass

    def serialize(self):
        def _dictmap(d):
            for k,v in d.items():
                if isinstance(v, BaseModel):
                    yield k,v.serialize()
                else:
                    yield k,v

        d = {}
        for c in self.children:
            if not isinstance(c, directives.Compiled):
                d.update(c.serialize())
        d.update(dict(_dictmap(self.exts)))
        return d

    @classmethod
    def deserialize(cls, d, validate=True, **kwargs):
        if validate:
            cls.validate(d)

        if isinstance(d, MutableMapping):
            # Unpack exts
            # {'ext1': ext1, ...}}
            exts = {k:d[k] for k in cls._extNames if k in d}

            # Create new instance, self
            # (child's parentNode)
            self = cls.__call__(
                name='untitledPlan',
                children=[],
                parentNode=None,
                **exts
            )

            if 'defs' in d:
                # Do Defs first
                subType = directives.Defs

                for c in self.children:
                    if c.name == 'defs':
                        self.children.remove(c)
                        break

                # Take care to use append to preserve the id of children
                self.children.append(
                    subType.deserialize(
                        {'defs':d['defs']},
                        validate=False,
                        parentNode=self
                    )
                )

            for k,v in d.items():
                if k not in (cls._extNames + ['defs']):
                    subType = getattr(directives, k.title())

                    # Take care to use append to preserve the id of children
                    self.children.append(
                        subType.deserialize(
                            {k:v},
                            validate=False,
                            parentNode=self
                        )
                    )

            return self
        else:
            return d
