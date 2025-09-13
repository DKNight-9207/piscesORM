from __future__ import annotations
from typing import Union, TYPE_CHECKING
import logging
from .. import errors
from ..base import TABLE_REGISTRY

if TYPE_CHECKING:
    from ..table import Table
logger = logger = logging.getLogger("piscesORM")

class Relationship:
    def __init__(self, table:Union[type["Table"], str], plural_data=False, **filter):
        self.table = table
        self.plural_data = plural_data
        self.filter = filter

    def get_table(self):
        if isinstance(self.table, str):
            t = TABLE_REGISTRY.get(self.table, None)
            if not t:
                raise errors.TableNotFound(self.table)
            return t
        return self.table

class FieldRef:
    def __init__(self, name:str):
        self.name = name