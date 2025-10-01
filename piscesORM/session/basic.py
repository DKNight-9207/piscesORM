from __future__ import annotations
from typing import Type,  Any
from abc import ABC, abstractmethod
from ..table import Table
from ..operator import Operator
from ..column import Column

class AsyncBaseSession(ABC):
    def __init__(self, connection: Any, mode="r", auto_commit: bool = True):
        """mode: only work on 'Application Lock' engine"""
        self._conn = connection
        self.mode = mode
        self._auto_commit = auto_commit

    @abstractmethod
    async def on_connected(self) -> bool:
        """
        檢查資料庫連線
        """ 
        ...

    @abstractmethod
    async def execute(self, sql, value: Any) -> Any:
        """
        直接傳遞SQL指令
        """
        ...

    @abstractmethod
    async def commit(self): 
        """
        提交
        """
        ...

    @abstractmethod
    async def rollback(self):
        """
        回滾
        """
        ...

    @abstractmethod
    async def initialize(self, structure_update=False, rebuild: bool = False): 
        """
        執行初始化(創建所有表、結構更新)
        """
        ...

    @abstractmethod
    async def update_table_structure(self, table: Type[Table], rebuild: bool = False): 
        """
        更新表結構
        """
        ...

    @abstractmethod
    async def create_table(self, table: Type[Table], exist_ok: bool = False):
        """
        創建表
        """
        ...

    @abstractmethod
    async def create_join_table(self, table_1:Type[Table], table_2:Type[Table], exist_ok:bool = False): 
        """
        創建多對多關聯表
        """
        ...

    @abstractmethod
    async def drop_table(self, table:Type[Table]|str):
        """
        刪除表
        """
        ...

    @abstractmethod
    async def insert(self, obj: Table): 
        """
        插入欄
        """
        ...

    @abstractmethod
    async def insert_many(self, objs: list[Table]): 
        """
        批量插入
        """
        ...

    @abstractmethod
    async def get_all(self, table: Type[Table], 
                      *filters:Operator,
                      order_by:str|Column|list[str]|list[Column],
                      limit:int=None,
                      **kwargs) -> list[Table]: 
        """
        搜尋所有符合條件的
        """
        ...

    @abstractmethod
    async def get_first(self, table: Type[Table], 
                        *filters:Operator,
                        order_by:str|Column|list[str]|list[Column],
                        limit:int=None,
                        **kwargs) -> Table: 
        """
        搜尋一個符合條件的
        """
        ...

    @abstractmethod
    async def update(self, table: Type[Table], *filters:Operator, **set:Operator): 
        """
        根據過濾器更新
        """
        ...

    @abstractmethod
    async def merge(self, obj: Table, cover: bool = False): 
        """
        根據物件更新
        """
        ...

    @abstractmethod
    async def delete_object(self, obj: Table | list[Table]): 
        """
        根據物件刪除
        """
        ...

    @abstractmethod
    async def delete(self, table:Type[Table], *filter: Operator):
        """
        根據條件刪除
        """
        ...

    @abstractmethod
    async def count(self, table: Type[Table], *filters: Operator) -> int: 
        """
        計算符合的物件數量
        """
        ...


class SyncBaseSession(ABC):
    def __init__(self, connection: Any, mode:str = "r", auto_commit: bool = True):
        self._conn = connection
        self.mode = mode
        self._auto_commit = auto_commit

    @abstractmethod
    def on_connected(self) -> bool:
        """
        檢查資料庫連線
        """ 
        ...

    @abstractmethod
    def execute(self, sql, value: Any) -> Any:
        """
        直接傳遞SQL指令
        """
        ...

    @abstractmethod
    def commit(self): 
        """
        提交
        """
        ...

    @abstractmethod
    def rollback(self):
        """
        回滾
        """
        ...

    @abstractmethod
    def initialize(self, structure_update=False, rebuild: bool = False): 
        """
        執行初始化(創建所有表、結構更新)
        """
        ...

    @abstractmethod
    def update_table_structure(self, table: Type[Table], rebuild: bool = False): 
        """
        更新表結構
        """
        ...

    @abstractmethod
    def create_table(self, table: Type[Table], exist_ok: bool = False):
        """
        創建表
        """
        ...

    @abstractmethod
    def create_join_table(self, table_1:Type[Table], table_2:Type[Table], exist_ok:bool = False): 
        """
        創建多對多關聯表
        """
        ...

    @abstractmethod
    def drop_table(self, table:Type[Table]|str):
        """
        刪除表
        """
        ...

    @abstractmethod
    def insert(self, obj: Table): 
        """
        插入欄
        """
        ...

    @abstractmethod
    def insert_many(self, objs: list[Table]): 
        """
        批量插入
        """
        ...

    @abstractmethod
    def get_all(self, table: Type[Table], *filters:Operator, order_by:str|list[str]=None, limit:int=None, **kwargs) -> list[Table]: 
        """
        搜尋所有符合條件的
        """
        ...

    @abstractmethod
    def get_first(self, table: Type[Table], *filters:Operator, order_by:str|list[str]=None, limit:int=None, **kwargs) -> Table: 
        """
        搜尋一個符合條件的
        """
        ...

    @abstractmethod
    def update(self, table: Type[Table], *filters:Operator, **set:Operator): 
        """
        根據過濾器更新
        """
        ...

    @abstractmethod
    def merge(self, obj: Table, cover: bool = False): 
        """
        根據物件更新
        """
        ...

    @abstractmethod
    def delete_object(self, obj: Table | list[Table]): 
        """
        根據物件刪除
        """
        ...

    @abstractmethod
    def delete(self, table:Type[Table], *filter: Operator):
        """
        根據條件刪除
        """
        ...

    @abstractmethod
    def count(self, table: Type[Table], *filters: Operator) -> int: 
        """
        計算符合的物件數量
        """
        ...

    
