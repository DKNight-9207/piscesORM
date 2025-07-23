from __future__ import annotations
from unittest import result
import aiosqlite
import sqlite3
from typing import Type, List, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from .table import Table, TableMeta
from .column import Column, Relationship, FieldRef
from . import errors
from . import generator

class AsyncBaseSession(ABC):
    def __init__(self, connection: Any, mode="r", auto_commit: bool = True):
        """mode: only work on 'Application Lock' engine"""
        self._conn = connection
        self.mode = mode
        self._auto_commit = auto_commit

    @abstractmethod
    async def __aenter__(self): ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb): ...

    @abstractmethod
    async def execute(self, sql, value: Any): ...

    @abstractmethod
    async def initialize(self, structure_update=False, rebuild: bool = False): ...

    @abstractmethod
    async def update_table_structure(self, table: Type[Table], rebuild: bool = False): ...

    @abstractmethod
    async def create_table(self, table: Type[Table], exist_ok: bool = False): ...

    @abstractmethod
    async def insert(self, obj: Table): ...

    @abstractmethod
    async def insert_many(self, objs: List[Table]): ...

    @abstractmethod # org. filter
    async def get_all(self, table: Type[Table], load_relationships = True, read_only=False, **kwargs) -> List[Table]: ...

    @abstractmethod
    async def get_first(self, table: Type[Table], load_relationships = True, read_only=False, **kwargs) -> Table: ...

    @abstractmethod
    async def update(self, obj: Table, merge: bool = False): ...

    @abstractmethod
    async def delete(self, obj: Table): ...

    @abstractmethod
    async def _load_relationship(self, obj: Table, _traces:dict[tuple, Table]=None): ...


class SyncBaseSession(ABC):
    def __init__(self, connection: Any, auto_commit: bool = True):
        self._conn = connection
        self._auto_commit = auto_commit

    @abstractmethod
    def __enter__(self): ...

    @abstractmethod
    def __exit__(self, exc_type, exc, tb): ...

    @abstractmethod
    def execute(self, sql, value: Any): ...

    @abstractmethod
    def initialize(self, structure_update=False, rebuild: bool = False): ...

    @abstractmethod
    def update_table_structure(self, table: Type[Table], rebuild: bool = False): ...

    @abstractmethod
    def create_table(self, table: Type[Table], exist_ok: bool = False): ...

    @abstractmethod
    def insert(self, obj: Table): ...

    @abstractmethod
    def insert_many(self, objs: List[Table]): ...

    @abstractmethod # org. filter
    def get_all(self, table: Type[Table], load_relationships = True, **kwargs) -> List[Table]: ...

    @abstractmethod
    def get_first(self, table: Type[Table], load_relationships = True, **kwargs) -> Table: ...

    @abstractmethod
    def update(self, obj: Table, merge: bool = False): ...

    @abstractmethod
    def delete(self, obj: Table): ...

    @abstractmethod
    def _load_relationship(self, obj: Table, _traces:dict[tuple, Table]=None): ...

