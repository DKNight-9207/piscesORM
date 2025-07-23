# PiscesORM 使用手冊

## 📚 模組總覽
- [column 欄位](#piscesormcolumn-欄位)
- [operator 運算子](#piscesormoperator-運算子)
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
- `type: str`：資料庫端欄位型別
- `primary_key: bool`：是否為主鍵
- `not_null: bool`
- `auto_increment: bool`
- `unique: bool`
- `default: Any`
- `index: bool`

### 🛠 方法

- `to_db(value: Any) -> Any`：轉換 Python 值為 DB 可存格式
- `from_db(value: Any) -> Any`：從 DB 轉回 Python 格式
- `normalize_default(default: Any) -> Any`：預設值預處理

</details>

<details>
<summary><strong>class Integer / Text / Blob / Real</strong></summary>

資料庫內建基本型別，無額外處理。
</details>

<details>
<summary><strong>class Boolean</strong></summary>

官方實現型別，讓資料庫支援布林值
</details>

<details>
<summary><strong>class Json</strong></summary>

官方實現型別，取出後會是字典
</details>

<details>
<summary><strong>class StringArray</strong></summary>

官方實現型別，取出後是`list[str]`
</details>

<details>
<summary><strong>class InterArray</strong></summary>

官方實現型別，取出後是`list[int]`
</details>

<details>
<summary><strong>class EnumType</strong></summary>

官方特殊型別，取出後是會打包成Enum
- `enum: Enum`：目標Enum類
- `store_as_value: bool`：在資料庫用Enum的值處理，或許可以省略一點資料庫占用
- `org_type`：取出後目標的原始型態，若`store_as_value=True`，則要告訴ORM目標是`int`還是什麼類別
</details>

<details>
<summary><strong>class EnumArray</strong></summary>

官方特殊型別，和上者相同，不過取出後會是`list[Enum]`
</details>

<details>
<summary><strong>class Relationship</strong></summary>

此類為關聯記號，資料庫搜尋後隨後會加載指定目標
- `table: Table`：關聯的表
- `plural_data: bool`：一對多關聯，若為`True`時此欄會是`list[Table]`
- `**filter`：過濾條件
</details>

<details>
<summary><strong>class FieldRef</strong></summary>

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
在搜尋條件時，除了可以直接 column=value 做基本`等於`判斷，也可用這裡的標記做進一步的判斷

<details>
<summary><strong>class Operator</strong></summary>

基本運算子，沒有特別意義
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

<strong> class TableMeta </strong>
基本資料表創建器，自訂義基本表時設定metaclass=TableMeta

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
with engine.session() as session:
    session.initialize() # 這樣就會自動創建資料庫了
```

---