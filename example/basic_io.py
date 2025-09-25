from __future__ import annotations
from piscesORM.table import Table
from piscesORM.column import Text, Integer, Relationship, FieldRef
from piscesORM.engine import SyncSQLiteEngine
import os

class Author(Table):
    __table_name__ = "authors"
    id = Integer(primary_key=True, auto_increment=True)
    name = Text()
    age = Integer()
    books = Relationship('Book', plural_data=True, author_name=FieldRef('name'))

class Book(Table):
    __table_name__ = "books"
    id = Integer(primary_key=True, auto_increment=True)
    title = Text()
    author_name = Text()
    author = Relationship(Author, name=FieldRef("author_name"))

engine = SyncSQLiteEngine()
engine.initialize()

with engine.session() as session:
    authors:list[Author] = [
        Author(name="J.K. Rowling", age=57),
        Author(name="George R.R. Martin", age=75),
        Author(name="J.R.R. Tolkien", age=81),
        Author(name="Isaac Asimov", age=72),
        Author(name="Arthur C. Clarke", age=90),
    ]
    books:list[Book] = [
        Book(title="Harry Potter and the Philosopher's Stone", author_name="J.K. Rowling"),
        Book(title="Harry Potter and the Chamber of Secrets", author_name="J.K. Rowling"),
        Book(title="A Game of Thrones", author_name="George R.R. Martin"),
        Book(title="The Hobbit", author_name="J.R.R. Tolkien"),
        Book(title="Foundation", author_name="Isaac Asimov"),
        Book(title="2001: A Space Odyssey", author_name="Arthur C. Clarke"),
    ]
    session.insert_many(authors)
    session.insert_many(books)

    session.commit()

with engine.session() as session:
    test_book:Book = session.get_first(Book, Book.title=="Harry Potter and the Philosopher's Stone")
    print(test_book)
    test_author:Author = test_book.author
    print(test_author)
    author_books:list[Book] = test_author.books
    print([b.title for b in author_books])