class AsyncSQLiteSession(AsyncBaseSession):
    def __init__(self, connection: aiosqlite.Connection, mode="r", auto_commit: bool = True):
        self._conn = connection
        self._auto_commit = auto_commit
        self._generator = generator.SQLiteGenerator

    async def __aenter__(self):
        self._conn.row_factory = aiosqlite.Row
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._conn:
            await self._conn.commit()
            await self._conn.close()

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
        
        sql = self._generator.generate_insert(objs[0])
        all_values = [self._generator.generate_insert(obj)[1] for obj in objs]

        try:
            await self._conn.executemany(sql, all_values)
            if self._auto_commit:
                await self._conn.commit()
        except sqlite3.IntegrityError:
            raise errors.PrimaryKeyConflict()

    async def filter(self, table: Type[Table], **kwargs) -> List[Table]:
        table_name = table.__table_name__ or table.__name__
        sql = f"SELECT * FROM {table_name}"
        values = []

        if kwargs:
            conditions = []
            for key, value in kwargs.items():
                if key not in table._columns:
                    raise ValueError(f"Unknown column name: {key}")
                column = table._columns[key]
                conditions.append(f"{key} = ?")
                values.append(value)
            sql += " WHERE " + " AND ".join(conditions)

        async with self._conn.execute(sql, values) as cursor:
            rows = await cursor.fetchall()
            objs = [table.from_row(dict(row)) for row in rows]
            return objs

    async def get_first(self, table: Type[Table], load_relationships = True, read_only = False, **kwargs) -> Table | None:
        result = await self.filter(table, **kwargs)
        if result is not None:
            result = result[0]
            if load_relationships:
                await self._load_relationship(result)
        return result if result else None

    async def get_all(self, table: Type[Table], load_relationships = True, read_only = False, **kwargs) -> List[Table]:
        result = await self.filter(table, **kwargs)
        for obj in result:
            if load_relationships:
                await self._load_relationship(obj)
        return result

    async def update(self, obj: Table, merge: bool=True) -> None:
        sql, values = self._generator.generate_update(obj, merge=merge)
        cursor = await self._conn.execute(sql, values)

        if self._auto_commit:
            await self._conn.commit()

    async def delete(self, obj: Table) -> None:
        sql, values = self._generator.generate_delete(obj)
        cursor = await self._conn.execute(sql, values)

        if self._auto_commit:
            await self._conn.commit()

    async def count(self, table: Table, **kwargs) -> int:
        table_name = table.__table_name__ or table.__name__
        sql = f"SELECT COUNT(*) FROM {table_name}"
        values = []
        if kwargs:
            conditions = []
            for key, value in kwargs.items():
                if key not in table._columns:
                    raise ValueError(f"Unknown column name: {key}")
                conditions.append(f"{key} = ?")
                values.append()
            sql += " WHERE " + " AND ".join(conditions)

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
        - If rebuild=False: Only add missing columns using ALTER TABLE.
        - If rebuild=True: Rebuild entire table (DROP and recreate).
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
        for table in TableMeta._registry:
            await self.create_table(table, True)
            if structure_update:
                await self.update_table_structure(table, rebuild)

    async def _load_relationship(self, obj, _traces=None):
        if _traces is None:
            _traces = {obj.__hash__():obj}

        for name, relation in obj._relationship.items():
            if relation.plural_data:
                table_data = await self.get_all(relation.table, **relation.filter)
                if not table_data:
                    continue
                for item in table_data:
                    if item.__hash__() in _traces:
                        continue
                    _traces[item.__hash__()] = item
                    await self._load_relationship(item, _traces)
            else:
                table_data = await self.get_first(relation.table, **relation.filter)
                if table_data is None:
                    continue
                if table_data.__hash__() in _traces:
                    continue
                _traces[obj.__hash__()] = table_data
                await self._load_relationship(table_data, _traces)
            setattr(obj, name, table_data)

