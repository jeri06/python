"""
Name:        helper
Purpose:

Author:      roma

Created:     01/04/2017
Copyright:   (c) arief 2017
Licence:     <your licence>
"""


class BaseExtension:
    __table__ = None

    def toDict(self, valuesAsObj=False):
        if valuesAsObj:
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}
        else:
            return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

    def __str__(self):
        return str(self.toDict())
