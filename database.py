"""
Database module for Library Management System
Handles all database operations and connections
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Database configuration
DATABASE = "library.db"

# 只初始化一次，避免在 pytest / CI 中重复建表与重复灌数据
_DB_BOOTSTRAPPED = False


def _connect_raw() -> sqlite3.Connection:
    """
    打开一个裸连接（不依赖 get_db_connection），用于引导初始化，避免递归调用。
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    """
    确保数据库表存在（幂等）。
    books 表字段保持与库层调用一致：total_copies / available_copies。
    borrow_records 表用于借阅记录，return_date 可为空。
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            total_copies INTEGER NOT NULL,
            available_copies INTEGER NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS borrow_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patron_id TEXT NOT NULL,
            book_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
        """
    )

    conn.commit()


def init_database() -> None:
    """
    显式初始化数据库表（保留原接口）。
    该函数内部自己创建与关闭连接，便于在 CI 或脚本里单独调用。
    """
    conn = _connect_raw()
    try:
        ensure_schema(conn)
    finally:
        conn.close()


def add_sample_data() -> None:
    """
    若库为空则灌入样例数据（幂等）。
    注意：仅在 books 为空时插入，避免多次运行造成重复数据。
    """
    conn = _connect_raw()
    try:
        count_row = conn.execute("SELECT COUNT(*) AS count FROM books").fetchone()
        book_count = count_row["count"] if count_row else 0

        if book_count == 0:
            sample_books = [
                ("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 3),
                ("To Kill a Mockingbird", "Harper Lee", "9780061120084", 2),
                ("1984", "George Orwell", "9780451524935", 1),
            ]

            for title, author, isbn, copies in sample_books:
                conn.execute(
                    """
                    INSERT INTO books (title, author, isbn, total_copies, available_copies)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (title, author, isbn, copies, copies),
                )

            # 让《1984》变为不可借：插入一条借阅记录并把可借数改为 0
            conn.execute(
                """
                INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "123456",
                    3,  # 假设第三本书自增 id = 3（在空库插入三本时成立）
                    (datetime.now() - timedelta(days=5)).isoformat(),
                    (datetime.now() + timedelta(days=9)).isoformat(),
                ),
            )
            conn.execute("UPDATE books SET available_copies = 0 WHERE id = 3")

            conn.commit()
    finally:
        conn.close()


def _bootstrap_db_once() -> None:
    """
    首次调用时：建表 + 灌样例数据（幂等）。
    """
    global _DB_BOOTSTRAPPED
    if _DB_BOOTSTRAPPED:
        return

    # 使用裸连接避免递归
    conn = _connect_raw()
    try:
        ensure_schema(conn)
    finally:
        conn.close()

    add_sample_data()
    _DB_BOOTSTRAPPED = True


def get_db_connection() -> sqlite3.Connection:
    """
    获取数据库连接；首次调用自动完成引导（建表与必要的样例数据），
    之后只返回普通连接。调用方负责在使用完毕后关闭连接。
    """
    _bootstrap_db_once()
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# --------------------------
# Helper Functions for Database Operations
# --------------------------

def get_all_books() -> List[Dict]:
    """Get all books from the database."""
    conn = get_db_connection()
    try:
        books = conn.execute("SELECT * FROM books ORDER BY title").fetchall()
        return [dict(book) for book in books]
    finally:
        conn.close()


def get_book_by_id(book_id: int) -> Optional[Dict]:
    """Get a specific book by ID."""
    conn = get_db_connection()
    try:
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return dict(book) if book else None
    finally:
        conn.close()


def get_book_by_isbn(isbn: str) -> Optional[Dict]:
    """Get a specific book by ISBN."""
    conn = get_db_connection()
    try:
        book = conn.execute("SELECT * FROM books WHERE isbn = ?", (isbn,)).fetchone()
        return dict(book) if book else None
    finally:
        conn.close()


def get_patron_borrowed_books(patron_id: str) -> List[Dict]:
    """Get currently borrowed books for a patron."""
    conn = get_db_connection()
    try:
        records = conn.execute(
            """
            SELECT br.*, b.title, b.author
            FROM borrow_records br
            JOIN books b ON br.book_id = b.id
            WHERE br.patron_id = ? AND br.return_date IS NULL
            ORDER BY br.borrow_date
            """,
            (patron_id,),
        ).fetchall()

        borrowed_books: List[Dict] = []
        for r in records:
            borrowed_books.append(
                {
                    "book_id": r["book_id"],
                    "title": r["title"],
                    "author": r["author"],
                    "borrow_date": datetime.fromisoformat(r["borrow_date"]),
                    "due_date": datetime.fromisoformat(r["due_date"]),
                    "is_overdue": datetime.now() > datetime.fromisoformat(r["due_date"]),
                }
            )
        return borrowed_books
    finally:
        conn.close()


def get_patron_borrow_count(patron_id: str) -> int:
    """Get the number of books currently borrowed by a patron."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM borrow_records
            WHERE patron_id = ? AND return_date IS NULL
            """,
            (patron_id,),
        ).fetchone()
        return int(row["count"]) if row else 0
    finally:
        conn.close()


def insert_book(
    title: str, author: str, isbn: str, total_copies: int, available_copies: int
) -> bool:
    """Insert a new book into the database."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO books (title, author, isbn, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, author, isbn, total_copies, available_copies),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def insert_borrow_record(
    patron_id: str, book_id: int, borrow_date: datetime, due_date: datetime
) -> bool:
    """Insert a new borrow record into the database."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date)
            VALUES (?, ?, ?, ?)
            """,
            (patron_id, book_id, borrow_date.isoformat(), due_date.isoformat()),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def update_book_availability(book_id: int, change: int) -> bool:
    """
    Update the available copies of a book by a given amount
    (+1 for return, -1 for borrow).
    """
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE books SET available_copies = available_copies + ? WHERE id = ?",
            (change, book_id),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def update_borrow_record_return_date(
    patron_id: str, book_id: int, return_date: datetime
) -> bool:
    """Update the return date for a borrow record."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE borrow_records
            SET return_date = ?
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
            """,
            (return_date.isoformat(), patron_id, book_id),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()
