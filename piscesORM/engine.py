from __future__ import annotations
from unittest import result
import aiosqlite
import sqlite3
import asyncio
from typing import Type, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from .table import Table, TableMeta
from .column import Column
from . import generator
from . import session
from contextlib import contextmanager, asynccontextmanager

class EngineType(Enum):
    SQLite = "sqlite"
    MySQL = "mysql"

class AsyncBaseEngine(ABC):
    def __init__(self, db_path: str = ":memory:", mode="r", auto_commit: bool = True):
        """mode: only work on 'Application Lock' engine"""
        self.mode = mode
        self.db_path = db_path
        self._auto_commit = auto_commit

    @abstractmethod
    @asynccontextmanager
    async def session(self, mode="r", auto_commit:bool = None) -> session.AsyncBaseSession: ...

    @abstractmethod
    async def get_session(self, mode="r", auto_commit:bool = None) -> session.AsyncBaseSession: ...

    @abstractmethod
    async def initialize(self) -> None: ...


class SyncBaseEngine(ABC):
    def __init__(self, db_path: str = ":memory:", auto_commit: bool = True):
        self.db_path = db_path
        self._auto_commit = auto_commit

    @abstractmethod
    @contextmanager
    def session(self, mode="r", auto_commit:bool = None) -> session.SyncBaseSession: ...

    @abstractmethod
    def get_session(self, mode="r", auto_commit:bool = None) -> session.SyncBaseSession: ...

    @abstractmethod
    def initialize(self) -> None: ...


class AsyncSQLiteEngine(AsyncBaseEngine):
    def __init__(self, db_path = ':memory:', auto_commit:bool = None):
        if db_path == ':memory:':
            self.db_path = 'file::memory:?cache=shared'
            self._mem_mode = True
        else:
            self.db_path = db_path
            self._mem_mode = False
        self._conn: Optional[aiosqlite.Connection] = None
        self._auto_commit = auto_commit
        self._conn_pool = []
        self._protect_session = None

    @asynccontextmanager
    async def session(self, mode="r", auto_commit = None):
        _conn = None
        
        try:
            _conn = await aiosqlite.connect(self.db_path, uri=self._mem_mode)
            await _conn.execute("PRAGMA foreign_keys = ON")
            __session = session.AsyncSQLiteSession(_conn, mode, auto_commit if auto_commit is not None else self._auto_commit)
            yield __session
        except Exception:
            if _conn:
                await _conn.rollback()
            raise
        finally:
            if _conn:
                await _conn.close()

    async def get_session(self, mode="r", auto_commit = None):
        _conn = await aiosqlite.connect(self.db_path, uri=self._mem_mode)
        return session.AsyncSQLiteSession(_conn, mode, auto_commit if auto_commit is not None else self._auto_commit)
    
    async def initialize(self, structure_update=False, rebuild=False):
        _conn = await aiosqlite.connect(self.db_path, uri=self._mem_mode)
        await _conn.execute("PRAGMA foreign_keys = ON")
        __session = session.AsyncSQLiteSession(_conn, "w", False)
        await __session.initialize(structure_update, rebuild)
        if self._mem_mode:
            self._protect_session = __session

    def sync_initialize(self, structure_update=False, rebuild=False):
        asyncio.run(self.initialize(structure_update, rebuild))

class SyncSQLiteEngine(SyncBaseEngine):
    def __init__(self, db_path = ":memory:", auto_commit = True):
        if db_path == ':memory:':
            self.db_path = 'file::memory:?cache=shared'
            self._mem_mode = True
        else:
            self.db_path = db_path
            self._mem_mode = False
        self._auto_commit = auto_commit

    @contextmanager
    def session(self, mode="r", auto_commit = None):
        _conn = None

        try:
            _conn = sqlite3.connect(self.db_path, uri=self._mem_mode)
            _conn.execute("PRAGMA foreign_keys = ON")
            __session = session.SyncSQLiteSession(_conn, mode, auto_commit if auto_commit is not None else self._auto_commit)
            yield __session
        except Exception:
            if _conn:
                _conn.rollback()
            raise
        finally:
            if _conn:
                _conn.close()

    def get_session(self, mode="r", auto_commit = None):
        _conn = sqlite3.connect(self.db_path, uri=self._mem_mode)
        return session.SyncSQLiteSession(_conn, mode, auto_commit if auto_commit is not None else self._auto_commit)
    
    def initialize(self, structure_update=False, rebuild=False):
        _conn = sqlite3.connect(self.db_path, uri=self._mem_mode)
        _conn.execute("PRAGMA foreign_keys = ON")
        __session = session.SyncSQLiteSession(_conn, "w", False)
        __session.initialize(structure_update, rebuild)
        if self._mem_mode:
            self._protect_session = __session


