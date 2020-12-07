from collections.abc import MutableMapping

from .abc import BaseAction, BaseModel, BaseStructure

class CRUD(BaseAction):
    @classmethod
    def validate(cls, d):
        pass

    def run(self):
        pass

    @classmethod
    def deserialize(cls, d, validate=True, **kwargs):
        if validate:
            cls.validate(d)

        if isinstance(d, MutableMapping):
            # Get parentNode of self
            parentNode = kwargs.get('parentNode')

            # Get name of directive
            directive = parentNode.name

            # Unpack
            # {'name': items, 'type': type, ...}}
            exts = {k:d[k] for k in cls._extNames if k in d}
            for k in d:
                if k not in cls._extNames:
                    name, items = k, d[k]
                    break

            # Create new instance, self
            self = cls.__call__(name, children=[], parentNode=parentNode, **exts)

            # Creating an Action under a Plan
            plan = parentNode.parentNode

            # Get child's parentNode from defs
            try:
                obj = plan.defs[d['parent']]
            except KeyError:
                for _, tokens in plan.compiled.children:
                    for t in tokens:
                        if t[0] == d['parent']:
                            obj = t[1]
                            break

            # !!! Add polymorphic handling for [] or {'items': items, ...}
            if issubclass(obj._childType, BaseModel):
                # Serialize if it is a BaseModel subclass,
                # linking up obj as the parentNode
                for item in items:
                    self.children.append(
                        obj._childType.deserialize(
                            item,
                            validate=False,
                            parentNode=obj
                        )
                    )
            else:
                self.children.extend(items)

            if isinstance(obj, BaseStructure):
                # If the parent object is a structure, store in compiled

                # append: (!directive.action, [(name, structure)
                #               for c in children])
                plan.compiled.children.append(
                    (
                        f'!{directive}::{name}',
                        [
                            (f"{d['parent']}.{c.name}",c)
                            for c in self.children
                        ]
                    )
                )

            # Make self
            return self
        else:
            return d
