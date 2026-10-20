
import sqlite3

DATABASE_NAME = "libranex.db"


def connect_db():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with connect_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                admission_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                accession_no TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                subject TEXT
            );

            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT DEFAULT NULL,

                FOREIGN KEY (student_id)
                    REFERENCES students(student_id),

                FOREIGN KEY (book_id)
                    REFERENCES books(book_id)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS
                one_active_loan_per_book
            ON loans(book_id)
            WHERE return_date IS NULL;
        """)


if __name__ == "__main__":
    initialize_database()
    print("LIBRANEX database initialized successfully!")
