from typing import Type
from .._setting import setting
from . import _T

def _get_autounlock_time(timeout:float):
    return timeout if timeout is not None else setting.lock_auto_release_time


# 產生鎖 key 的函數
def generateLockKey(model: Type[_T], **filters) -> str:
    # 依據 model 與 filters 產生唯一 key
    key = f"{model.__name__}:" + ",".join(f"{k}={v}" for k, v in sorted(filters.items()))
    return key