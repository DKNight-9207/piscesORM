from __future__ import annotations
from typing import Type, Any, overload
from .table import Table
from .column import Column
import logging
from abc import ABC, abstractmethod
from . import errors
from . import operator
import warnings


class BasicGenerator(ABC):
    @staticmethod
    @abstractmethod
    def generate_create_table(table: Type[Table], exist_ok: bool = False) -> str:...

    @staticmethod
    @abstractmethod
    def generate_starcture(table: Type[Table]) -> str: ...

    @staticmethod
    @abstractmethod
    def generate_insert_column(table: Type[Table], org_starcture:dict) -> list[str]: ...

    @staticmethod
    @abstractmethod
    def generate_insert(obj: Table) -> tuple[str, tuple[Any]]: ...

    @staticmethod
    @abstractmethod
    def generate_update(obj: Table, merge:bool = True) -> tuple[str, tuple[Any]]: ...

    @staticmethod
    @abstractmethod
    def generate_delete(obj_or_table: Table|Type[Table], **filters) -> tuple[str, tuple[Any]]:
        """
        Delete records from the database.

        Args:
            obj_or_table (Table | Type[Table]): 
                - Table instance: Delete the record represented by the instance.
                - Table class: Delete records based on the provided filters.
            **filters: The rules for deletion.

        Returns:
            tuple[str, tuple[Any]]: SQL statement and values to execute.
        """
        pass

    @staticmethod
    @abstractmethod
    def generate_index(table: Type[Table]) -> list[str]: ...

    @staticmethod
    @abstractmethod
    def generate_drop(table: Type[Table]) -> str: ...

    @staticmethod
    @abstractmethod
    def generate_get_pk(table: Type[Table], **filters) -> tuple[str, tuple[Any]]: ...

    @staticmethod
    @abstractmethod
    def generate_select(table: Type[Table], **filters) -> tuple[str, list]: ...
    


