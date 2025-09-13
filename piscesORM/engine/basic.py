from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod
from .. import session
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