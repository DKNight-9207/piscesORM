from __future__ import annotations
from typing import Union, TYPE_CHECKING
import logging
from .. import errors
from ..base import TABLE_REGISTRY
from ..operator.basic import *
from .column import Column

if TYPE_CHECKING:
    from ..table import Table
    

logger = logger = logging.getLogger("piscesORM")

class Relationship:
    """
    Represents a one-to-one relationship between tables.

    Parameters:
    - table (Table class or str): The related table class. If the class is not yet defined,
        you can pass the table name as a string, and it will be resolved later.
    
    - *filters: Optional filter expressions to define the relationship condition. 
        All filters will be combined using logical 'AND'. This is the recommended way to define conditions.

    Examples:
    ```
    # These three are equivalent:
    Relationship(User, User.age > 18, User.money >= 100000)
    Relationship(User, (User.age > 18) & (User.money >= 100000))
    Relationship("User", (ColumnRef("age") > 18) & (ColumnRef("money") >= 100000))

    # These two are equivalent:
    Relationship(Author, Author.name == FieldRef("author_name"))
    Relationship("Author", ColumnRef("name") == FieldRef("author_name"))
    ```
    """
    def __init__(self, table:Union[type["Table"], str], *filters):
        self.table = table
        self.obj = None
        self.plural_data = False

        self.filters = filters
        # self.conditions = conditions

    def get_table(self):
        """
        Resolve and return the actual table class if `self.table` was passed as a string.
        Raises:
            TableNotFound: If the table name cannot be found in the registry.
        """
        if isinstance(self.table, str):
            t = TABLE_REGISTRY.get(self.table, None)
            if not t:
                raise errors.TableNotFound(self.table)
            return t
        return self.table
    
    def fix_filters(self):
        """
        Combine all filters using AND logic and resolve any ColumnRef to actual columns.
        
        Returns:
            The combined and resolved filter expression.
        """
        combined_filter = None
        if self.filters:
            for f in self.filters:
                if combined_filter is None:
                    combined_filter = f
                else:
                    combined_filter &= f
        if combined_filter:
            combined_filter = self.fix_column(combined_filter)
                        
        return combined_filter
    
    def fix_column(self, op:Operator):
        """
        Recursively resolves all `ColumnRef` instances in the operator tree to actual Column objects.

        Parameters:
            op (Operator): The filter expression tree.

        Returns:
            Operator: A new operator with all ColumnRefs replaced by actual Columns.

        Raises:
            NoSuchColumn: If a referenced column does not exist in the table.
        """
        fix_part = []
        table = self.get_table()
        for p in op.parts:
            if isinstance(p, Operator):
                fix_part.append(self.fix_column(p))
            elif isinstance(p, ColumnRef):
                column = getattr(table, p.name, None)
                if column is None:
                    raise errors.NoSuchColumn(p.name)
                fix_part.append(column)
            else:
                fix_part.append(p)

        return type(op)(*fix_part)
    
class PluralRelationship(Relationship):
    """
    Represents a many-to-one relationship between tables.

    Parameters:
    - table (Table class or str): The related table class. If the class is not yet defined,
        you can pass the table name as a string, and it will be resolved later.
    
    - *filters: Optional filter expressions to define the relationship condition. 
        All filters will be combined using logical 'AND'. This is the recommended way to define conditions.

    Examples:
    ```
    # These three are equivalent:
    Relationship(User, User.age > 18, User.money >= 100000)
    Relationship(User, (User.age > 18) & (User.money >= 100000))
    Relationship("User", (ColumnRef("age") > 18) & (ColumnRef("money") >= 100000))
    ```
    """
    def __init__(self, table, *filters):
        super().__init__(table, *filters)
        self.plural_data = True

class ManyToMany:
    """
    Represents a many-to-many relationship between two tables.
    This type of relationship requires an intermediate connection table.
    Unlike `Relationship`, this will automatically manage the creation of the join table.
    """
    def __init__(self, connect_name:str):
        self.connect_name = connect_name
        self.pks:set = None


class FieldRef:
    """
    Represents a deferred reference to a field on the current table instance.

    Used in filter conditions to indicate that the value should come from the current record,
    and will be resolved at query time.

    Attributes:
        name (str): The name of the column to reference.

    Example:
    ```
    class Author(Table):
        id: int = Integer(primary_key=True)
        name: str = Text()

    class Book(Table):
        id: int = Integer(primary_key=True)
        name: str = Text()
        author_name: str = Text()

        author: Author = Relationship(
            Author, 
            Author.name == FieldRef("author_name")
        )
        # This means: find the Author where Author.name matches this record's author_name
    ```
    """
    def __init__(self, name:str):
        self.name = name

class ColumnRef(Column): # inheritance for Column's magic function.
    """
    Represents a column reference for deferred resolution.

    Used to avoid type-checking issues when referencing a table that is not yet defined.
    It will be resolved to an actual Column instance during query construction.

    Example:
    ```
    class Book(Table):
        id: int = Integer(primary_key=True)
        name: str = Text()
        author_name: str = Text()

        author: Author = Relationship(
            "Author", 
            ColumnRef("name") == FieldRef("author_name")
        )
        # Since Author is not yet defined at this point,
        # we use a string for the table and a ColumnRef to reference the column.

    class Author(Table):
        id: int = Integer(primary_key=True)
        name: str = Text()
    ```
    """
    def __init__(self, name:str):
        self.name = name