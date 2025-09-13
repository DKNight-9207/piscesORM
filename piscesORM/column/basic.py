from __future__ import annotations
from typing import Any
from decimal import Decimal
import logging
from enum import IntEnum, IntFlag, StrEnum
from . import Column
logger = logger = logging.getLogger("piscesORM")

class Integer(Column[int]):
    """
    default integer.
    - enum: if you wanna use `IntEnum` or `IntFlag` in this column. It can hendle it.
    """
    def __init__(self, enum:IntEnum|IntFlag = None, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("INTEGER", primary_key, not_null, auto_increment, unique, default, index)
        self.enum = enum

    def from_db(self, value):
        if self.enum is not None:
            return self.enum(value)
        return super().from_db(value)

class Text(Column[str]):
    def __init__(self, enum:StrEnum=None, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("TEXT", primary_key, not_null, auto_increment, unique, default, index)
        self.enum = enum

    def from_db(self, value):
        if self.enum is not None:
            return self.enum(value)
        return super().from_db(value)
    
class Blob(Column[bytes]):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("BLOB", primary_key, not_null, auto_increment, unique, default, index)

class Real(Column[float]):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("REAL", primary_key, not_null, auto_increment, unique, default, index)

class Numeric(Column[Decimal]):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("NUMERIC", primary_key, not_null, auto_increment, unique, default, index)

