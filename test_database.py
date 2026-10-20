
import sqlite3
import tempfile
import unittest
from pathlib import Path


class LibranexDatabaseTests(unittest.TestCase):

    def setUp(self):
        # Create an isolated temporary database for each test.
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".db",
            delete=False
        )
        self.db_path = Path(temp_file.name)
        temp_file.close()

        self.db = sqlite3.connect(self.db_path)
        self.db.execute("PRAGMA foreign_keys = ON")

        self.db.executescript("""
            CREATE TABLE students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                admission_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL
            );

            CREATE TABLE books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                accession_no TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                subject TEXT
            );

            CREATE TABLE loans (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL
                    REFERENCES students(student_id),
                book_id INTEGER NOT NULL
                    REFERENCES books(book_id),
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT DEFAULT NULL
            );

            CREATE UNIQUE INDEX one_active_loan_per_book
            ON loans(book_id)
            WHERE return_date IS NULL;
        """)

        self.db.execute("""
            INSERT INTO students
                (admission_no, name, class_name)
            VALUES ('TEST001', 'Test Student', '11A')
        """)

        self.student_id = self.db.execute(
            "SELECT student_id FROM students"
        ).fetchone()[0]

        self.db.execute("""
            INSERT INTO books
                (accession_no, title, author, subject)
            VALUES ('BOOK001', 'Test Book', 'Test Author', 'Science')
        """)

        self.book_id = self.db.execute(
            "SELECT book_id FROM books"
        ).fetchone()[0]

        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.db_path.unlink(missing_ok=True)

    def add_loan(self, student_id=None, book_id=None):
        self.db.execute("""
            INSERT INTO loans
                (student_id, book_id, issue_date, due_date)
            VALUES (?, ?, '2026-10-01', '2026-10-15')
        """, (
            self.student_id if student_id is None else student_id,
            self.book_id if book_id is None else book_id
        ))
        self.db.commit()

    def test_duplicate_admission_number_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("""
                INSERT INTO students
                    (admission_no, name, class_name)
                VALUES ('TEST001', 'Another Student', '11B')
            """)

    def test_duplicate_accession_number_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("""
                INSERT INTO books
                    (accession_no, title, author)
                VALUES ('BOOK001', 'Another Book', 'Another Author')
            """)

    def test_book_cannot_have_two_active_loans(self):
        self.add_loan()

        with self.assertRaises(sqlite3.IntegrityError):
            self.add_loan()

    def test_returned_book_can_be_issued_again(self):
        self.add_loan()

        self.db.execute("""
            UPDATE loans
            SET return_date = '2026-10-10'
            WHERE book_id = ?
              AND return_date IS NULL
        """, (self.book_id,))
        self.db.commit()

        # A new active loan should now be allowed.
        self.add_loan()

        active_count = self.db.execute("""
            SELECT COUNT(*)
            FROM loans
            WHERE book_id = ?
              AND return_date IS NULL
        """, (self.book_id,)).fetchone()[0]

        self.assertEqual(active_count, 1)

    def test_loan_history_is_preserved_after_return(self):
        self.add_loan()

        self.db.execute("""
            UPDATE loans
            SET return_date = '2026-10-10'
            WHERE book_id = ?
        """, (self.book_id,))
        self.db.commit()

        record = self.db.execute("""
            SELECT issue_date, due_date, return_date
            FROM loans
            WHERE book_id = ?
        """, (self.book_id,)).fetchone()

        self.assertEqual(
            record,
            ('2026-10-01', '2026-10-15', '2026-10-10')
        )

    def test_invalid_student_reference_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_loan(student_id=999999)

    def test_invalid_book_reference_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_loan(book_id=999999)


if __name__ == "__main__":
    unittest.main(verbosity=2)
