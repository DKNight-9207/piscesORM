from __future__ import annotations
from piscesORM.table import Table
from piscesORM.column import Text, Integer, Relationship, FieldRef, Real
from piscesORM.engine import SyncSQLiteEngine
from piscesORM.operator import Gte, Lte


class Books(Table):
    name:str = Text(primary_key=True)
    price:float = Real()

engine = SyncSQLiteEngine()
engine.initialize()

with engine.session() as session:
    books:list[Books] = [
        Books(name="Readyplayer one", price=9.97),
        Books(name="Pride and Prejudice", price=5.29),
        Books(name="The Lord of the Rings ", price=15.51),
        Books(name="Wonder", price=10.84)
    ]

    session.insert_many(books)
    session.commit()

with engine.session() as session:
    books_1:list[Books] = session.get_all(Books, price = Gte(10))
    print([b.name for b in books_1])