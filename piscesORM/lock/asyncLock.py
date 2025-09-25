from __future__ import annotations
import threading
import time
import logging
import asyncio
import random
from asyncio import Lock as AsyncLock
from threading import Lock as SyncLock
from contextlib import asynccontextmanager, AsyncExitStack, contextmanager, ExitStack
from typing import TypeVar, Type, List, Optional, Dict, Any, Union
from .._setting import setting
from .. import errors
from . import _T
from .toolbox import _get_autounlock_time


logger = logging.getLogger("piscesORM")

"""
note:
LockManager: Those classes which manage row locks.
LockClient: A class remembering the locks held by a user.
RowLock: A unit (row) of lock, which stores actually lock and extra information.
"""



# =========== Async Lock ===========
class AsyncLockManager:
    """ The real Lock manager who create, distribute, and collect locks"""
    def __init__(self):
        self._locks: Dict[str, AsyncRowLock] = {}
        self._manager_lock = AsyncLock() # protect self._locks
        self._login_users: Dict[str, AsyncLockClient] = {}

        self._gc_task: Optional[asyncio.Task] = None

    def start(self):
        """ Start GC task"""
        if self._gc_task is None:
            self._gc_task = asyncio.create_task(self._garbage_collector)
            logger.info("AsyncLockManager GC task started.")

    async def stop(self):
        """[async] Stop GC task"""
        if self._gc_task:
            self._gc_task.cancel()
            try:
                await self._gc_task
            except asyncio.CancelledError:
                pass
            self._gc_task = None
            logger.info("AsyncLockManager GC task stopped.")

        for user in list(self._login_users.keys()):
            await self.logout(user)

    async def _garbage_collector(self):
        while True:
            await asyncio.sleep(setting.garbage_clean_cycle)
            logger.debug("Running AsyncLockManager garbage collector...")
            
            expired_locks: List[AsyncRowLock] = []
            to_delete_locks: List[str] = []

            async with self._manager_lock:
                # level 1: mark and collect
                for key, lock in self._locks.items():
                    if lock.is_locked() and lock.is_expired():
                        expired_locks.append(lock)

                    if not lock.is_locked() and lock._garbageMark:
                        to_delete_locks.append(key)
                    else:
                        lock._garbageMark = True

            for lock in expired_locks:
                lock._forceRelease()

            if to_delete_locks:
                async with self._manager_lock:
                    for key in to_delete_locks:
                        if key in self._locks and self._locks[key]._garbageMark and not self._locks[key].is_locked():
                            del self._locks[key]
                            logger.debug(f"Cleaned up unused AsyncRowLock for key: {key}")

    async def getLock(self, key: str) -> AsyncRowLock:
        async with self._manager_lock:
            if key not in self._locks:
                self._locks[key] = AsyncRowLock()
            lock = self._locks[key]
            lock._garbageMark = False
            return lock
        
    async def login(self, user: Optional[str] = None, relogin = False) -> AsyncLockClient:
        async with self._manager_lock:
            user_list = self._login_users.keys()
            if not user:
                while True:
                    _user = f"user_{random.randint(10000, 99999)}"
                    if _user not in user_list:
                        break
            else:
                _user = user
            
            if user in user_list:
                if not relogin:
                    raise errors.UserAlreadyLogin(_user)
                client = self._login_users[_user]
                return client
            client = AsyncLockClient(self, _user)
            self._login_users[_user] = client
        return client
        
    async def logout(self, user: str):
        async with self._manager_lock:
            client = self._login_users.pop(user, None)
        
        if client:
            await client._cleanup()
            logger.info(f"AsyncLockClient for user {user} logged out successfully.")
        else:
            logger.warning(f"AsyncLockClient for user {user} not found during logout.")
            

