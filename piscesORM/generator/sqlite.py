from __future__ import annotations
from typing import Type, Any, overload
from ..table import Table
from ..column import Column
import logging
from abc import ABC, abstractmethod
from .. import errors
from ..import operator
import warnings
from . import BasicGenerator

class SQLiteGenerator(BasicGenerator):
    @staticmethod
    def generate_create_table(table, exist_ok = False):
        table_name = table.__table_name__ or table.__name__
        column_defs = []
        pk_fields = []

        for name, column in table._columns.items():
            parts = [name, column._type['sqlite']]

            # INTEGER PRIMARY KEY AUTOINCREMENT
            if column.primary_key and column.auto_increment and column._type['sqlite'] == "INTEGER":
                parts.append("PRIMARY KEY AUTOINCREMENT")
                # 不要再於後面補 PRIMARY KEY
            else:
                if column.not_null:
                    parts.append("NOT NULL")
                if column.unique and not column.primary_key:
                    parts.append("UNIQUE")      
                if column.default is not None:
                    parts.append(f"DEFAULT {repr(column.to_db(column.default))}")
            
            column_defs.append(" ".join(parts))

            if column.primary_key:
                pk_fields.append(name)

        # 修正：如果已經在欄位加了 PRIMARY KEY AUTOINCREMENT，就不要再加 PRIMARY KEY
        # 單一主鍵且不是自增主鍵時才補 PRIMARY KEY
        if len(pk_fields) == 1:
            pk_name = pk_fields[0]
            col = table._columns[pk_name]
            if not (col.primary_key and col.auto_increment and col._type['sqlite'] == "INTEGER"):
                # 找到該欄位加 PRIMARY KEY
                for i, name in enumerate(table._columns):
                    if name == pk_name:
                        column_defs[i] += " PRIMARY KEY"
        elif len(pk_fields) > 1:
            quoted = ", ".join(quote_ident(f) for f in pk_fields)
            column_defs.append(f"PRIMARY KEY ({quoted})")
        elif not table.__no_primary_key__:
            warnings.warn(errors.NoPrimaryKeyWarning())

        columns_sql = ", ".join(column_defs)
        return f"CREATE TABLE {'IF NOT EXISTS' if exist_ok else ''} {table_name} ({columns_sql});"
    
    @staticmethod
    def generate_structure(table):
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
                
                col_type = column._type['sqlite']
                constraints = []
                if column.not_null:
                    if column.default is None:
                        raise errors.NotNullColumnWithoutDefault(col_name)
                    constraints.append("NOT NULL")

                constraint_sql = " ".join(constraints)
                default_sql = ""
                if column.default is not None:
                    default_sql = f"DEFAULT {format_default(column.to_db(column.default))}"

                full_col_sql = f"{quote_ident(col_name)} {col_type} {constraint_sql} {default_sql}".strip()
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
    def generate_update_object(obj, merge = True):
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

        if not set_parts:
            return None , tuple()

        sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        return sql, tuple(set_values + where_values)
    
    @staticmethod
    def generate_update(table, filters, **target):
        table_name = table.__table_name__ or table.__name__
        set_parts = []
        set_values = []
        where_sql, where_values = parse_LogicalOperator(table, filters)

        key_list = table._columns.keys()
        for col_name, value in target.items():
            if col_name not in key_list:
                raise errors.NoSuchColumn(col_name)
            

        sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {where_sql}"
        return sql, tuple()
    
    @staticmethod
    def generate_delete(obj_or_table: Table|Type[Table], filters=None, delete_all_protect=True):
        table_name = obj_or_table.__table_name__ or obj_or_table.__name__

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
                if not delete_all_protect:
                    sql = f"DELETE FROM {table_name}"
                    return sql, ()
                raise errors.UnsafeDeleteError()
            else:
                where_clause, values = parse_LogicalOperator(obj_or_table, filters)
                sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                return sql, tuple(values)
    
    @staticmethod
    def generate_index(table):
        table_name = table.__table_name__ or table.__name__
        sqls = []
        for col_name in table._indexes:
            index_name = f"{table_name}_{col_name}_idx"
            col = table._columns[col_name]
            unique_sql = "UNIQUE " if col.unique else ""
            sql = f"CREATE {unique_sql}INDEX IF NOT EXISTS {quote_ident(index_name)} ON {table_name} ({quote_ident(col_name)})"
            sqls.append(sql)
        return sqls
    
    @staticmethod
    def generate_drop(table):
        table_name = table.__table_name__ or table.__name__
        return f"DROP table {table_name}"
    
    @staticmethod
    def generate_select(table: Type[Table], filters=None) -> tuple[str, list]:
        table_name = table.__table_name__ or table.__name__
        sql = f"SELECT * FROM {table_name}"
        if filters:
            where_clause, values = parse_LogicalOperator(table, filters)
            sql += " WHERE " + where_clause
        else:
            values = []
        return sql, values
    
    @staticmethod
    def generate_count(table: Type[Table], filters=None) -> tuple[str, list]:
        table_name = table.__table_name__ or table.__name__
        sql = f"SELECT COUNT(*) FROM {table_name}"
        values = []
        if filters:
            where_clause, values = parse_LogicalOperator(table, filters)
            sql += " WHERE " + where_clause
        return sql, values

def parse_LogicalOperator(table: Type[Table], op: operator.LogicalOperator) -> tuple[str, list]:
    from ..operator import SQLITE_TRANSLATE_MAP
    if isinstance(op, (operator.AND, operator.OR)):
        left_sql, left_vals = parse_LogicalOperator(table, op.first_part)
        right_sql, right_vals = parse_LogicalOperator(table, op.second_part)
        sql = f"({left_sql}) {SQLITE_TRANSLATE_MAP[type(op)]} ({right_sql})"
        return sql, left_vals + right_vals
    elif isinstance(op, operator.In_):
        col = table._columns[op.first_part]
        placeholders = ','.join(['?'] * len(op.second_part))
        sql = f"{op.first_part} IN ({placeholders})"
        vals = [col.to_db(v) for v in op.second_part]
        return sql, vals
    else:
        col = table._columns[op.first_part]
        sql = f"{op.first_part} {SQLITE_TRANSLATE_MAP[type(op)]} ? "
        val = col.to_db(op.second_part)
        return sql, [val]

def quote_ident(name: str) -> str:
    """Quote identifier to avoid conflicts with SQLite keywords"""
    return f'"{name}"'   

def format_default(val: any) -> str:
    """Format DEFAULT value safely for SQLite"""
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val).replace("'", "''")  # escape single quotes
    return f"'{s}'"