import aiosqlite
import sqlite3
from typing import Type, List
from ..basic import AsyncBaseSession
from ...generator import SQLiteGenerator
from ...operator import Equal
from ...table import Table
from ...column import FieldRef
from ...base import TABLE_REGISTRY
from ... import errors

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

    async def execute(self, sql:str, value=None):
        return await self._conn.execute(sql, value)

    async def commit(self):
        await self._conn.commit()

    async def create_table(self, table: Type[Table], exist_ok: bool = False):
        sql = self._generator.generate_create_table(table, exist_ok)
        await self._conn.execute(sql)

        for index_sql in self._generator.generate_index(table):
            await self._conn.execute(index_sql)

        if self._auto_commit:
            await self._conn.commit()

    async def insert(self, obj: Table):
        sql, values = self._generator.generate_insert(obj)
        try:
            await self._conn.execute(sql, values)

            if self._auto_commit:
                await self._conn.commit()
        except sqlite3.IntegrityError:
            raise errors.PrimaryKeyConflict()

    async def insert_many(self, objs: List[Table]):
        if not objs:
            return
        
        sql, _ = self._generator.generate_insert(objs[0])
        all_values = [self._generator.generate_insert(obj)[1] for obj in objs]

        try:
            await self._conn.executemany(sql, all_values)
            if self._auto_commit:
                await self._conn.commit()
        except sqlite3.IntegrityError:
            raise errors.PrimaryKeyConflict()

    async def _filter(self, table: Type[Table], *filters, ref_obj:Table=None) -> List[Table]:
        combined_filter = None
        if filters:
            for f in filters:
                if combined_filter is None:
                    combined_filter = f
                else:
                    combined_filter &= f
        sql, values = self._generator.generate_select(table, combined_filter, ref_obj)
        async with self._conn.execute(sql, values) as cursor:
            rows = await cursor.fetchall()
            objs = [table.from_row(dict(row)) for row in rows]
            return objs

    async def get_first(self, table, *filters, load_relationships=True, read_only=False, ref_obj:Table=None) -> Table | None:
        result = await self._filter(table, *filters, ref_obj=ref_obj)
        if result:
            result = result[0]
            if load_relationships:
                await self._load_relationship(result, ref_obj=ref_obj)
            result._initialized = True
        return result if result else None

    async def get_all(self, table, *filters, load_relationships=True, read_only=False, ref_obj:Table=None) -> List[Table]:
        result = await self._filter(table, *filters, ref_obj=ref_obj)
        for obj in result:
            if load_relationships:
                await self._load_relationship(obj, ref_obj=ref_obj)
            obj._initialized = True
        return result

    async def update(self, obj: Table, merge: bool=True, update_relationship: bool=True) -> None:
        # update relationships
        if update_relationship:
            traces = {obj}
            await self._update_relationship(obj, traces=traces)
        else:
            sql, values = self._generator.generate_update(obj, merge=merge)
            await self._conn.execute(sql, values)

        if self._auto_commit:
            await self._conn.commit()

    async def delete(self, obj: Table) -> None:
        sql, values = self._generator.generate_delete(obj)
        await self._conn.execute(sql, values)

        if self._auto_commit:
            await self._conn.commit()

    async def count(self, table: Table, filters=None) -> int:
        sql, values = self._generator.generate_count(table, filters)

        async with self._conn.execute(sql, values) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
        
    async def get_table_structure(self, table: Table) -> list[dict]:
        table_name = table.__table_name__ or table.__name__
        async with self._conn.execute(f"PRAGMA table_info({table_name})") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        
    async def update_table_structure(self, table: Type[Table], rebuild=False):
        """
        Update table structure to sync with definition.
        - If rebuild = `False`: Only add missing columns using ALTER TABLE.
        - If rebuild = `True`: Rebuild entire table (DROP and recreate).
        """
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

            if self._auto_commit:
                await self._conn.commit()
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

        if self._auto_commit:
            await self._conn.commit()

    async def initialize(self, structure_update=False, rebuild=False):
        for table in TABLE_REGISTRY.values():
            await self.create_table(table, True)
            if structure_update:
                await self.update_table_structure(table, rebuild)

    async def _load_relationship(self, obj: Table, _traces=None, ref_obj:Table=None):
        if _traces is None:
            _traces = {obj.__hash__():obj}

        for name, relation in obj._relationship.items():
            if relation.plural_data:
                table_data = await self.get_all(relation.get_table(), relation.fix_filters(), load_relationships=False, ref_obj=obj)
                if not table_data:
                    continue
                for item in table_data:
                    if item.__hash__() in _traces:
                        continue
                    _traces[item.__hash__()] = item
                    await self._load_relationship(item, _traces, ref_obj=obj)
            else:
                table_data = await self.get_first(relation.get_table(), relation.fix_filters(), load_relationships=False, ref_obj=obj)
                if table_data is None:
                    continue
                if table_data.__hash__() in _traces:
                    continue
                _traces[obj.__hash__()] = table_data
                await self._load_relationship(table_data, _traces, ref_obj=obj)
            setattr(obj, name, table_data)

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
                    await self._conn.execute(sql, values)
                    await self._update_relationship(item, traces)
                    traces.add(item)
            else:
                if related_data in traces:
                    continue
                sql, values = self._generator.generate_update(related_data, merge=True)
                await self._conn.execute(sql, values)
                await self._update_relationship(related_data, traces)
                traces.add(related_data)