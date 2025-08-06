from __future__ import annotations
from typing import Any, Dict, Optional, Union
import json
import logging
from enum import Enum
from . import errors
from .base import TABLE_REGISTRY
from dataclasses import dataclass
from typing import TYPE_CHECKING
logger = logger = logging.getLogger("piscesORM")

if TYPE_CHECKING:
    from .table import Table

class Column:
    type:str = ""
    primary_key = False
    not_null = False
    auto_increment = False
    unique = False
    default:Any = None
    index:bool = False
    
    def __init__(self, type:str|dict[str, str], primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool = False):
        self.type = type
        self.primary_key = primary_key
        self.not_null = not_null
        self.auto_increment = auto_increment
        self.unique = unique
        self.default = self.normalize_default(default)
        self.index = index

        self._type = type if isinstance(type, dict) else {"sqlite": type, "mysql": type}

    def get_type(self, dialect: str) -> str:
        return self._type.get(dialect, self._type["sqlite"])
        

    def to_db(self, value: Any) -> Any:
        return value

    def from_db(self, value: Any) -> Any:
        return value
    
    def normalize_default(self, default: Any) -> Any:
        return default

class Integer(Column):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("INTEGER", primary_key, not_null, auto_increment, unique, default, index)
    
class Text(Column):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("TEXT", primary_key, not_null, auto_increment, unique, default, index)

class Blob(Column):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("BLOB", primary_key, not_null, auto_increment, unique, default, index)

class Real(Column):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("REAL", primary_key, not_null, auto_increment, unique, default, index)

class Numeric(Column):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("NUMERIC", primary_key, not_null, auto_increment, unique, default, index)

class Boolean(Column):
    def __init__(self, primary_key = False, not_null = False, auto_increment = False, unique = False, default = None, index = False):
        super().__init__("INTEGER", primary_key, not_null, auto_increment, unique, default, index)

    def to_db(self, value):
        return int(value)
    
    def from_db(self, value):
        return bool(value)

class Json(Column):
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

class StringArray(Column):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("TEXT", primary_key, not_null, auto_increment, unique, default, index)

    def to_db(self, value:list[str]):
        return ",".join(value) if value else ""

    def from_db(self, value:str):
        return value.split(",") if value else []

class IntegerArray(Column):
    def __init__(self, primary_key:bool=False, not_null:bool=False, auto_increment:bool=False, unique:bool=False, default:Any=None, index:bool=False):
        super().__init__("TEXT", primary_key, not_null, auto_increment, unique, default, index)

    def to_db(self, value:list[int]):
        return ",".join(map(str, value)) if value else ""

    def from_db(self, value:str):
        return list(map(int, value.split(","))) if value else []
    
class EnumType(Column):
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
    
class EnumArray(Column):
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
            return ""
        try:
            if self.store_as_value:
                return ",".join(str(v.value) for v in value)
            else:
                return ",".join(v.name for v in value)
        except KeyError as e:
            logger.error(f"EnumArray from_db error: {e}")
    
    def from_db(self, value):
        if not value:
            return []
        try:
            items = value.split(",")
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