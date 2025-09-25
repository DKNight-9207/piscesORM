# PiscesORM 使用手冊

## 📚 模組總覽
- [column 欄位](#piscesormcolumn-欄位)
- [LogicalOperator 運算子](#piscesormLogicalOperator-運算子)
- [table 資料表](#piscesormtable-資料表)
- [engine 引擎]()
- [session ]()
- [lock 鎖]()
- [generator 語句產生器]()
- [errors 錯誤]()

---

## piscesORM.column 欄位

<details>
<summary><strong>class Column</strong></summary>

此類為基本欄位，如果要自訂義資料輸入/輸出，請繼承它
- `type: str | dict[str, str]`：資料庫端欄位型別，傳入`str`代表對所有資料庫都使用此型態
- `primary_key: bool`：是否為主鍵
- `not_null: bool`:是否不允許空值
- `auto_increment: bool`:自動增加
- `unique: bool`:是否唯一
- `default: Any`:預設值
- `index: bool`:索引

### 🛠 方法

- `to_db(value: Any) -> Any`：轉換 Python 值為 DB 可存格式
- `from_db(value: Any) -> Any`：從 DB 轉回 Python 格式
- `normalize_default(default: Any) -> Any`：預設值預處理

</details>

<details>
<summary><strong>class piscesORM.column.Integer</strong></summary>
資料庫內建基本整數型別

額外功能:
- `enum: IntEnum|IntFlag`: 自動把內容打包成Intenum/IntFlag。
</details>

<details>
<summary><strong>class piscesORM.column.Text</strong></summary>
資料庫內建基本文字型別

額外功能:
- `enum: StrEnum`: 自動把內容打包成StrEnum。
</details>

<details>
<summary><strong>class piscesORM.column.Blob</strong></summary>
資料庫內建基本二進制型別。
</details>

<details>
<summary><strong>class piscesORM.column.Real</strong></summary>
資料庫內建基本浮點數型別。
</details>

<details>
<summary><strong>class piscesORM.column.Numeric</strong></summary>
資料庫內建基本高精度浮點數型別。
</details>

<details>
<summary><strong>class piscesORM.column.Boolean</strong></summary>

官方實現型別，讓資料庫支援布林值
</details>

<details>
<summary><strong>class piscesORM.column.Json</strong></summary>

官方實現型別，取出後會是`dict`
</details>

<details>
<summary><strong>class piscesORM.column.StringArray</strong></summary>

官方實現型別，取出後是`list[str]`
</details>

<details>
<summary><strong>class piscesORM.column.InterArray</strong></summary>

官方實現型別，取出後是`list[int]`
</details>

<details>
<summary><strong>class piscesORM.column.EnumType</strong></summary>

官方特殊型別，取出後是會打包成Enum
- `enum: Enum`：目標Enum類
- `store_as_value: bool`：在資料庫用Enum的值處理，或許可以省略一點資料庫占用
- `org_type`：取出後目標的原始型態，若`store_as_value=True`，則要告訴ORM目標是`int`還是什麼類別
</details>

<details>
<summary><strong>class piscesORM.column.EnumArray</strong></summary>

官方特殊型別，和上者相同，不過取出後會是`list[Enum]`
</details>

<details>
<summary><strong>class piscesORM.column.Time</strong></summary>

官方特殊型別，取出後會是`piscesORM.PiscesTime`。簡單來說就是加了額外方便功能的datetime
</details>

<details>
<summary><strong>class piscesORM.column.Relationship</strong></summary>

此類為關聯記號，資料庫搜尋後隨後會加載指定目標
- `table: Table`：關聯的表
- `plural_data: bool`：一對多關聯，若為`True`時此欄會是`list[Table]`
- `**filter`：過濾條件
</details>

<details>
<summary><strong>class piscesORM.column.FieldRef</strong></summary>

此類為關聯特殊標記，代表關聯值來自自身，應該事後解析
- `name: str`：關聯的自身欄位
```py
class Author(Table):
    name: str = Text()
    age: int = Integer()

class Book(Table):
    author_name: str = Text()
    author: Author = Relationship(Author, name = FieldRef("author_name"))
    # 這邊的意思是，從Author這個表尋找 name = self.author_name 的資料
```
</details>

---

## piscesORM.operator 運算子
這個東西和內部實現有關，且主要作為標籤用。應用層僅需對作為基底的Operator有所了解即可

<details>
<summary><strong>class piscesORM.operator.Operator</strong></summary>

基本運算子標籤

- `abs()`: 表示取絕對值
- `ceiling()`: 表示向上取整
- `floor()`: 表示向下取整
- `round()`: 表示四捨五入到整數
- `sqrt()`: 表示取更號
- `isin(value: list)`: 判斷一個值是否存在於一組給定的列表中。
- `|`: 或運算
- `&`: 且運算
- `+`: 加運算
- `-`: 減運算
- `*`: 乘運算
- `/`: 除運算
- `//`: 整數除法。`a//b`等價於`FLOOR(a/b)`
- `%`: 取餘運算
- `**`: 指數運算

註：由於python解釋器解析時會從左到右，因此請多多善加利用括號，否則容易報錯
</details>

<details>
<summary><strong>class LogicalOperator</strong></summary>

基本運算子標籤，代表這是邏輯運算子
</details>

<details>
<summary><strong>class  MathOperator</strong></summary>

基本運算子標籤，代表這是數學運算子
</details>

<details>
<summary><strong>class  OneInputMathOperator</strong></summary>

基本運算子標籤，代表這是數學運算子，且僅允許一個輸入
</details>

<details>
<summary><strong>class GreaterThan</strong></summary>

`大於`運算子，在SQL中代表 `>`。另有縮寫`Gt`
</details>

<details>
<summary><strong>class GreaterEqual</strong></summary>

`大於等於`運算子，在SQL中代表 `>=`。另有縮寫`Gte`
</details>

<details>
<summary><strong>class LessThan</strong></summary>

`小於`運算子，在SQL中代表 `<`。另有縮寫`Lt`
</details>

<details>
<summary><strong>class LessEqual</strong></summary>

`小於等於`運算子，在SQL中代表 `<=`。另有縮寫`Lte`
</details>

<details>
<summary><strong>class Equal</strong></summary>

`等於`運算子，在SQL中代表 `=`。另有縮寫`Eq`
~~話說你用這個似乎多此一舉~~
</details>

<details>
<summary><strong>class NotEqual</strong></summary>

`不等於`運算子，在SQL中代表 `!=`。另有縮寫`Ne`
</details>

---

## piscesORM.table 資料表

<strong> class Table </strong>
基本資料表，創建表時請繼承它

### 🔧 資料表設定
- `__abstract__: bool`：為`False`時，ORM不會自動創建此表
- `__table_name__: str`：自訂義資料表名稱，沒指定時會是類名
- `__no_primary_key__: bool`：為`True`時，ORM會允許該表沒有主鍵，不過會失去"ORM更新資料"功能

### 基本用法
```py
from __future__ import annotations
from piscesORM.table import Table
from piscesORM.column import Text, Integer 
from piscesORM.engine import SyncSQLiteEngine

class Log(Table):
    __table_name__ = "log"
    __no_primary_key__ = True

    time: int = Integer()
    level: str = Text()
    message: str = Text()

class MemberData(Table):
    __table_name__ = "member_data"

    guild_id: int = Integer(primary_key=True)
    member_id: int = Integer(primary_key=True)

engine = SyncSQLiteEngine("./database.db")
engine.initilize()# 這樣就會自動創建資料庫了
```
---

## piscesORM.engine 引擎
為了簡化資料庫設定的上手難度，所以具體的資料庫類型等並非像其他資料庫通過網址欄位控制，而是通過選擇引擎來實現

<details>
<summary><strong>class SyncBaseEngine/AsyncBaseEngine 基本同步/異步引擎</strong></summary>
這是一個抽象基底類，用來規範統一基本接口
</details>

<details>
<summary><strong>class AsyncSQLiteEngine SQLite異步引擎</strong></summary>

### 初始化欄位：
- `db_path`: 指定 SQLite 檔案的位置，預設為`:memory:`，代表使用內存模式。

### 方法：
- `session`: 這會回傳一個上下文管理器，所以要用`async with engine.session() as s:`來使用。會自動處理連線的回收等事務
- `get_session`: 這會回傳一個 Session 物件，這意味著你需要自行管理 Session生命週期
- `initialize`: 執行初始化
- `sync_initialize`: 和`initialize`一樣，只是用了`asyncio.run()`包裝，免去使用`await`
    * `structure_update`: 若結構有異動，是否更新？預設為`False`
    * `rebuild`: 是否使用重建來解決異動？預設為`False`，但因此只能新增多出來的欄位，不能刪除舊欄位
    * 回傳值: SyncSQLiteSession()/AsyncSQLiteSession()

</details>

<details>
<summary><strong>class SyncSQLiteLockEngine SQLite上鎖異步引擎</strong></summary>

注意：這個鎖的原理是悲觀鎖，所以對效能影響略大，但優點是會排隊處理。


### 初始化欄位：
- `db_path`: 指定 SQLite 檔案的位置，預設為`:memory:`，代表使用內存模式。
- `auto_release`: 設定鎖過期的時間，單位為秒，預設為`0`，表示不啟用。雖然可以確保系統不會完全阻塞，但不保證資源不洩漏，因此應該僅在開發階段使用
- `read_lock`: 預設為`False`，表示讀取不用鎖，設為`True`時，會進一步保證純讀取時也有資料原子性，但相對性能會下降。

### 方法：
- `session`: 這會回傳一個上下文管理器，所以要用`async with engine.session() as s:`來使用。會自動處理連線的回收等事務
- `get_session`: 這會回傳一個 Session 物件，這意味著你需要自行管理 Session生命週期
    * `mode`: 啟動模式。
        - `r`: 預設值，表示僅讀取，若嘗試寫入資料庫會報錯。
        - `w`: 雖然寫作`w`，但實際上也可讀取。此次連線會為每個搜尋上鎖。

- `initialize`: 執行初始化
- `sync_initialize`: 和`initialize`一樣，只是用了`asyncio.run()`包裝，免去使用`await`
    * `structure_update`: 若結構有異動，是否更新？預設為`False`
    * `rebuild`: 是否使用重建來解決異動？預設為`False`，但因此只能新增多出來的欄位，不能刪除舊欄位
    * 回傳值: AsyncSQLiteLockSession()

</details>