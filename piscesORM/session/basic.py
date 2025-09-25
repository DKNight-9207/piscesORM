from __future__ import annotations
from typing import Type, List, Any
from abc import ABC, abstractmethod
from ..table import Table

class AsyncBaseSession(ABC):
    def __init__(self, connection: Any, mode="r", auto_commit: bool = True):
        """mode: only work on 'Application Lock' engine"""
        self._conn = connection
        self.mode = mode
        self._auto_commit = auto_commit

    @abstractmethod
    async def on_connected(self): ...

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

    @abstractmethod
    async def get_all(self, table: Type[Table], *filters, load_relationships=True, read_only=False, ref_obj:Table=None) -> List[Table]: ...

    @abstractmethod
    async def get_first(self, table: Type[Table], *filters, load_relationships=True, read_only=False, ref_obj:Table=None) -> Table: ...

    @abstractmethod
    async def update(self, obj: Table, merge: bool = False): ...

    @abstractmethod
    async def delete(self, obj: Table): ...

    @abstractmethod
    def count(self, table: Type[Table], filters = None): ...


class SyncBaseSession(ABC):
    def __init__(self, connection: Any, auto_commit: bool = True):
        self._conn = connection
        self._auto_commit = auto_commit

    @abstractmethod
    def on_connected(self): ...

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

    @abstractmethod
    def get_all(self, table: Type[Table], *filters, load_relationships=True, read_only=False, ref_obj:Table=None) -> List[Table]: ...

    @abstractmethod
    def get_first(self, table: Type[Table], *filters, load_relationships=True, read_only=False, ref_obj:Table=None) -> Table: ...

    @abstractmethod
    def update(self, obj: Table, merge: bool = False): ...

    @abstractmethod
    def delete(self, obj: Table): ...

    @abstractmethod
    def count(self, table: Type[Table], filters = None): ...
