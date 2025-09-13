from __future__ import annotations
from typing import Any, TypeVar, Generic
import logging
from .. import LogicalOperator
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
        if T != TypeVar('_T'):
            self._python_type = T
        else:
            self._python_type = Any

    def __set_name__(self, owner, name: str):
        self._name = name

    def __set__(self, instance, value):
        if value is not None:
            self._check_type(value)
            value = self.to_db(value)
        instance.__dict__[self._name] = value
        instance._edited.add(self._name)

    def get_type(self, dialect: str) -> str:
        return self._type.get(dialect, self._type["sqlite"])
    
    def _check_type(self, value):
        if self._python_type is Any:
            return
        
        if not isinstance(value, self._python_type):
            raise TypeError(f"Value '{value}' must be of type {self._python_type}, not {type(value)}")
        
    def to_db(self, value: Any) -> Any:
        return value

    def from_db(self, value: Any) -> Any:
        return value

    def normalize_default(self, default: Any) -> Any:
        return default
    

    # 條件運算子
    def equal(self, value):
        return LogicalOperator.Equal(self._name, value)
    
    def not_equal(self, value):
        return LogicalOperator.NotEqual(self._name, value)

    def greater_than(self, value):
        return LogicalOperator.GreaterThan(self._name, value)

    def greater_equal(self, value):
        return LogicalOperator.GreaterEqual(self._name, value)
    
    def less_than(self, value):
        return LogicalOperator.LessThan(self._name, value)
    
    def less_equal(self, value):
        return LogicalOperator.LessEqual(self._name, value)
    
    def in_(self, value):
        return LogicalOperator.In_(self._name, value)
    
    def like(self, value):
        return LogicalOperator.Like(self._name, value)
    
    def ilike(self, value):
        return LogicalOperator.ILike(self._name, value)
    

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