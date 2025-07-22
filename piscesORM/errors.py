



class PiscesError(Exception):
    pass

class PiscesWarning(Warning):
    pass

class NoPrimaryKeyWarning(PiscesWarning):
    def __init__(self):
        message = "This table has no primary key, which means you can't use ORM edit or delete operations. If you don't want to see this warning, set '__no_primary_key__ = True'."
        super().__init__(message)

class NoPrimaryKeyError(PiscesError):
    def __init__(self):
        message = "You are trying to update or delete data without a primary key, so the ORM can't perform the operation automatically."
        super().__init__(message)

class InsertPrimaryKeyColumn(PiscesError):
    def __init__(self):
        message = (
            "You are trying to add a primary key column to an existing table, which may affect indexing and is not supported in-place. "
            "To apply this change, enable 'rebuild' mode to recreate the table and migrate the data."
        )
        super().__init__(message)
        
PROTECT_NAME = set([
    # table protected val
    "_registry", "__abstract__", "__table_name__", "__no_primary_key__", "_columns", "_relantionship", "_indexes", "_edited", "_initialized", 
    # column protected val
    "plurl_data",
    # session protected val
    "read_only", "load_relationships" 
    ])
class ProtectedColumnName(PiscesError):
    def __init__(self, column_name: str):
        message = f"The column name '{column_name}' is reserved or protected and cannot be used as a column name."
        super().__init__(message)

class IllegalDefaultValue(PiscesError):
    def __init__(self, message):
        super().__init__(message)

class PrimaryKeyConflict(PiscesError):
    def __init__(self):
        message = "Primary key conflict occurred."
        super().__init__(message)

class NoSuchColumn(PiscesError):
    def __init__(self, column_name: str):
        message = f"No such column: '{column_name}'"
        super().__init__(message)