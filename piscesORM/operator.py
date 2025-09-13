# 邏輯運算子
class LogicalOperator:
    def __init__(self, first_part, second_part):
        self.first_part = first_part
        self.second_part = second_part
        
    def __or__(self, value):
        return OR(self, value)

    def __and__(self, value):
        return AND(self, value)

class GreaterThan(LogicalOperator): pass  # >
class GreaterEqual(LogicalOperator): pass # >=
class LessThan(LogicalOperator): pass     # <
class LessEqual(LogicalOperator): pass    # <=
class Equal(LogicalOperator): pass        # ==
class NotEqual(LogicalOperator): pass     # !=
class In_(LogicalOperator): pass          # in
class Like(LogicalOperator): pass         # like
class ILike(LogicalOperator): pass        # ilik
class OR(LogicalOperator): pass           # |
class AND(LogicalOperator): pass          # &


SQLITE_TRANSLATE_MAP = {
    GreaterThan: ">",
    GreaterEqual: ">=",
    LessThan: "<",
    LessEqual: "<=",
    Equal: "=",
    NotEqual: "!=",
    In_: "IN",
    Like: "LIKE",
    ILike: "LIKE", # 不支援ilike，以like代替
    OR: "OR",
    AND: "AND"
}

class MathOperator:
    def __init__(self, val_a, val_b):
        self.val_a = val_a
        self.val_b = val_b
class SelfColumn: pass

class Plus(MathOperator): pass    # a + b
class Minus(MathOperator): pass   # a - b
class Times(MathOperator): pass   # a * b
class Divided(MathOperator): pass # a / b
class Modulo(MathOperator): pass  # a % b
class ABS(MathOperator): pass     # |a|
class Celing(MathOperator): pass  # 無條件進位(a)
class Floor(MathOperator): pass   # 取整(a)
class Round(MathOperator): pass   # 四捨五入(a)
class Power(MathOperator): pass   # a ^ b
class Sqrt(MathOperator): pass    # √a