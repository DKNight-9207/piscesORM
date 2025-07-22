
class Operator:
    def __init__(self, value):
        self.value = value

class GreaterThan(Operator): pass
class GreaterEqual(Operator): pass
class LessThan(Operator): pass
class LessEqual(Operator): pass
class Equal(Operator): pass
class NotEqual(Operator): pass
#class In_(Operator): pass
#class Like(Operator): pass
#class ILike(Operator): pass

# 縮寫別名版本
Gt = GreaterThan
Gte = GreaterEqual
Lt = LessThan
Lte = LessEqual
Eq = Equal
Ne = NotEqual
#Ilike = ILike


OP_MAPPING = {
    GreaterThan: ">", # "> {value}"
    GreaterEqual: ">=",
    LessThan: "<",
    LessEqual: "<=",
    Equal: "=",
    NotEqual: "!="
    #In_: "IN",
    #Like: "LIKE",
    #ILike: "ILIKE"
}