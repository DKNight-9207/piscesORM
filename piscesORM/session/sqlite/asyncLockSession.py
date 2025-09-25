from .asyncSession import AsyncSQLiteSession

class AsyncSQLiteLockSession(AsyncSQLiteSession):
    def __init__(self, connection, mode="r", auto_commit = True):
        raise RuntimeError("this session not ready yet.")
        super().__init__(connection, mode, auto_commit)
        self.mode = mode