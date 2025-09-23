from __future__ import annotations
from typing import Any, Dict
import json
import logging
from enum import Enum, IntEnum, IntFlag, StrEnum
from .. import errors
from ..ptime import PiscesTime
from . import Column
import traceback
from datetime import datetime
logger = logger = logging.getLogger("piscesORM")

class Boolean(Column[bool]):
    def __init__(self, primary_key = False, not_null = False, auto_increment = False, unique = False, default = None, index = False):
        super().__init__("INTEGER", primary_key, not_null, auto_increment, unique, default, index)

    def to_db(self, value):
        return int(value)
    
    def from_db(self, value):
        return bool(value)

class Json(Column[dict]):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("TEXT", primary_key, not_null, auto_increment, unique, default, index)

    def to_db(self, value: Any) -> Any:
        return json.dumps(value)

    def from_db(self, value: Any) -> Any:
        return json.loads(value)
    
    def normalize_default(self, default:str|Dict):
        if default is not None:
            if isinstance(default, str):
                try:
                    return json.loads(default)
                except Exception:
                    raise errors.IllegalDefaultValue("Invalid default for Json column")
            elif not isinstance(default, dict):
                return errors.IllegalDefaultValue("Json Type default only support dict and json string")
        if self.not_null:
            return {}
        return default

class Array(Column[list[Any]]):
    """
    It's a array that support by python json. those type whose support by json.dump() can be support by this.
    - enum: 
        - this is a special function that can auto store into enum.
        - If you use this, you need to make shure all value are in the enum. 
        - no mix enums support.
    """
    def __init__(self, enum:IntEnum|StrEnum|IntFlag=None, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("TEXT", primary_key, not_null, auto_increment, unique, default, index)
        self.enum = enum

    def to_db(self, value:list[Any]):
        if value is None:
            return None
        result = json.dumps(value)
        if self.enum is not None:
            return [self.enum(v) for v in result]
        return result

    def from_db(self, value:str):
        if not value:
            return []
        return json.loads(value)

    
class EnumType(Column[Enum]):
    """
    
    
    """
    def __init__(self, enum:Enum, store_as_value:bool=False, org_type:Any=None, 
                 primary_key = False, not_null = False, auto_increment = False, 
                 unique = False, default = None, index = False):
        if store_as_value and org_type is None:
            raise errors.IllegalDefaultValue("EnumType requires org_type when store_as_value is True")
        if default is not None:
            if not isinstance(default, enum):
                raise errors.IllegalDefaultValue("default isn't match enum")
            
        self.enum = enum
        self.store_as_value = store_as_value
        self.org_type = org_type

        super().__init__("TEXT", primary_key, not_null, auto_increment, unique, default, index)
        
    def to_db(self, value:type[Enum]):
        if value is None:
            return ""
        try:
            return value.value if self.store_as_value else value.name
        except Exception as e:
            logger.error(f"EnumType to_db error: {e}")

    def from_db(self, value:Any):
        if not value:
            return None
        try:
            if self.store_as_value:
                return self.enum(self.org_type(value))
            return self.enum[value]
        except Exception as e:
            logger.error(f"EnumArray from_db error: {e}")
    
class EnumArray(Column[list[Enum]]):
    """
    If the enum value only is `int` or `str`, the basic `Array` is a better choise.\n
    EnumArray not support mixing enum, also is for Array.
    """
    def __init__(self, enum:Enum, store_as_value:bool = False, org_type:Any = None, 
                 primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, 
                 unique:bool=False, default:Any=None, index:bool=None):
        if store_as_value and org_type is None:
            raise errors.IllegalDefaultValue("EnumArray requires org_type when store_as_value is True")
        
        
        self.enum = enum
        self.store_as_value = store_as_value
        self.org_type = org_type

        super().__init__("TEXT", primary_key, not_null, auto_increment, unique, default, index)
        
    def to_db(self, value):
        if value is None:
            return None
        try:
            if self.store_as_value:
                return json.dumps([v.value for v in value])
            else:
                return json.dumps([v.name for v in value])
        except KeyError as e:
            logger.error(f"EnumArray from_db error: {e}")
    
    def from_db(self, value):
        if not value:
            return []
        try:
            items = json.loads(value)
            if self.store_as_value:
                return [self.enum(self.org_type(v)) for v in items]
            else:
                return [self.enum[v] for v in items]
        except KeyError as e:
            logger.error(f"EnumArray from_db error: {e}")

    def normalize_default(self, default:list[type[Enum]]):
        if default is not None:
            if not isinstance(default, list) or not all(isinstance(v, self.enum) for v in default):
                raise errors.IllegalDefaultValue("default must be a list of Enum members")
            if self.store_as_value:
                default = ",".join(str(v.value) for v in default)
            else:
                default = ",".join(v.name for v in default)

class Time(Column[PiscesTime]):
    def __init__(self, primary_key=False, not_null=False, auto_increment=False, unique=False, default=None, index=False):
        super().__init__("DATETIME", primary_key, not_null, auto_increment, unique, default, index)

    def to_db(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
                return PiscesTime.fromtimestamp(value).to_database()
        if isinstance(value, PiscesTime):
            return value.to_database()
        if isinstance(value, datetime):
            return PiscesTime.from_datetime(value).to_database()
        raise ValueError("the value of time only support int/float/datetime/PiscesTime")
    
    def from_db(self, value:str|None):
        if not value:
            return PiscesTime.fromtimestamp(0)
        return PiscesTime.from_database(value)
    
    def normalize_default(self, default:int|float|datetime|PiscesTime|None):
        if default is not None:
            if isinstance(default, (int, float)):
                return PiscesTime.fromtimestamp(default)
            if isinstance(default, datetime):
                return PiscesTime.from_datetime(default)
            return default
        
    @staticmethod
    def _format_time(value):
        if isinstance(value, (int, float)):
            return PiscesTime.fromtimestamp(value).to_database()
        elif isinstance(value, PiscesTime):
            return value.to_database()
        elif isinstance(value, datetime):
            return PiscesTime.from_datetime(value).to_database()
        raise ValueError("only support int/float/datetime/PiscesTime")

        
    def __eq__(self, value):
        return super().__eq__(self._format_time(value))
    
    def __ne__(self, value):
        return super().__ne__(self._format_time(value))
    
    def __ge__(self, value):
        return super().__ge__(self._format_time(value))
    
    def __gt__(self, value):
        return super().__gt__(self._format_time(value))
    
    def __le__(self, value):
        return super().__le__(self._format_time(value))
    
    def __lt__(self, value):
        return super().__lt__(self._format_time(value))