class SyncSQLiteSession(SyncBaseSession):
    def __init__(self, connection: sqlite3.Connection, mode="r", auto_commit: bool = True):
        self._conn = connection
        self._conn.row_factory = sqlite3.Row
        self._auto_commit = auto_commit
        self._generator = generator.SQLiteGenerator

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._conn:
            self._conn.commit()
            self._conn.close()

    def execute(self, sql:str, value=None):
        return self._conn.execute(sql, value or [])

    def commit(self):
        self._conn.commit()

    def create_table(self, table: Type[Table], exist_ok: bool = False):
        sql = self._generator.generate_create_table(table, exist_ok)
        self._conn.execute(sql)

        for index_sql in self._generator.generate_index(table):
            self._conn.execute(index_sql)

        if self._auto_commit:
            self._conn.commit()

    def insert(self, obj: Table):
        sql, values = self._generator.generate_insert(obj)
        try:
            cursor = self._conn.execute(sql, values)

            if self._auto_commit:
                self._conn.commit()
        except sqlite3.IntegrityError:
            raise errors.PrimaryKeyConflict()


    def insert_many(self, objs: List[Table]):
        if not objs:
            return
        
        sql, value = self._generator.generate_insert(objs[0])
        all_values = [self._generator.generate_insert(obj)[1] for obj in objs]

        try:
            self._conn.executemany(sql, all_values)
            if self._auto_commit:
                self._conn.commit()
        except sqlite3.IntegrityError:
            raise errors.PrimaryKeyConflict()
    
    def filter(self, table: Type[Table], **kwargs) -> List[Table]:
        table_name = table.__table_name__ or table.__name__
        sql = f"SELECT * FROM {table_name}"
        values = []

        if kwargs:
            conditions = []
            for key, value in kwargs.items():
                if key not in table._columns:
                    raise ValueError(f"Unknown column name: {key}")
                conditions.append(f"{key} = ?")
                values.append(value)
            sql += " WHERE " + " AND ".join(conditions)

        cursor = self._conn.execute(sql, values)
        rows = cursor.fetchall()
        objs = [table.from_row(dict(row)) for row in rows]
        return objs

    def get_first(self, table: Type[Table], load_relationships = True, **kwargs) -> Table | None:
        result = self.filter(table, **kwargs)
        if result is not None:
            result = result[0]
            if load_relationships:
                self._load_relationship(result)
            result._initialized = True
        return result if result else None

    def get_all(self, table: Type[Table], load_relationships = True, **kwargs) -> List[Table]:
        result = self.filter(table, **kwargs)
        for obj in result:
            if load_relationships:
                self._load_relationship(obj)
            obj._initialized = True
        return result
        
    def update(self, obj: Table, merge: bool=True, update_relationship: bool=True) -> None:
        

        # update relationships
        if update_relationship:
            traces = {obj}
            self._update_relationship(obj, traces=traces)
        else: 
            sql, values = self._generator.generate_update(obj, merge=merge)
            self._conn.execute(sql, values)

        if self._auto_commit:
            self._conn.commit()

    def _update_relationship(self, obj: Table, traces: set[Table] = None) -> None:
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
                    self._conn.execute(sql, values)
                    self._update_relationship(item, traces)
                    traces.add(item)
            else:
                if related_data in traces:
                    continue
                sql, values = self._generator.generate_update(related_data, merge=True)
                self._conn.execute(sql, values)
                self._update_relationship(related_data, traces)
                traces.add(related_data)
            


    def delete(self, obj: Table) -> None:
        sql, values = self._generator.generate_delete(obj)
        self._conn.execute(sql, values)

        if self._auto_commit:
            self._conn.commit()

    def count(self, table: Table, **kwargs) -> int:
        table_name = table.__table_name__ or table.__name__
        sql = f"SELECT COUNT(*) FROM {table_name}"
        values = []
        if kwargs:
            conditions = []
            for key, value in kwargs.items():
                if key not in table._columns:
                    raise ValueError(f"Unknown column name: {key}")
                conditions.append(f"{key} = ?")
                values.append()
            sql += " WHERE " + " AND ".join(conditions)

        cursor = self._conn.execute(sql, values)
        row = cursor.fetchone()
        return row[0] if row else 0
        
    def get_table_structure(self, table: Table) -> list[dict]:
        table_name = table.__table_name__ or table.__name__
        cursor = self._conn.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
        
    def update_table_structure(self, table: Type[Table], rebuild=False):
        """
        Update table structure to sync with definition.
        - If rebuild=False: Only add missing columns using ALTER TABLE.
        - If rebuild=True: Rebuild entire table (DROP and recreate).
        """
        table_name = table.__table_name__ or table.__name__

        # 1. Get actual DB columns
        db_columns = self.get_table_structure(table)
        db_columns_list:list[str] = [col["name"] for col in db_columns]
        defined_columns_set:set[str] = set(table._columns.keys())

        update_sqls = self._generator.generate_insert_column(table, db_columns_list)
        if update_sqls is None:
            return
        
        if not rebuild:
            # Try only to add missing columns
            for s in update_sqls:
                self._conn.execute(s)

            if self._auto_commit:
                self._conn.commit()
            return
        
        # 2. create new table / copy data
        self._conn.execute("PRAGMA foreign_keys = OFF;")  # Temporarily disable FK

        tmp_table_name =f"{table_name}_tmp_fix"
        create_sql = self._generator.generate_create_table(table, exist_ok=True).replace(table_name, tmp_table_name)
        self._conn.execute(create_sql)

        shared_keys = set(db_columns_list) & defined_columns_set
        shared_keys_sql = ", ".join(shared_keys)
        copy_sql = (
            f"INSERT INTO {tmp_table_name} ({shared_keys_sql}) "
            f"SELECT {shared_keys_sql} FROM {table_name};"
        )
        self._conn.execute(copy_sql)

        # Drop old table and rename new one
        self._conn.execute(f"DROP TABLE {table_name};")
        self._conn.execute(f"ALTER TABLE {tmp_table_name} RENAME TO {table_name};")

        for sql in self._generator.generate_index(table):
            self._conn.execute(sql)

        self._conn.execute("PRAGMA foreign_keys = ON;")

        if self._auto_commit:
            self._conn.commit()

    def initialize(self, structure_update=False, rebuild=False):
        for table in TableMeta._registry:
            self.create_table(table, True)
            if structure_update:
                self.update_table_structure(table, rebuild)

    def _resolve_filter(self, obj, filter_dict):
        resolved = {}
        for k, v in filter_dict.items():
            if isinstance(v, FieldRef):
                resolved[k] = getattr(obj, v.name)
            else:
                resolved[k] = v
        return resolved

    def _load_relationship(self, obj, _traces=None):
        if _traces is None:
            _traces = {obj.__hash__():obj}

        for name, relation in obj._relationship.items():
            # 解析 filter 裡的 FieldRef
            resolved_filter = self._resolve_filter(obj, relation.filter)
            if relation.plural_data:
                table_data = self.get_all(relation.table, **resolved_filter)
                if not table_data:
                    continue
                for item in table_data:
                    if item.__hash__() in _traces:
                        continue
                    _traces[item.__hash__()] = item
                    self._load_relationship(item, _traces)
            else:
                table_data = self.get_first(relation.table, **resolved_filter)
                if table_data is None:
                    continue
                if table_data.__hash__() in _traces:
                    continue
                _traces[obj.__hash__()] = table_data
                self._load_relationship(table_data, _traces)
            setattr(obj, name, table_data)
            obj._initialized = True