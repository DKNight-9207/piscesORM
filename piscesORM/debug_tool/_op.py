from ..operator import Operator

def print_op(op:object)->str:
    if isinstance(op, Operator):
        return f"{op.__class__}({','.join([print_op(p) for p in op.parts])})"
    elif isinstance(op, (int, float, str, list)):
        return f"<{op.__class__}: {op}>"
    return f"<{op.__class__} object>"