from __future__ import annotations
from typing import Any, Dict
import json
import logging
from enum import Enum
from . import errors
from .column import Column, Relationship, FieldRef
logger = logger = logging.getLogger("piscesORM")


class TableMeta(type):
    _registry = []

    def __new__(cls, name, bases, attrs):
        columns: Dict[str, Column] = {}
        relationship: Dict[str, Relationship] = {}
        indexes = []

        for key, value in attrs.items():
            if isinstance(value, Column):
                if key in errors.PROTECT_NAME:
                    raise errors.ProtectedColumnName(key)
                columns[key] = value
                if value.index:
                    indexes.append(key)
            elif isinstance(value, Relationship):
                if key in errors.PROTECT_NAME:
                    raise errors.ProtectedColumnName(key)
                relationship[key] = value


        attrs["_columns"] = columns
        attrs["_indexes"] = indexes
        attrs["_relationship"] = relationship
        attrs["_initialized"] = False

        new_cls = super().__new__(cls, name, bases, attrs)
        if not attrs.get("__abstract__", False):
            TableMeta._registry.append(new_cls)
        return new_cls

class Table(metaclass=TableMeta):
    __abstract__ = True
    __table_name__ = None
    __no_primary_key__ = False

    _columns:dict[str, Column]     # var_name: column
    _relationship:dict[str, Relationship]
    _indexes:list[str]             # var_name
    _edited:set[str]
    _initialized:bool              # init mark

    def __init__(self, **kwargs):
        self._edited = set()
        for name, column in self._columns.items():
            value = kwargs.get(name, column.default)
            setattr(self, name, value)

    def __setattr__(self, name, value):
        if hasattr(self, "_initialized") and self._initialized:
            if hasattr(self, "_columns") and name in self._columns:
                self._edited.add(name)
        super().__setattr__(name, value)

    def clear_edited_mark(self):
        self._edited.clear()

    def __str__(self):
        from textwrap import shorten

        table_name = self.__table_name__ or self.__class__.__name__
        lines = []
        lines.append(f"┌─ Table: {table_name} ─{'─' * (30 - len(table_name))}")
        lines.append("│ {:<15} {:<12} {:<30}".format("Column", "Type", "Value"))
        lines.append("├" + "─" * 60)

        for name, col in self._columns.items():
            value = getattr(self, name, None)
            value_str = str(value)
            if len(value_str) > 28:
                value_str = shorten(value_str, width=28, placeholder="...")

            edited_mark = "*" if name in self._edited else " "
            lines.append("│{:<1} {:<14} {:<12} {:<30}".format(
                edited_mark, name, col.__class__.__name__, value_str
            ))

        lines.append("└" + "─" * 60)
        return "\n".join(lines)
    
    def _get_pks(self):
        pk = [ v for v in self._columns.values() if v.primary_key]
        if not pk:
            pk = []
        return (self.__table_name__ or self.__class__.__name__, tuple(pk))
    
    def __hash__(self):
        return hash(self._get_pks())
    
    def __eq__(self, value):
        if isinstance(value, Table):
            return self._get_pks() == value._get_pks()
        return False
    
    def __ne__(self, value):
        return not self.__eq__(value)

    @classmethod
    def from_row(cls, row: dict):
        obj = cls()
        for key, column in cls._columns.items():
            if key in row:
                setattr(obj, key, column.from_db(row[key]))

        _rel = cls._relationship.copy()
        for name, rel in cls._relationship.items():
            if isinstance(rel, FieldRef):
                try:
                    _rel[name] = getattr(obj, rel.name)
                except AttributeError:
                    raise errors.NoSuchColumn(rel.name)
        obj._relationship = _rel
                

        return obj

    @classmethod
    def get_subclasses(cls):
        return TableMeta._registry

    @classmethod
    def get_primary_keys(cls) -> list[str]:
        return [name for name, col in cls._columns.items() if col.primary_key]
