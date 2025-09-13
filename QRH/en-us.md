# PiscesORM User Manual

## 📚 Module Overview
- [column](#piscesormcolumn)
- [LogicalOperator](#piscesormLogicalOperator)
- [table](#piscesormtable)
- [engine]()
- [session]()
- [lock]()
- [generator]()
- [errors]()

---

## piscesORM.column

<details>
<summary><strong>class Column</strong></summary>

Basic column class. To customize input/output, inherit this class.
- `type: str`: Database column type
- `primary_key: bool`: Is primary key
- `not_null: bool`
- `auto_increment: bool`
- `unique: bool`
- `default: Any`
- `index: bool`

### 🛠 Methods

- `to_db(value: Any) -> Any`: Convert Python value to DB format
- `from_db(value: Any) -> Any`: Convert DB value to Python format
- `normalize_default(default: Any) -> Any`: Preprocess default value

</details>
<details>
<summary><strong>class Relationship</strong></summary>

Relationship marker. After DB query, loads the target.
- `table: Table`: Related table
- `plural_data: bool`: One-to-many relationship, if `True` this field is `list[Table]`
- `**filter`: Filter conditions
</details>

<details>
<summary><strong>class FieldRef</strong></summary>

Special relationship marker, means the value comes from itself and should be resolved later.
- `name: str`: Related field name
</details>

<details>
<summary><strong>class Integer / Text / Blob / Real</strong></summary>

Built-in DB types, no extra handling.
</details>

<details>
<summary><strong>class Boolean</strong></summary>

Official type, enables boolean support in DB.
</details>

<details>
<summary><strong>class Json</strong></summary>

Official type, returns a dictionary after fetching.
</details>

<details>
<summary><strong>class StringArray</strong></summary>

Official type, returns `list[str]` after fetching.
</details>

<details>
<summary><strong>class InterArray</strong></summary>

Official type, returns `list[int]` after fetching.
</details>

<details>
<summary><strong>class EnumType</strong></summary>

Special type, returns Enum after fetching.
- `enum: Enum`: Target Enum class
- `store_as_value: bool`: Store Enum value in DB, may save space
- `org_type`: Target original type after fetching, if `store_as_value=True`, tell ORM the type (e.g. `int`)
</details>

<details>
<summary><strong>class EnumArray</strong></summary>

Special type, same as above, but returns `list[Enum]`
</details>

---

## piscesORM.LogicalOperator

When searching, you can use column=value for basic `equal` check, or use these markers for advanced conditions.

<details>
<summary><strong>class LogicalOperator</strong></summary>

Basic LogicalOperator, no special meaning.
</details>

<details>
<summary><strong>class GreaterThan</strong></summary>

`Greater than` LogicalOperator, SQL `>`. Alias: `Gt`
</details>

<details>
<summary><strong>class GreaterEqual</strong></summary>

`Greater or equal` LogicalOperator, SQL `>=`. Alias: `Gte`
</details>

<details>
<summary><strong>class LessThan</strong></summary>

`Less than` LogicalOperator, SQL `<`. Alias: `Lt`
</details>

<details>
<summary><strong>class LessEqual</strong></summary>

`Less or equal` LogicalOperator, SQL `<=`. Alias: `Lte`
</details>

<details>
<summary><strong>class Equal</strong></summary>

`Equal` LogicalOperator, SQL `=`. Alias: `Eq`
~~You probably don't need this one~~
</details>

<details>
<summary><strong>class NotEqual</strong></summary>

`Not equal` LogicalOperator, SQL `!=`. Alias: `Ne`
</details>

---

## piscesORM.table

<strong> class TableMeta </strong>
Basic table creator. Set metaclass=TableMeta when defining custom tables.

<strong> class Table </strong>
Basic table class. Inherit this class to create tables.

### 🔧 Table Settings
- `__abstract__: bool`: If `False`, ORM will not auto-create this table
- `__table_name__: str`: Custom table name, defaults to class name
- `__no_primary_key__: bool`: If `True`, ORM allows table without primary key, but disables "ORM update" feature

---