class AsyncLockClient:
    """ A lock owner who remembers the locks it holds and suffers operation interface. """
    def __init__(self, manager: AsyncLockManager, user:str):
        self.manager = manager
        self.user = user
        self._own_locks: Dict[str, AsyncRowLock] = {}
        logger.debug(f"AsyncLockClient created for user: {self.user}")

    async def acquire(self, key: str, timeout: Optional[float] = None) -> AsyncRowLock:
        """ Accquire a lock by key. """
        if key in self._own_locks:
            lock = self._own_locks[key]
            with lock._meta_lock:
                if lock.lock_owner == self.user:
                    t = _get_autounlock_time(timeout)
                    new_time = time.time() + t if t > 0 else float('inf')
                    return lock
        else:
            lock = await self.manager.getLock(key)
        effective_timeout = _get_autounlock_time(timeout)
        await lock.acquire(self.user, effective_timeout)
        self._own_locks[key] = lock
        return lock
        
    def release(self, key:str):
        """ Release a lock by key """
        if key in self._own_locks:
            lock = self._own_locks.pop(key)
            if lock.get_owner() == self.user:
                lock.release(self.user)
        else:
            logger.warning(f"User {self.user} attempted to release a lock '{key}'")

    async def _cleanup(self):
        """ Clear all lock held by user. """
        logger.debug(f"Cleaning up all lock for user {self.user}...")
        for key, lock in list(self._own_locks.items()):
            if lock.get_owner() == self.user:
                lock.release(self.user)
        self._own_locks.clear()
        logger.debug(f"All locks for user {self.user} have been released.")

    async def check_lock(self, require_keys:list[str], raise_error=True) -> bool:
        req_set = set(require_keys)
        own_set = set(self._own_locks.keys)

        # lost key:
        lost_set = req_set - own_set
        if lost_set:
            if raise_error:
                raise errors.MissingLock(list(lost_set))
            return False

        # check own lock:
        missing_lock = []
        for key in req_set:
            lock = self._own_locks[key]
            if lock.get_owner() != self.user or lock.is_expired():
                missing_lock.append(key)

        if missing_lock:
            if raise_error:
                raise errors.MissingLock(missing_lock)
            return False
        return True
                
class AsyncRowLock:
    """ A Real Lock which have python lock and extra information."""
    def __init__(self):
        # lock
        self.lock: AsyncLock = AsyncLock()
        self._meta_lock = SyncLock() # make sure the thread-safe access to lock metadata

        # metadata
        self.lock_owner: Optional[str] = None
        self.autounlock_time: float = 0
        # -----------------------------
        self._garbageMark: bool = False

    def is_locked(self) -> bool:
        """ Check if the lock is currently held """
        return self.lock.locked()
    
    def get_owner(self) -> Optional[str]:
        """ Get the owner with thread-safe access """
        with self._meta_lock:
            return self.lock_owner

    async def acquire(self, owner: str, timeout: float):
        """ Acquire the lock until the lock is available """
        await self.lock.acquire() # timeout release job is managed by the manager

        with self._meta_lock:
            self._garbageMark = False
            self.lock_owner = owner
            self.autounlock_time = time.time() + timeout if timeout > 0 else float('inf')
            logger.debug(f"AsyncRowLock acquired by {owner}.")


    def release(self, owner: str):
        """ Release lock by owner"""
        with self._meta_lock:
            if self.lock_owner != owner:
                logger.warning(f"Attempt to release by non-owner. Owner: {self.lock_owner}, Attempted by: {owner}")
                return
        
            if not self.lock.locked():
                logger.warning(f"Attempt to release a non-locked lock by {owner}")
                self.lock_owner = None
                self.autounlock_time = 0
                return
            
            self.lock_owner = None
            self.autounlock_time = 0
        
        self.lock.release()
        logger.debug(f"AsyncRowLock released by {owner}.")

    def _forceRelease(self):
        """ Force release lock by LockManager. """
        with self._meta_lock:
            owner = self.lock_owner
            self.lock_owner = None
            self.autounlock_time = 0

        if self.lock.locked():
            self.lock.release()
            logger.warning(f"AsyncRowLock forcibly released from expired owner: {owner}.")

    def is_expired(self) -> bool:
        """ Check if the lock is expired """
        with self._meta_lock:
            if self.lock_owner is None:
                return False
            return time.time() > self.autounlock_time

# 實例化管理器
asyncLockManager = AsyncLockManager()