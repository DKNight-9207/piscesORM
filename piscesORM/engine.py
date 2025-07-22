from __future__ import annotations
from unittest import result
import aiosqlite
import sqlite3
from typing import Type, List, Any
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


class SyncBaseEngine(ABC):
    def __init__(self, db_path: str = ":memory:", auto_commit: bool = True):
        self.db_path = db_path
        self._auto_commit = auto_commit

    @abstractmethod
    @contextmanager
    def session(self, mode="r", auto_commit:bool = None) -> session.SyncBaseSession: ...

    @abstractmethod
    async def get_session(self, mode="r", auto_commit:bool = None) -> session.SyncBaseSession: ...


class AsyncSQLiteEngine(AsyncBaseEngine):
    def __init__(self, db_path = ':memory:', auto_commit:bool = None):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None
        self._auto_commit = auto_commit
        self._conn_pool =[]

    @asynccontextmanager
    async def session(self, mode="r", auto_commit = None):
        _conn = None
        
        try:
            _conn = await aiosqlite.connect(self.db_path)
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
        _conn = await aiosqlite.connect(self.db_path)
        return session.AsyncSQLiteSession(_conn, mode, auto_commit if auto_commit is not None else self._auto_commit)

class SyncSQLiteEngine(SyncBaseEngine):
    def __init__(self, db_path = ":memory:", auto_commit = True):
        super().__init__(db_path, auto_commit)

    @contextmanager
    def session(self, mode="r", auto_commit = None):
        _conn = None

        try:
            _conn = sqlite3.connect(self.db_path)
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
        _conn = sqlite3.connect(self.db_path)
        return session.SyncSQLiteSession(_conn, mode, auto_commit if auto_commit is not None else self._auto_commit)

