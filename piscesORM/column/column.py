from __future__ import annotations
from typing import Any, TypeVar, Generic
import logging
from .. import operator
logger = logger = logging.getLogger("piscesORM")

T = TypeVar('_T')

class Column(Generic[T]):
    """
    The basic Column of a table.

    Args:

        type: the type of str.
            - str: global type.
            - dict: you can select sql type in different database.
            - support:"sqlite"

        primary_key: 

        not_null

        auto_increment

        unique

        default

        index
    """
    def __init__(self, type: str|dict[str, str], primary_key=False, not_null=False,
                 auto_increment=False, unique=False, default=None, index=False):
        self._type = type if isinstance(type, dict) else {"sqlite": type, "mysql": type}
        self.primary_key = primary_key
        self.not_null = not_null
        self.auto_increment = auto_increment
        self.unique = unique
        self.default = self.normalize_default(default)
        self.index = index
        self._name = None

        self._name: str|None = None  # 欄位名稱

    def __set_name__(self, owner, name: str):
        self._name = name
    
        
    def to_db(self, value: Any) -> Any:
        return value

    def from_db(self, value: Any) -> Any:
        return value

    def normalize_default(self, default: Any) -> Any:
        return default
    

    # 條件運算子
    def equal(self, value):
        return operator.Equal(self, value)
    
    def not_equal(self, value):
        return operator.NotEqual(self, value)

    def greater_than(self, value):
        return operator.GreaterThan(self, value)

    def greater_equal(self, value):
        return operator.GreaterEqual(self, value)
    
    def less_than(self, value):
        return operator.LessThan(self, value)
    
    def less_equal(self, value):
        return operator.LessEqual(self, value)
    
    def in_(self, value):
        return operator.IsIn(self, value)
    
    def like(self, value):
        return operator.Like(self, value)
    
    def ilike(self, value):
        return operator.ILike(self, value)
    

    # 快速調用 (特殊方法)
    def __eq__(self, value):
        return self.equal(value)
    
    def __ne__(self, value):
        return self.not_equal(value)
        
    def __gt__(self, value):
        return self.greater_than(value)
        
    def __ge__(self, value):
        return self.greater_equal(value)
    
    def __lt__(self, value):
        return self.less_than(value)
        
    def __le__(self, value):
        return self.less_equal(value)
        
    def __contains__(self, value):
        return self.in_(value)
    
    def __or__(self, value):
        return operator.OR(self, value)

    def __and__(self, value):
        return operator.AND(self, value)
    
    def __add__(self, value):
        return operator.Plus(self, value)
    
    def __sub__(self, value):
        return operator.Minus(self, value)
    
    def __mul__(self, value):
        return operator.Multiply(self, value)
    
    def __truediv__(self, value):
        return operator.Divide(self, value)
    
    def __mod__(self, value):
        return operator.Modulo(self, value)
    
    def __pow__(self, value):
        return operator.Power(self, value)