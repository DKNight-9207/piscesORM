from .. import *
from ...column import Column, FieldRef
from ...table import Table
from ... import errors

SQLITE_TRANSLATE_MAP = {
    # 邏輯
    GreaterThan: ">",
    GreaterEqual: ">=",
    LessThan: "<",
    LessEqual: "<=",
    Equal: "=",
    NotEqual: "!=",
    IsIn: "IN",
    Like: "LIKE",
    ILike: "LIKE",  # SQLite 沒有 ILIKE，只能轉 LIKE
    OR: "OR",
    AND: "AND",
    IsNull: "IS NULL",
    IsNotNull: "IS NOT NULL",
    Between: "BETWEEN",

    # 數學
    Plus: "+",
    Minus: "-",
    Multiply: "*",
    Divide: "/",
    Modulo: "%",
    Power: "POWER",
    ABS: "ABS",
    Ceiling: "CEIL",
    Floor: "FLOOR",
    Round: "ROUND",
    Sqrt: "SQRT"
}


def translate_sqlite(op: Operator, ref_obj:Table=None) -> str:
    """把 Operator 物件轉換成 SQLite 可執行的 SQL (WHERE 子句片段)"""
    t = SQLITE_TRANSLATE_MAP.get(type(op))
    parts = []

    for p in op.parts:
        if isinstance(p, Operator):
            translate_part = translate_sqlite(p)
            if isinstance(p, (OR, AND)):
                parts.append(f"({translate_part})")
            else:
                parts.append(translate_part)
        elif isinstance(p, Column):
            parts.append(f'"{p._name}"')
        elif isinstance(p, FieldRef):
            if ref_obj is None:
                raise errors.MissingReferenceObject()
            parts.append(f"'{getattr(ref_obj, p.name)}'")
        else:
            parts.append(repr(p))

    # --- 單輸入函數 ---
    if isinstance(op, OneInputMathOperator):
        return f"{t}({parts[0]})"
    
    # --- 雙輸入/多輸入邏輯 ---
    if isinstance(op, LogicalOperator):
        if isinstance(op, IsNull):
            return f"{parts[0]} IS NULL"
        if isinstance(op, IsNotNull):
            return f"{parts[0]} IS NOT NULL"
        if isinstance(op, IsIn):
            return f"{parts[0]} IN ({', '.join(parts[1:])})"
        if isinstance(op, Between):
            if len(parts) != 3:
                raise ValueError("Between requires exactly 3 parts")
            return f"{parts[0]} BETWEEN {parts[1]} AND {parts[2]}"
        if isinstance(op, (OR, AND, GreaterThan, GreaterEqual,
                           LessThan, LessEqual, Equal, NotEqual,
                           Like, ILike)):
            return f"{parts[0]} {t} {parts[1]}"

    # --- 數學運算 ---
    if isinstance(op, MathOperator):
        if isinstance(op, Power):
            return f"{t}({parts[0]}, {parts[1]})"
        return f"({parts[0]} {t} {parts[1]})"

    # --- 沒對應 ---
    raise RuntimeError(f"unknown optrator in translate\n - object: {op}\n - type: {type(op)}")


def translate_sqlite_security(op: Operator, ref_obj:Table=None) -> tuple[str, list]:
    t = SQLITE_TRANSLATE_MAP.get(type(op))
    sql_parts = []
    params = []

    for p in op.parts:
        if isinstance(p, Operator):
            sql_part, sub_params = translate_sqlite_security(p, ref_obj)
            if isinstance(p, (OR, AND)):
                sql_parts.append(f"({sql_part})")
            else:
                sql_parts.append(sql_part)
            params.extend(sub_params)
        elif isinstance(p, Column):
            sql_parts.append(f'"{p._name}"')
        elif isinstance(p, FieldRef):
            if ref_obj is None:
                raise errors.MissingReferenceObject()
            sql_parts.append("?")
            params.append(getattr(ref_obj, p.name, None))
        else:
            sql_parts.append("?")
            params.append(p)

    # --- 單輸入函數 ---
    if isinstance(op, OneInputMathOperator):
        return f"{t}({sql_parts[0]})", params

    # --- 邏輯運算 ---
    if isinstance(op, LogicalOperator):
        if isinstance(op, IsNull):
            return f"{sql_parts[0]} IS NULL", params
        if isinstance(op, IsNotNull):
            return f"{sql_parts[0]} IS NOT NULL", params
        if isinstance(op, IsIn):
            placeholders = ", ".join("?" for _ in sql_parts[1:])
            return f"{sql_parts[0]} IN ({placeholders})", params
        if isinstance(op, Between):
            return f"{sql_parts[0]} BETWEEN {sql_parts[1]} AND {sql_parts[2]}", params
        if isinstance(op, (OR, AND, GreaterThan, GreaterEqual,
                           LessThan, LessEqual, Equal, NotEqual,
                           Like, ILike)):
            return f"{sql_parts[0]} {t} {sql_parts[1]}", params

    # --- 數學運算 ---
    if isinstance(op, MathOperator):
        if isinstance(op, Power):
            return f"{t}({sql_parts[0]}, {sql_parts[1]})", params
        return f"({sql_parts[0]} {t} {sql_parts[1]})", params

    raise RuntimeError(f"unknown operator in translate_sqlite_security\n - object: {op}\n - type: {type(op)}")

