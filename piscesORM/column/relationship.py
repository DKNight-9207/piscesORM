from __future__ import annotations
from typing import Union, TYPE_CHECKING
import logging
from .. import errors
from ..base import TABLE_REGISTRY
from ..operator.basic import *

if TYPE_CHECKING:
    from ..table import Table
    

logger = logger = logging.getLogger("piscesORM")

class Relationship:
    def __init__(self, table:Union[type["Table"], str], *filters, plural_data=False, **conditions):
        """
        - table: The class of table. The backup way is input the class name of table.
        - plural_data: allow
        - *filters: the suggest way to input. all item will be connected by 'AND'. Example: Table.column_1 >= 3
        - **conditions: the backup way to input to solute python cycle input. Example: column_1 = GreaterThen()
        """
        self.table = table
        self.obj = None
        self.plural_data = plural_data

        self.filters = filters
        self.conditions = conditions

    def get_table(self):
        if isinstance(self.table, str):
            t = TABLE_REGISTRY.get(self.table, None)
            if not t:
                raise errors.TableNotFound(self.table)
            return t
        return self.table
    
    def fix_filters(self):
        combined_filter = None
        if self.filters:
            for f in self.filters:
                if combined_filter is None:
                    combined_filter = f
                else:
                    combined_filter &= f
        if self.conditions:
            for c_first, c_second in self.conditions.items():
                if isinstance(c_second, Operator):
                    # normal: A == B -> Equal(A,B)
                    # here: A = Equal(B)
                    # fix: insert at first
                    op_cls = type(c_second)
                    fixed_op = op_cls(c_first, *c_second.parts)
                    combined_filter = fixed_op if combined_filter is None else combined_filter & fixed_op
                else:
                    if combined_filter is None:
                        combined_filter = Equal(getattr(self.get_table(), c_first), c_second)
                    else:
                        combined_filter &= Equal(getattr(self.get_table(), c_first), c_second)
                        
        return combined_filter


class FieldRef:
    def __init__(self, name:str):
        self.name = name