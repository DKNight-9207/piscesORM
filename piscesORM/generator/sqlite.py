from __future__ import annotations
from typing import Type
from ..table import Table
import logging
from .. import errors
import warnings
from . import BasicGenerator
from ..operator import Operator
from ..operator.translate.sqlite import SQLITE_TRANSLATE_MAP, translate_sqlite_security
logger = logging.getLogger("piscesORM")

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
        sql = f"CREATE TABLE {'IF NOT EXISTS ' if exist_ok else ''}{table_name} ({columns_sql});"
        logger.debug(f"Generate sql: {sql}")
        return sql
    
    @staticmethod
    def generate_structure(table):
        table_name = table.__table_name__ or table.__name__
        sql = f"PRAGMA table_info({table_name})"
        logger.debug(f"Generate sql: {sql}")
        return sql
    
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
                logger.debug(f"Generate sql: {sqls}")
            return sqls
        return None

    @staticmethod
    def generate_insert(obj:Table):
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
        logger.debug(f"Generate sql: {sql}, {values}")
        return sql, tuple(values)
    
    @staticmethod
    def generate_update_object(obj:Table, cover = False):
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
                if cover or name in obj._edited:
                    set_parts.append(f"{name} = ?")
                    set_values.append(column.to_db(value))

        if not set_parts:
            return None , tuple()

        sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        logger.debug(f"Generate sql: {sql}, {set_values + where_values}")
        return sql, tuple(set_values + where_values)
    
    @staticmethod
    def generate_update(table:Type[Table], filters, **target):
        table_name = table.__table_name__ or table.__name__
        set_parts = []
        set_values = []
        where_sql, where_values = translate_sqlite_security(filters)

        key_list = table._columns.keys()
        for col_name, value in target.items():
            if col_name not in key_list:
                raise errors.NoSuchColumn(col_name)
            
            if isinstance(value, Operator):
                set_parts.append(f"{col_name} = {col_name} {SQLITE_TRANSLATE_MAP[type(value)]} ?")
                set_values.append(table._columns[col_name].to_db(value.parts[0]))
            else:
                set_parts.append(f"{col_name} = ?")
                set_values.append(table._columns[col_name].to_db(value))
            

        sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {where_sql}"
        logger.debug(f"Generate sql: {sql}, {set_values + list(where_values)}")
        return sql, tuple(set_values + list(where_values))
    
    @staticmethod
    def generate_delete(obj_or_table: Table|Type[Table], filters=None, delete_all_protect=True):
        table_name = get_table_name(obj_or_table)

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
                raise errors.NoPrimaryKeyError("Cannot delete without a primary key.")

            sql = f"DELETE FROM {table_name} WHERE {' AND '.join(where_parts)}"
            logger.debug(f"Generate sql: {sql}, {where_values}")
            return sql, tuple(where_values)
        else: # delete by filters
            if not filters:
                if not delete_all_protect:
                    sql = f"DELETE FROM {table_name}"
                    return sql, ()
                raise errors.UnsafeDeleteError()
            else:
                where_clause, values = translate_sqlite_security(filters)
                sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                logger.debug(f"Generate sql: {sql}, {values}")
                return sql, tuple(values)
    
    @staticmethod
    def generate_index(table:Type[Table]):
        table_name = table.__table_name__ or table.__name__
        sqls = []
        for col_name in table._indexes:
            index_name = f"{table_name}_{col_name}_idx"
            col = table._columns[col_name]
            unique_sql = "UNIQUE " if col.unique else ""
            sql = f"CREATE {unique_sql}INDEX IF NOT EXISTS {quote_ident(index_name)} ON {table_name} ({quote_ident(col_name)})"
            sqls.append(sql)
        logger.debug(f"Generate sql: {sqls}")
        return sqls
    
    @staticmethod
    def generate_drop(table:Type[Table]):
        table_name = table.__table_name__ or table.__name__
        sql = f"DROP table {table_name}"
        logger.debug(f"Generate sql: {sql}")
        return sql
    
    @staticmethod
    def generate_select(table: Type[Table], columns=None, filters=None, order_by=None, limit=None, ref_obj:Table=None) -> tuple[str, list]:
        table_name = table.__table_name__ or table.__name__
        valid_columns = table._columns.keys()
        logger.debug(f"try to generate select:")
        logger.debug(f" - table:    {type(table)}")
        logger.debug(f" - columns:  {columns}")
        logger.debug(f" - filters:  {repr(filters)}")
        logger.debug(f" - order_by: {order_by}")
        logger.debug(f" - limit:    {limit}")
        logger.debug(f" - ref_obj:  {ref_obj}")

        if not columns:
            select_clause = "*"
        else:
            if isinstance(columns, str):
                columns = [columns]

            for col in columns:
                if col not in valid_columns:
                    raise errors.NoSuchColumn(col)
            select_clause = ", ".join(columns)    
        sql = f"SELECT {select_clause} FROM {table_name}"
        values = []

        if filters:
            where_clause, values = translate_sqlite_security(filters, ref_obj)
            sql += " WHERE " + where_clause
            
        if order_by:
            if isinstance(order_by, str):
                order_by = [order_by]
            oder_by_clause = []
            for col in order_by:
                if col.startswith("-"):
                    col_name = col[1:]
                    direction = "DESC"
                else:
                    col_name = col
                    direction = "ASC"

                if col_name not in valid_columns:
                    raise errors.NoSuchColumn(col_name)
                oder_by_clause.append(f"{col_name} {direction}")

            if oder_by_clause:
                sql += " ORDER BY " + ", ".join(oder_by_clause)
    
        if isinstance(limit, int) and limit > 0: # SQL inject protect
            sql += f" LIMIT {limit}"

        logger.debug(f"Generate sql: {sql}, {values}")
        return sql, values
    
    @staticmethod
    def generate_count(table: Type[Table], filters=None, ref_obj:Table = None) -> tuple[str, list]:
        table_name = table.__table_name__ or table.__name__

        sql = f"SELECT COUNT(*) FROM {table_name}"
        values = []
        if filters:
            where_clause, values = translate_sqlite_security(filters, ref_obj)
            sql += " WHERE " + where_clause
        logger.debug(f"Generate sql: {sql}, {values}")
        return sql, values

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

def get_table_name(obj_or_table: Table | Type[Table]) -> str:
    if isinstance(obj_or_table, type):
        return obj_or_table.__table_name__ or obj_or_table.__name__
    return obj_or_table.__table_name__ or obj_or_table.__class__.__name__