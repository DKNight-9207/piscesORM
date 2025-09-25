class Operator:
    def __init__(self, *parts):
        if not parts:
            raise ValueError("Operator must have at least one part")
        self.parts = parts

    def abs(self):
        return ABS(self)
    
    def ceiling(self):
        return Ceiling(self)
    
    def floor(self):
        return Floor(self)
    
    def round(self):
        return Round(self)
    
    def sqrt(self):
        return Sqrt(self)
    
    def isin(self, value):
        return IsIn(self, value)
    
    # 快速調用 (特殊方法)
    def __or__(self, value):
        return OR(self, value)

    def __and__(self, value):
        return AND(self, value)

    def __eq__(self, value):
        return Equal(self, value)
    
    def __ne__(self, value):
        return NotEqual(self, value)
        
    def __gt__(self, value):
        return GreaterThan(self, value)
        
    def __ge__(self, value):
        return GreaterEqual(self, value)
    
    def __lt__(self, value):
        return LessThan(self, value)
        
    def __le__(self, value):
        return LessEqual(self, value)
        
    def __contains__(self, value):
        return self.isin(value)
    
    def __add__(self, value):
        return Plus(self, value)
    
    def __sub__(self, value):
        return Minus(self, value)
    
    def __mul__(self, value):
        return Multiply(self, value)
    
    def __truediv__(self, value):
        return Divide(self, value)
    
    def __floordiv__(self, value):
        return Floor(self/value)
    
    def __mod__(self, value):
        return Modulo(self, value)
    
    def __pow__(self, value):
        return Power(self, value)
    
class LogicalOperator(Operator): pass
class MathOperator(Operator): pass
class OneInputMathOperator(MathOperator):
    def __init__(self, first_part, second_part=None):
        if second_part is not None:
            raise ValueError("second_part should be None")
        super().__init__(first_part, second_part)
class SelfColumn: pass

class GreaterThan(LogicalOperator): pass  # >
class GreaterEqual(LogicalOperator): pass # >=
class LessThan(LogicalOperator): pass     # <
class LessEqual(LogicalOperator): pass    # <=
class Equal(LogicalOperator): pass        # ==
class NotEqual(LogicalOperator): pass     # !=
class IsIn(LogicalOperator): pass         # in
class Like(LogicalOperator): pass         # like
class ILike(LogicalOperator): pass        # ilike
class OR(LogicalOperator): pass           # |
class AND(LogicalOperator): pass          # &

class IsNull(LogicalOperator): pass       # IS NULL
class IsNotNull(LogicalOperator): pass    # IS NOT NULL
class Between(LogicalOperator): pass

class Plus(MathOperator): pass            # a + b
class Minus(MathOperator): pass           # a - b
class Multiply(MathOperator): pass        # a * b
class Divide(MathOperator): pass          # a / b
class Modulo(MathOperator): pass          # a % b
class Power(MathOperator): pass           # a ^ b
class ABS(OneInputMathOperator): pass     # |a|
class Ceiling(OneInputMathOperator): pass # 無條件進位(a)
class Floor(OneInputMathOperator): pass   # 取整(a)
class Round(OneInputMathOperator): pass   # 四捨五入(a)
class Sqrt(OneInputMathOperator): pass    # √a