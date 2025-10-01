# 基本操作
piscesORM 研究多個資料庫ORM系統，最終採用類似 piccolo 的資料表宣告方式，我認為這是多個資料庫中宣告起來最簡單、易懂的
因此要宣告一個資料表，需要這樣做
```py
from piscesORM.table import Table # 創建表要繼承這個
from piscesORM.column import Integer, Text # 宣告欄位時，要賦值為這個

class Book(Table):
    isbn = Integer(primary_key=True)
    title = Text()
    author_name = Text()
    price = Integer(default=100)

```
其餘支援的欄位，請參閱 column 篇。

當表宣告完後，我們就可以創建了，不過在這之前，我們要告訴 piscesORM 想要的資料庫種類。
目前 ORM 只支援 sqlite ，不過還有分同步與異步，這部分是通過創建一個 engine 來決定的，創建好了之後，就能呼叫 engine 來進行初始化
```py
from piscesORM.engine import SyncSQLiteEngine
engine = SyncSQLiteEngine() # 在這裡，我用基本的同步SQLite作為範例
                            # 預設下，是 memory 模式，memory模式的資料庫生命週期和程式生命週期一致
                            # 如果要把檔案存在硬碟，只需在這邊指定路徑即可。但目前不支援遠端硬碟位置

engine.initialize() # 使用這個函式後，它就會自動創建前面宣告的表。
                    # 其餘可選參數，詳閱 engine 篇
```

創建完 engine 後，我們就能建立連線了。要建立一個連線，我們需要使用上下文管理器`with ... as ...`，這樣 ORM 就能夠自動處理連線的前置與善後工作。這裡我示範資料的基本插入、搜尋與刪除

```py
with engine.session() as session:
    books = [
        Book(isbn=9781408855652, title="Harry Potter and the Philosopher's Stone", author_name="J. K. Rowling"),
        Book(isbn=9780439064873, title="Harry Potter and the Chamber of Secrets", author_name="J. K. Rowling"),
        Book(isbn=9780593198025, title="Little Women", author_name="Louisa May Alcott")
    ]
    book_2 = Book(isbn=9781408855676, title="Harry Potter and the Prisoner of Azkaban", author_name="J. K. Rowling")
    
    session.insert_many(books) # 插入多筆資料
    session.insert(book_2) # 插入單筆資料
    
    # 這裡的邏輯是：搜尋 Book 表中，所有過濾書名以 `Harry` 開頭的，並且根據isbn反向排序
    books = session.get_all(Book, Book.title.like('Harry%'), sort_by=-Book.isbn)
    print('\n'.join([b.title for b in books]))
    print("---------------------------")

    session.delete_object(books[1]) # 根據物件刪除
    session.delete(Book, Book.author_name != "J. K. Rowling") # 根據條件刪除
    books = session.get_all(Book, sort_by=Book.title) # 確認是否刪除
    print('\n'.join([b.title for b in books]))
    print("---------------------------")
    # 到這裡應該少兩本書
    # 少 Little Women 和 Harry Potter and the Philosopher's Stone

    book:Book = session.get_first(Book, Book.title == "Harry Potter and the Chamber of Secrets")
    book.price *= 0.8 # 假設打8折
    session.merge(book) # 把本地修改推送到資料庫
    # 在資料庫端，JK羅琳的書打8折
    session.update(Book, Book.author_name=="J. K. Rowling", price=operator.Multiply(0.8)) 

    book_1 = session.get_first(Book, Book.title == "Harry Potter and the Chamber of Secrets")
    book_2 = session.get_first(Book, Book.title == "Harry Potter and the Prisoner of Azkaban")
    print(f"the price is {book_1.price}") # 應該會顯示 64 元
    print(f"the price is {book_2.price}") # 應該會顯示 80 元
```