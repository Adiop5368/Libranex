
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date, timedelta

from database import initialize_database, connect_db


BORROWING_PERIOD_DAYS = 14


class IssueBookManager:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX - Issue Books")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        initialize_database()

        self.all_students = []
        self.all_books = []
        self.student_options = {}
        self.book_options = {}

        self.student_var = tk.StringVar()
        self.book_var = tk.StringVar()

        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        ttk.Label(
            self.root,
            text="LIBRANEX - Issue Books",
            font=("Arial", 22, "bold")
        ).pack(pady=15)

        ttk.Label(
            self.root,
            text="Search and issue books to registered students",
            font=("Arial", 11)
        ).pack(pady=(0, 10))

        form = ttk.LabelFrame(
            self.root,
            text="Issue a Book",
            padding=18
        )
        form.pack(fill="x", padx=20, pady=10)
        form.columnconfigure(1, weight=1)

        # Student search
        ttk.Label(form, text="Search Student:").grid(
            row=0, column=0, padx=8, pady=10, sticky="w"
        )

        self.student_combo = ttk.Combobox(
            form,
            textvariable=self.student_var,
            state="normal"
        )
        self.student_combo.grid(
            row=0, column=1, padx=8, pady=10, sticky="ew"
        )

        self.student_combo.bind(
            "<KeyRelease>", self.filter_students
        )
        self.student_combo.bind(
            "<<ComboboxSelected>>", self.select_student
        )
        self.student_combo.bind(
            "<Return>", self.select_first_student_match
        )

        # Book search
        ttk.Label(form, text="Search Available Book:").grid(
            row=1, column=0, padx=8, pady=10, sticky="w"
        )

        self.book_combo = ttk.Combobox(
            form,
            textvariable=self.book_var,
            state="normal"
        )
        self.book_combo.grid(
            row=1, column=1, padx=8, pady=10, sticky="ew"
        )

        self.book_combo.bind(
            "<KeyRelease>", self.filter_books
        )
        self.book_combo.bind(
            "<<ComboboxSelected>>", self.select_book
        )
        self.book_combo.bind(
            "<Return>", self.select_first_book_match
        )

        self.issue_date_label = ttk.Label(form)
        self.issue_date_label.grid(
            row=2, column=0, columnspan=2,
            padx=8, pady=5, sticky="w"
        )

        self.due_date_label = ttk.Label(form)
        self.due_date_label.grid(
            row=3, column=0, columnspan=2,
            padx=8, pady=5, sticky="w"
        )

        buttons = ttk.Frame(form)
        buttons.grid(
            row=4, column=0, columnspan=2, pady=12
        )

        ttk.Button(
            buttons,
            text="Issue Book",
            command=self.issue_book
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Refresh Data",
            command=self.refresh_data
        ).pack(side="left", padx=5)

        # Active loans
        ttk.Label(
            self.root,
            text="Current Active Loans",
            font=("Arial", 15, "bold")
        ).pack(anchor="w", padx=22, pady=(15, 5))

        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both", expand=True, padx=20, pady=(5, 20)
        )

        self.columns = (
            "loan_id",
            "admission_no",
            "student_name",
            "accession_no",
            "book_title",
            "issue_date",
            "due_date",
            "status"
        )

        headings = (
            "Loan ID",
            "Admission No.",
            "Student",
            "Accession No.",
            "Book Title",
            "Issue Date",
            "Due Date",
            "Status"
        )

        widths = (65, 110, 155, 110, 200, 100, 100, 100)

        self.tree = ttk.Treeview(
            table_frame,
            columns=self.columns,
            show="headings",
            selectmode="browse"
        )

        for column, heading, width in zip(
            self.columns, headings, widths
        ):
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, minwidth=60)

        scrollbar_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        scrollbar_x = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("overdue", foreground="red")

    # ---------------- SEARCH ----------------

    def filter_students(self, event=None):
        if event and event.keysym in (
            "Up", "Down", "Left", "Right",
            "Return", "Escape", "Tab"
        ):
            return

        typed = self.student_var.get().strip().lower()

        matches = [
            label for label in self.all_students
            if typed in label.lower()
        ]

        # Update matches without opening the dropdown.
        self.student_combo["values"] = matches

    def filter_books(self, event=None):
        if event and event.keysym in (
            "Up", "Down", "Left", "Right",
            "Return", "Escape", "Tab"
        ):
            return

        typed = self.book_var.get().strip().lower()

        matches = [
            label for label in self.all_books
            if typed in label.lower()
        ]

        # Update matches without opening the dropdown.
        self.book_combo["values"] = matches

    def select_student(self, event=None):
        selected = self.student_var.get()

        if selected not in self.student_options:
            self.student_var.set("")

    def select_book(self, event=None):
        selected = self.book_var.get()

        if selected not in self.book_options:
            self.book_var.set("")

    def select_first_student_match(self, event=None):
        typed = self.student_var.get().strip().lower()

        matches = [
            label for label in self.all_students
            if typed and typed in label.lower()
        ]

        if len(matches) == 1:
            self.student_var.set(matches[0])
        elif typed in self.student_options:
            self.student_var.set(typed)

        return "break"

    def select_first_book_match(self, event=None):
        typed = self.book_var.get().strip().lower()

        matches = [
            label for label in self.all_books
            if typed and typed in label.lower()
        ]

        if len(matches) == 1:
            self.book_var.set(matches[0])

        return "break"

    # ---------------- DATES ----------------

    def update_date_labels(self):
        today = date.today()
        due = today + timedelta(days=BORROWING_PERIOD_DAYS)

        self.issue_date_label.config(
            text=f"Issue Date: {today.isoformat()}"
        )
        self.due_date_label.config(
            text=(
                f"Due Date: {due.isoformat()} "
                f"({BORROWING_PERIOD_DAYS}-day borrowing period)"
            )
        )

    # ---------------- LOAD DATA ----------------

    def refresh_data(self):
        self.load_students()
        self.load_available_books()
        self.load_active_loans()
        self.update_date_labels()

    def load_students(self):
        try:
            with connect_db() as db:
                rows = db.execute(
                    """
                    SELECT student_id, admission_no, name, class_name
                    FROM students
                    ORDER BY name COLLATE NOCASE
                    """
                ).fetchall()

            self.student_options.clear()
            self.all_students = []

            for student_id, admission_no, name, class_name in rows:
                label = (
                    f"{admission_no} - {name} ({class_name})"
                )
                self.student_options[label] = student_id
                self.all_students.append(label)

            self.student_combo["values"] = self.all_students

            if self.student_var.get() not in self.student_options:
                self.student_var.set("")

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load students:\n{error}"
            )

    def load_available_books(self):
        try:
            with connect_db() as db:
                rows = db.execute(
                    """
                    SELECT b.book_id, b.accession_no, b.title, b.author
                    FROM books AS b
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM loans AS l
                        WHERE l.book_id = b.book_id
                          AND l.return_date IS NULL
                    )
                    ORDER BY b.title COLLATE NOCASE
                    """
                ).fetchall()

            self.book_options.clear()
            self.all_books = []

            for book_id, accession_no, title, author in rows:
                label = (
                    f"{accession_no} - {title} by {author}"
                )
                self.book_options[label] = book_id
                self.all_books.append(label)

            self.book_combo["values"] = self.all_books

            if self.book_var.get() not in self.book_options:
                self.book_var.set("")

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load available books:\n{error}"
            )

    # ---------------- ISSUE BOOK ----------------

    def issue_book(self):
        student_label = self.student_var.get()
        book_label = self.book_var.get()

        if student_label not in self.student_options:
            messagebox.showwarning(
                "Select Student",
                "Select a student from the dropdown results."
            )
            return

        if book_label not in self.book_options:
            messagebox.showwarning(
                "Select Book",
                "Select an available book from the dropdown results."
            )
            return

        student_id = self.student_options[student_label]
        book_id = self.book_options[book_label]

        today = date.today()
        due = today + timedelta(days=BORROWING_PERIOD_DAYS)

        issue_text = today.isoformat()
        due_text = due.isoformat()

        confirm = messagebox.askyesno(
            "Confirm Book Issue",
            f"Student: {student_label}\n\n"
            f"Book: {book_label}\n\n"
            f"Issue Date: {issue_text}\n"
            f"Due Date: {due_text}\n\n"
            "Proceed with issuing this book?"
        )

        if not confirm:
            return

        try:
            with connect_db() as db:
                active_loan = db.execute(
                    """
                    SELECT 1 FROM loans
                    WHERE book_id = ?
                      AND return_date IS NULL
                    LIMIT 1
                    """,
                    (book_id,)
                ).fetchone()

                if active_loan:
                    messagebox.showwarning(
                        "Book Unavailable",
                        "This book has already been issued. "
                        "Refresh and select another book."
                    )
                    self.refresh_data()
                    return

                student_exists = db.execute(
                    """
                    SELECT 1 FROM students
                    WHERE student_id = ?
                    """,
                    (student_id,)
                ).fetchone()

                if not student_exists:
                    messagebox.showerror(
                        "Student Not Found",
                        "This student no longer exists."
                    )
                    self.refresh_data()
                    return

                db.execute(
                    """
                    INSERT INTO loans
                    (student_id, book_id, issue_date, due_date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (student_id, book_id, issue_text, due_text)
                )

            messagebox.showinfo(
                "Success",
                f"Book issued successfully!\n\n"
                f"Student: {student_label}\n"
                f"Book: {book_label}\n"
                f"Due Date: {due_text}"
            )

            self.student_var.set("")
            self.book_var.set("")
            self.refresh_data()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Issue Not Completed",
                "The database rejected this issue. "
                "The book may already be on loan, or a related "
                "record may no longer exist."
            )
            self.refresh_data()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not issue the book:\n{error}"
            )

    # ---------------- ACTIVE LOANS ----------------

    def load_active_loans(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        today = date.today().isoformat()

        try:
            with connect_db() as db:
                rows = db.execute(
                    """
                    SELECT
                        l.loan_id,
                        s.admission_no,
                        s.name,
                        b.accession_no,
                        b.title,
                        l.issue_date,
                        l.due_date
                    FROM loans AS l
                    JOIN students AS s
                        ON s.student_id = l.student_id
                    JOIN books AS b
                        ON b.book_id = l.book_id
                    WHERE l.return_date IS NULL
                    ORDER BY l.due_date, s.name
                    """
                ).fetchall()

            for row in rows:
                (
                    loan_id,
                    admission_no,
                    student_name,
                    accession_no,
                    book_title,
                    issue_date,
                    due_date
                ) = row

                status = "Overdue" if due_date < today else "On Loan"

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        loan_id,
                        admission_no,
                        student_name,
                        accession_no,
                        book_title,
                        issue_date,
                        due_date,
                        status
                    ),
                    tags=("overdue",) if status == "Overdue" else ()
                )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load active loans:\n{error}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = IssueBookManager(root)
    root.mainloop()
