from __future__ import annotations
from piscesORM.table import Table
from piscesORM.column import Text, Integer, Relationship

class Author(Table):
    name = Text()
    age = Integer()

class Book(Table):
    __table_name__ = "books"
    id = Integer(primary_key=True, auto_increment=True)
    title = Text()
    author_name = Text()
    author = Relationship(Author, name="author_name")
    
