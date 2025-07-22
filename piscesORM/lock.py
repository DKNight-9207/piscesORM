import threading
import time
import logging
from asyncio import Lock
from contextlib import asynccontextmanager, AsyncExitStack
from typing import TypeVar, overload, Type, List

logger = logging.getLogger("piscesORM")

MAX_LOCK_TIME = 5
GARBAGE_CLEAN_CYCLE = 5
_T = TypeVar("_T")

class RowLock:
    def __init__(self):
        self.lock_owner: str = None
        self.autounlock_time: float = 0
        self.lock: Lock = Lock()
        self._garbageMark: bool = False

    async def acquire(self, owner: str, timeout: float = MAX_LOCK_TIME):
        if time.time() > self.autounlock_time and self.lock.locked():
            logger.warning(
                f"RowLock held by {self.lock_owner} expired for {time.time() - self.autounlock_time:.2f}s"
            )
            self._forceRelease()
        await self.lock.acquire()
        self._garbageMark = False
        self.lock_owner = owner
        self.autounlock_time = time.time() + timeout

    def release(self, owner: str):
        if self.lock_owner != owner:
            logger.warning(f"RowLock owned by {self.lock_owner} tried to be released by {owner}")
            return
        if not self.lock.locked():
            logger.warning(f"RowLock not locked but release attempted by {owner}")
            return
        self.lock_owner = None
        self.autounlock_time = 0
        self.lock.release()

    def _forceRelease(self):
        if self.lock.locked():
            self.lock.release()
        self.lock_owner = None
        self.autounlock_time = 0

    @asynccontextmanager
    async def context(self, owner: str):
        await self.acquire(owner)
        try:
            yield
        finally:
            self.release(owner)

    @asynccontextmanager
    async def acquire_locks(keys: List[str], owner: str):
        # 鎖順序排序避免死鎖
        sorted_keys = sorted(keys)

        async with AsyncExitStack() as stack:
            for key in sorted_keys:
                lock = lockManager.getLock(key)
                await stack.enter_async_context(lock.context(owner))
            yield

class LockGroup:
    def __init__(self, owner: str):
        self.owner = owner
        self.stack = AsyncExitStack()
        self.lock_keys = set()

    async def add(self, key: str):
        if key in self.lock_keys:
            return  # 避免重複加鎖
        lock = lockManager.getLock(key)
        await self.stack.enter_async_context(lock.context(self.owner))
        self.lock_keys.add(key)

    async def __aenter__(self):
        await self.stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stack.__aexit__(exc_type, exc, tb)

class LockManager:
    def __init__(self):
        self.locks: dict[str, RowLock] = {}
        self._lock = threading.Lock()
        self._stop = False
        self._cleaner = threading.Thread(name="LockManagerGarbageCleaner", target=self._garbageCleaner, daemon=True)
        self._cleaner.start()

    def getLock(self, key: str) -> RowLock:
        with self._lock:
            if key not in self.locks:
                self.locks[key] = RowLock()
            return self.locks[key]

    def _garbageCleaner(self):
        while not self._stop:
            time.sleep(GARBAGE_CLEAN_CYCLE)
            now = time.time()
            to_delete = []

            with self._lock:
                for key, lock in self.locks.items():
                    if now > lock.autounlock_time and lock.lock.locked():
                        logger.warning(f"Forcing release of expired RowLock for key: {key}")
                        lock._forceRelease()

                    if lock._garbageMark:
                        to_delete.append(key)
                    else:
                        lock._garbageMark = True

                for key in to_delete:
                    logger.debug(f"Cleaning up unused RowLock for key: {key}")
                    del self.locks[key]

    def stop(self):
        self._stop = True
        self._cleaner.join()




def generateLockKey(model: Type[_T], **filters) -> str:
    pass


lockManager = LockManager()