class SQLiteGenerator(BasicGenerator):
    @staticmethod
    def generate_create_table(table, exist_ok = False):
        table_name = table.__table_name__ or table.__name__
        column_defs = []
        pk_fields = []

        for name, column in table._columns.items():
            parts = [name, column.type]

            # 這是 SQLite 的唯一合法形式：INTEGER PRIMARY KEY AUTOINCREMENT
            if column.primary_key and column.auto_increment and column.type == "INTEGER":
                parts.append("PRIMARY KEY AUTOINCREMENT")

            else:
                if column.not_null:
                    parts.append("NOT NULL")
                if column.unique:
                    parts.append("UNIQUE")      
                if column.default is not None:
                    parts.append(f"DEFAULT {repr(column.to_db(column.default))}")
            
            column_defs.append(" ".join(parts))

            if column.primary_key:
                pk_fields.append(name)

        if len(pk_fields) == 1:
            # 單一主鍵可以直接寫在欄位
            for i, name in enumerate(table._columns):
                col = table._columns[name]
                if col.primary_key:
                    column_defs[i] += " PRIMARY KEY"
        elif len(pk_fields) > 1:
            column_defs.append(f"PRIMARY KEY ({', '.join(pk_fields)})")
        elif not table.__no_primary_key__:
            warnings.warn(errors.NoPrimaryKeyWarning())

        columns_sql = ", ".join(column_defs)
        return f"CREATE TABLE {'IF NOT EXISTS' if exist_ok else ''} {table_name} ({columns_sql});"
    
    @staticmethod
    def generate_starcture(table):
        table_name = table.__table_name__ or table.__name__
        return f"PRAGMA table_info({table_name})"
    
    @staticmethod
    def generate_insert_column(table:Type[Table], org_starcture):
        table_name = table.__table_name__ or table.__name__
        missing_keys:set[str] = set(table._columns.keys()) - set(org_starcture)
        if missing_keys:
            sqls = []
            for col_name in missing_keys:
                column = table._columns[col_name]
                if column.primary_key:
                    raise errors.InsertPrimaryKeyColumn()
                
                col_type = column.type
                constraints = []
                if column.not_null:
                    constraints.append("NOT NULL")

                constraint_sql = " ".join(constraints)
                full_col_sql = f"{col_name} {col_type} {constraint_sql}".strip()
                sql = f"ALTER TABLE {table_name} ADD COLUMN {full_col_sql};"
                sqls.append(sql)
            return sqls
        return None

    @staticmethod
    def generate_insert(obj):
        table_name = obj.__table_name__ or obj.__class__.__name__
        column_names = []
        placeholders = []
        values = []

        for name, column in obj._columns.items():
            if column.auto_increment and column.primary_key:
                continue  # 忽略自增主鍵
            column_names.append(name)
            placeholders.append("?")
            value = getattr(obj, name, column.default)
            values.append(column.to_db(value))

        sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(placeholders)})"
        return sql, tuple(values)
    
    @staticmethod
    def generate_update(obj, merge = True):
        """merge: only edit change column"""
        table_name = obj.__table_name__ or obj.__class__.__name__
        set_parts = []
        set_values = []
        where_parts = []
        where_values = []

        if not obj.get_primary_keys():
            raise errors.NoPrimaryKeyError()

        for name, column in obj._columns.items():
            value = getattr(obj, name, column.default)
            if column.primary_key:
                where_parts.append(f"{name} = ?")
                where_values.append(column.to_db(value))
            elif not column.auto_increment:
                if merge or name in obj._edited:
                    set_parts.append(f"{name} = ?")
                    set_values.append(column.to_db(value))

        sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        return sql, tuple(set_values + where_values)
    
    @staticmethod
    def generate_delete(obj_or_table: Table|Type[Table], **filters):
        table_name = obj_or_table.__table_name__ or obj_or_table.__class__.__name__

        # delete by object
        if isinstance(obj_or_table, Table):
            obj = obj_or_table
            where_parts = []
            where_values = []

            for name, column in obj._columns.items():
                if column.primary_key:
                    value = getattr(obj, name, column.default)
                    where_parts.append(f"{name} = ?")
                    where_values.append(column.to_db(value))

            if not where_parts:
                raise ValueError("Cannot delete without a primary key.")

            sql = f"DELETE FROM {table_name} WHERE {' AND '.join(where_parts)}"
            return sql, tuple(where_values)
        else: # delete by filters
            if not filters:
                sql = f"DELETE FROM {table_name}"
                return sql, ()
            else:
                where_clause, values = parse_filter(obj_or_table, filters)
                sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                return sql, tuple(values)

    
    @staticmethod
    def generate_index(table):
        table_name = table.__table_name__ or table.__name__
        sqls = []
        for col_name in table._indexes:
            index_name = f"{table_name}_{col_name}_idx"
            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({col_name})"
            sqls.append(sql)
        return sqls
    
    @staticmethod
    def generate_drop(table):
        table_name = table.__table_name__ or table.__name__
        return f"DROP table {table_name}"
    
    @staticmethod
    def generate_get_pk(table, **filters):
        table_name = table.__table_name__ or table.__name__
        pk_fields = [ name for name, col in table._columns.items() if col.primary_key]
        pk_sql = ", ".join(pk_fields)
        if not pk_fields:
            return f"SELECT {pk_sql} from {table_name}", tuple()
        where_clause, values = parse_filter(table, filters)
        return f"SELECT {pk_sql} from {table_name} WHERE {where_clause}", tuple(values)
    
    @staticmethod
    def generate_select(table: Type[Table], **filters) -> tuple[str, list]:
        table_name = table.__table_name__ or table.__name__
        sql = f"SELECT * FROM {table_name}"
        if filters:
            where_clause, values = parse_filter(table, filters)
            sql += " WHERE " + where_clause
        else:
            values = []
        return sql, values
    
def parse_filter(table:Table, filters: dict) -> tuple[str, list]:
    conditions = []
    values = []
    for key, value in filters.items():
        if key not in table._columns:
            raise ValueError(f"Unknown column name: {key}")
        col = table._columns[key]
        if isinstance(value, operator.Operator):
            op = operator.OP_MAPPING.get(type(value), "=")
            conditions.append(f"{key} {op} ?")
            values.append(col.to_db(value.value))
        else:
            conditions.append(f"{key} = ?")
            values.append(col.to_db(value))
    return " AND ".join(conditions), values   