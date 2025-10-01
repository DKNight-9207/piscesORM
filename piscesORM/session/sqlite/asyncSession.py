import aiosqlite
import sqlite3
from typing import Type, List
import functools
from ..basic import AsyncBaseSession
from ...generator import SQLiteGenerator
from ...operator import Equal, Operator
from ...table import Table
from ...column import FieldRef, Column
from ...base import TABLE_REGISTRY
from ... import errors
from logging import getLogger

logger = getLogger("piscesORM")

class AsyncSQLiteSession(AsyncBaseSession):
    def __init__(self, connection: aiosqlite.Connection, mode="r", auto_commit: bool = True):
        self._conn = connection
        self._conn.row_factory = sqlite3.Row
        self._auto_commit = auto_commit
        self._generator = SQLiteGenerator

    async def on_connected(self):
        try:
            await self.execute("SELECT 1")
            return True
        except:
            return False

    async def execute(self, sql: str, value=None):
        return await self._run_sql(sql, value or [])

    async def commit(self):
        await self._conn.commit()

    async def rollback(self):
        await self._conn.rollback()

    async def initialize(self, structure_update=False, rebuild=False):
        for table in TABLE_REGISTRY.values():
            await self.create_table(table, True)
            if structure_update:
                await self.update_table_structure(table, rebuild)

    async def create_table(self, table: Type[Table], exist_ok: bool = False):
        sql = self._generator.generate_create_table(table, exist_ok)
        await self._run_sql(sql)

        for index_sql in self._generator.generate_index(table):
            await self._run_sql(index_sql)

        await self._maybe_commit()

    async def create_join_table(self, table_1, table_2, exist_ok=False):
        raise RuntimeError("NOT ready yet")

    async def drop_table(self, table):
        if isinstance(table, str):
            table = TABLE_REGISTRY.get(table)
        sql = self._generator.generate_drop(table)
        await self._run_sql(sql)
        await self._maybe_commit()

    async def insert(self, obj: Table):
        sql, values = self._generator.generate_insert(obj)
        await self._run_sql(sql, values)
        await self._maybe_commit()

    async def insert_many(self, objs: List[Table]):
        if not objs:
            return
        
        sql, _ = self._generator.generate_insert(objs[0])
        all_values = [self._generator.generate_insert(obj)[1] for obj in objs]
        await self._run_sql(sql, all_values, True)
        await self._maybe_commit()

    async def _filter(self, table: Type[Table]|Table, *filters, order_by=None, limit=None, ref_obj:Table=None) -> List[Table]:
        condition = self._combine_filters(*filters)
        new_order_by = self._fix_order(order_by)
        
        sql, values = self._generator.generate_select(table, None, condition, new_order_by, limit, ref_obj)
        cursor = await self._run_sql(sql, values)
        rows = await cursor.fetchall()
        return [table.from_row(dict(row)) for row in rows]

    async def _get_first(self, table, *filters, order_by=None, limit=None, ref_obj=None, **kwargs):
        if result := await self._filter(table, *filters, order_by=order_by, limit=limit, ref_obj=ref_obj):
            result:Table = result[0]
            if kwargs.get("load_relationships", True):
                await self._load_relationship(result)
            result._initialized = True
        logger.debug(f"get data: {result._get_pks() if result else 'None'}")
        return result if result else None
    
    async def get_first(self, table, *filters, order_by = None, limit= None, **kwargs) -> Table:
        return await self._get_first(table, *filters, order_by=order_by, limit=limit, **kwargs)

    async def _get_all(self, table: Type[Table] | Table, *filters, order_by: str | list[str] = None, limit: int = None, ref_obj: Table = None, **kwargs):
        result:list[Table] = await self._filter(table, *filters, order_by=order_by, limit=limit, ref_obj=ref_obj)
        for obj in result:
            if kwargs.get("load_relationships", True):
                await self._load_relationship(obj)
            obj._initialized = True
        logger.debug(f"get data: {[r._get_pks() for r in result]}")
        return result

    async def get_all(self, table: Type[Table], *filters: Operator, order_by: str | list[str] = None, limit: int = None, **kwargs) -> List[Table]:
        return await self._get_all(table, *filters, order_by, limit, **kwargs)
       
    async def update(self, table, *filters, **set):
        sql, values = self._generator.generate_update(table, *filters, **set)
        await self._run_sql(sql, values)
        await self._maybe_commit()

    async def merge(self, obj: Table, cover: bool = False) -> None:
        await self._update_relationship(obj)
        sql, values = self._generator.generate_update_object(obj, cover)
        await self._run_sql(sql, values)
        await self._maybe_commit()

    async def _update_relationship(self, obj: Table, traces: set[Table] = None) -> None:
        if traces is None:
            traces = {obj}

        for name, relation in obj._relationship.items():
            related_data = getattr(obj, name, None)
            if related_data is None:
                continue
            if relation.plural_data:
                for item in related_data:
                    if item in traces:
                        continue
                    sql, values = self._generator.generate_update(item, merge=True)
                    await self._run_sql(sql, values)
                    await self._update_relationship(item, traces)
                    traces.add(item)
            else:
                if related_data in traces:
                    continue
                sql, values = self._generator.generate_update(related_data, merge=True)
                await self._run_sql(sql, values)
                await self._update_relationship(related_data, traces)
                traces.add(related_data)

    async def delete_object(self, obj: Table) -> None:
        sql, values = self._generator.generate_delete(obj)
        await self._run_sql(sql, values)

        await self._maybe_commit()

    async def delete(self, table, *filters):
        condition = self._combine_filters(*filters)
        sql, values = self._generator.generate_delete(table, condition)
        await self._run_sql(sql, values)
        await self._maybe_commit()

    async def count(self, table: Table, filters=None) -> int:
        sql, values = self._generator.generate_count(table, filters)
        cursor = await self._run_sql(sql, values)
        row = await cursor.fetchone()
        return row[0] if row else 0
        
    async def get_table_structure(self, table: Table) -> list[dict]:
        table_name = table.__table_name__ or table.__name__
        cursor = await self._run_sql(f"PRAGMA table_info({table_name})")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
        
    async def update_table_structure(self, table: Type[Table], rebuild=False):
        table_name = table.__table_name__ or table.__name__

        # 1. Get actual DB columns
        db_columns = await self.get_table_structure(table)
        db_columns_list:list[str] = [col["name"] for col in db_columns]
        defined_columns_set:set[str] = set(table._columns.keys())

        update_sqls = self._generator.generate_insert_column(table, db_columns_list)
        if update_sqls is None:
            return
        
        if not rebuild:
            # Try only to add missing columns
            for s in update_sqls:
                await self._conn.execute(s)

            await self._maybe_commit()
            return
        
        # 2. create new table / copy data
        await self._conn.execute("PRAGMA foreign_keys = OFF;")  # Temporarily disable FK

        tmp_table_name =f"{table_name}_tmp_fix"
        create_sql = self._generator.generate_create_table(table, exist_ok=True).replace(table_name, tmp_table_name)
        await self._conn.execute(create_sql)

        shared_keys = set(db_columns_list) & defined_columns_set
        shared_keys_sql = ", ".join(shared_keys)
        copy_sql = (
            f"INSERT INTO {tmp_table_name} ({shared_keys_sql}) "
            f"SELECT {shared_keys_sql} FROM {table_name};"
        )
        await self._conn.execute(copy_sql)

        # Drop old table and rename new one
        await self._conn.execute(f"DROP TABLE {table_name};")
        await self._conn.execute(f"ALTER TABLE {tmp_table_name} RENAME TO {table_name};")

        for sql in self._generator.generate_index(table):
            await self._conn.execute(sql)

        await self._conn.execute("PRAGMA foreign_keys = ON;")

        await self._maybe_commit()

    async def initialize(self, structure_update=False, rebuild=False):
        for table in TABLE_REGISTRY.values():
            await self.create_table(table, True)
            if structure_update:
                await self.update_table_structure(table, rebuild)


    async def _load_relationship(self, obj:Table, _traces=None):
        if _traces is None:
            _traces = {obj._get_pks(): obj}

        for name, relation in obj._relationship.items():
            table_data = None
            if relation.plural_data:
                table_data = await self._get_all(
                    relation.get_table(),
                    relation.fix_filters(),
                    ref_obj=obj,
                    load_relationships=False)
                for item in table_data:
                    pk = item._get_pks()
                    if pk in _traces.keys():
                        continue
                    _traces[pk] = item
                    await self._load_relationship(item, _traces)
            else:
                table_data = await self._get_first(
                    relation.get_table(),
                    relation.fix_filters(),
                    ref_obj=obj,
                    load_relationships=False)
                if table_data is not None:
                    pk = table_data._get_pks()
                    if pk not in _traces:
                        _traces[pk] = table_data
                        await self._load_relationship(table_data, _traces)
            setattr(obj, name, table_data)
        obj._initialized = True

    @staticmethod
    def _combine_filters(*filters:Operator) -> Operator:
        return functools.reduce(lambda x, y: x & y if x else y, filters or [], None)
    
    @staticmethod
    def _fix_order(orders) -> list[str]:
        combine_order = []
        if not isinstance(orders, list):
            orders = [orders] 

        for ord in orders:
            if isinstance(ord, Column):
                combine_order.append(f"-{ord._name}" if ord._neg_tag else ord._name)
            elif isinstance(ord, str):
                combine_order.append(ord)
            else:
                raise errors.IllegalOrderByValue()

        return combine_order

    async def _run_sql(self, sql:str, values=None, many=False):
        try:
            if many:
                cursor = await self._conn.executemany(sql, values)
            else:
                cursor = await self._conn.execute(sql, values or [])
            return cursor
        except sqlite3.IntegrityError:
            raise errors.PrimaryKeyConflict()
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error during SQL execution: {sql}, values: {values}")
            raise

    async def _maybe_commit(self):
        if self._auto_commit:
            await self._conn.commit()