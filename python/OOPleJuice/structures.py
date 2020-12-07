from .abc import BaseStructure

class Leaf(BaseStructure):
    _childType = object

    @classmethod
    def validate(cls, d):
        pass

class Branch(BaseStructure):
    _childType = Leaf

    @classmethod
    def validate(cls, d):
        pass

class Tree(BaseStructure):
    _childType = Branch

    @classmethod
    def validate(cls, d):
        pass

class Forest(BaseStructure):
    _childType = Tree

    @classmethod
    def validate(cls, d):
        pass

    def __getattribute__(self, attr):
        if attr in ('uri', 'client'):
            obj = self.exts.get(attr, None)
        else:
            obj = super().__getattribute__(attr)
        return obj

    def __setattribute__(self, attr, value):
        if attr in ('uri', 'client'):
            self.exts[attr] = value
        else:
            super().__setattribute__(attr, value)
