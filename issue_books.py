import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from database import initialize_database, connect_db


BORROWING_PERIOD_DAYS = 14

# LIBRANEX light-theme palette (consistent with the dashboard)
BG = "#F4F6F8"
PANEL = "#FFFFFF"
PANEL_LIGHT = "#F8FAFC"
ACCENT = "#4F6BED"
ACCENT_HOVER = "#4059D6"
TEXT = "#1E293B"
MUTED = "#64748B"
BORDER = "#E2E8F0"
GREEN = "#3F8A6B"
RED = "#C96A6A"
RED_LIGHT = "#FEF2F2"


class IssueBookManager:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX | Issue Books")
        self.root.geometry("1180x760")
        self.root.minsize(940, 640)
        self.root.configure(bg=BG)

        initialize_database()

        self.all_students = []
        self.all_books = []
        self.student_options = {}
        self.book_options = {}

        self.student_var = tk.StringVar()
        self.book_var = tk.StringVar()

        self._configure_styles()
        self.create_widgets()
        self.refresh_data()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT)
        style.configure(
            "Title.TLabel", background=BG, foreground=TEXT,
            font=("Segoe UI", 22, "bold")
        )
        style.configure(
            "Subtitle.TLabel", background=BG, foreground=MUTED,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Section.TLabel", background=PANEL, foreground=TEXT,
            font=("Segoe UI", 12, "bold")
        )
        style.configure(
            "Field.TLabel", background=PANEL, foreground=MUTED,
            font=("Segoe UI", 9, "bold")
        )
        style.configure(
            "TEntry", padding=(9, 7), fieldbackground="#FFFFFF",
            foreground=TEXT, bordercolor=BORDER, lightcolor=BORDER,
            darkcolor=BORDER
        )
        style.configure(
            "TCombobox", padding=(9, 7), fieldbackground="#FFFFFF",
            background="#FFFFFF", foreground=TEXT, arrowcolor=MUTED,
            bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#FFFFFF"), ("!disabled", "#FFFFFF")],
            foreground=[("disabled", MUTED)]
        )
        style.configure(
            "TButton", padding=(12, 8), background=PANEL_LIGHT,
            foreground=TEXT, bordercolor=BORDER, focusthickness=0
        )
        style.map(
            "TButton",
            background=[("active", "#EEF2F7"), ("pressed", "#E2E8F0")],
            foreground=[("disabled", MUTED)]
        )
        style.configure(
            "Accent.TButton", padding=(14, 9), background=ACCENT,
            foreground="#FFFFFF", bordercolor=ACCENT,
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "Accent.TButton",
            background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)],
            foreground=[("active", "#FFFFFF"), ("pressed", "#FFFFFF")]
        )
        style.configure(
            "Treeview", background="#FFFFFF", fieldbackground="#FFFFFF",
            foreground=TEXT, rowheight=32, bordercolor=BORDER,
            lightcolor=BORDER, darkcolor=BORDER
        )
        style.configure(
            "Treeview.Heading", background="#F1F5F9", foreground=MUTED,
            font=("Segoe UI", 9, "bold"), padding=(8, 10), relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", "#E0E7FF")],
            foreground=[("selected", TEXT)]
        )

    def create_widgets(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x", pady=(0, 18))

        ttk.Label(
            header, text="Issue Books", style="Title.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Issue available books to registered students and track due dates.",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(4, 0))

        # Issue form panel
        form = tk.Frame(
            outer, bg=PANEL, highlightbackground=BORDER,
            highlightthickness=1, padx=20, pady=18
        )
        form.pack(fill="x", pady=(0, 18))
        form.columnconfigure(1, weight=1)

        ttk.Label(
            form, text="Issue a Book", style="Section.TLabel"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        ttk.Label(
            form, text="Search Student", style="Field.TLabel"
        ).grid(row=1, column=0, sticky="w", padx=(0, 18), pady=8)

        self.student_combo = ttk.Combobox(
            form, textvariable=self.student_var, state="normal"
        )
        self.student_combo.grid(
            row=1, column=1, sticky="ew", pady=8
        )
        self.student_combo.bind("<KeyRelease>", self.filter_students)
        self.student_combo.bind("<<ComboboxSelected>>", self.select_student)
        self.student_combo.bind("<Return>", self.select_first_student_match)

        ttk.Label(
            form, text="Search Available Book", style="Field.TLabel"
        ).grid(row=2, column=0, sticky="w", padx=(0, 18), pady=8)

        self.book_combo = ttk.Combobox(
            form, textvariable=self.book_var, state="normal"
        )
        self.book_combo.grid(row=2, column=1, sticky="ew", pady=8)
        self.book_combo.bind("<KeyRelease>", self.filter_books)
        self.book_combo.bind("<<ComboboxSelected>>", self.select_book)
        self.book_combo.bind("<Return>", self.select_first_book_match)

        dates = tk.Frame(form, bg=PANEL_LIGHT, padx=12, pady=10)
        dates.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 4))
        self.issue_date_label = ttk.Label(dates, style="Panel.TLabel")
        self.issue_date_label.pack(anchor="w")
        self.due_date_label = ttk.Label(dates, style="Panel.TLabel")
        self.due_date_label.pack(anchor="w", pady=(4, 0))

        buttons = ttk.Frame(form, style="Panel.TFrame")
        buttons.grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 0))
        ttk.Button(
            buttons, text="Issue Book", style="Accent.TButton",
            command=self.issue_book
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            buttons, text="Refresh Data", command=self.refresh_data
        ).pack(side="left")

        # Active loans panel
        loans_panel = tk.Frame(
            outer, bg=PANEL, highlightbackground=BORDER,
            highlightthickness=1, padx=14, pady=14
        )
        loans_panel.pack(fill="both", expand=True)

        loans_header = tk.Frame(loans_panel, bg=PANEL)
        loans_header.pack(fill="x", pady=(0, 12))
        ttk.Label(
            loans_header, text="Current Active Loans", style="Section.TLabel"
        ).pack(side="left")
        self.loan_count_label = ttk.Label(
            loans_header, text="0 active loans", style="Panel.TLabel"
        )
        self.loan_count_label.pack(side="right")

        table_frame = ttk.Frame(loans_panel, style="Panel.TFrame")
        table_frame.pack(fill="both", expand=True)

        self.columns = (
            "loan_id", "admission_no", "student_name", "accession_no",
            "book_title", "issue_date", "due_date", "status"
        )
        headings = (
            "Loan ID", "Admission No.", "Student", "Accession No.",
            "Book Title", "Issue Date", "Due Date", "Status"
        )
        widths = (72, 120, 170, 120, 230, 105, 105, 100)

        self.tree = ttk.Treeview(
            table_frame, columns=self.columns, show="headings",
            selectmode="browse"
        )
        for column, heading, width in zip(self.columns, headings, widths):
            self.tree.heading(column, text=heading)
            self.tree.column(
                column, width=width, minwidth=70,
                anchor="center" if column in ("loan_id", "issue_date", "due_date", "status") else "w"
            )

        scrollbar_y = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        scrollbar_x = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("overdue", foreground=RED, background=RED_LIGHT)
        self.tree.tag_configure("on_loan", foreground=GREEN)

    # ---------------- SEARCH ----------------

    def _show_matches(self, combo, matches, typed):
        # Updating values is safe while the user is typing. Do not simulate
        # a Down Arrow keypress here: that can select a suggestion and replace
        # the text after every keystroke. Users can open the filtered list by
        # clicking the combobox arrow or pressing Alt+Down.
        combo["values"] = matches

    def filter_students(self, event=None):
        if event and event.keysym in (
            "Up", "Down", "Left", "Right", "Return", "Escape", "Tab",
            "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"
        ):
            return

        typed = self.student_var.get().strip().lower()
        matches = [
            label for label in self.all_students
            if typed in label.lower()
        ] if typed else self.all_students[:]
        self._show_matches(self.student_combo, matches, typed)

    def filter_books(self, event=None):
        if event and event.keysym in (
            "Up", "Down", "Left", "Right", "Return", "Escape", "Tab",
            "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"
        ):
            return

        typed = self.book_var.get().strip().lower()
        matches = [
            label for label in self.all_books
            if typed in label.lower()
        ] if typed else self.all_books[:]
        self._show_matches(self.book_combo, matches, typed)

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
        elif self.student_var.get() in self.student_options:
            pass
        return "break"

    def select_first_book_match(self, event=None):
        typed = self.book_var.get().strip().lower()
        matches = [
            label for label in self.all_books
            if typed and typed in label.lower()
        ]
        if len(matches) == 1:
            self.book_var.set(matches[0])
        elif self.book_var.get() in self.book_options:
            pass
        return "break"

    # ---------------- DATES ----------------

    def update_date_labels(self):
        today = date.today()
        due = today + timedelta(days=BORROWING_PERIOD_DAYS)
        self.issue_date_label.config(text=f"Issue Date: {today.isoformat()}")
        self.due_date_label.config(
            text=f"Due Date: {due.isoformat()} "
                 f"({BORROWING_PERIOD_DAYS}-day borrowing period)"
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

            current_text = self.student_var.get()
            self.student_options.clear()
            self.all_students = []
            for student_id, admission_no, name, class_name in rows:
                label = f"{admission_no} - {name} ({class_name})"
                self.student_options[label] = student_id
                self.all_students.append(label)

            self.student_combo["values"] = self.all_students
            if current_text not in self.student_options:
                self.student_var.set("")
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", f"Could not load students:\n{error}",
                parent=self.root
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

            current_text = self.book_var.get()
            self.book_options.clear()
            self.all_books = []
            for book_id, accession_no, title, author in rows:
                label = f"{accession_no} - {title} by {author}"
                self.book_options[label] = book_id
                self.all_books.append(label)

            self.book_combo["values"] = self.all_books
            if current_text not in self.book_options:
                self.book_var.set("")
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", f"Could not load available books:\n{error}",
                parent=self.root
            )

    # ---------------- ISSUE BOOK ----------------

    def issue_book(self):
        student_label = self.student_var.get()
        book_label = self.book_var.get()

        if student_label not in self.student_options:
            messagebox.showwarning(
                "Select Student",
                "Select a student from the matching dropdown results.",
                parent=self.root
            )
            return

        if book_label not in self.book_options:
            messagebox.showwarning(
                "Select Book",
                "Select an available book from the matching dropdown results.",
                parent=self.root
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
            "Proceed with issuing this book?",
            parent=self.root
        )
        if not confirm:
            return

        try:
            with connect_db() as db:
                active_loan = db.execute(
                    """
                    SELECT 1 FROM loans
                    WHERE book_id = ? AND return_date IS NULL
                    LIMIT 1
                    """,
                    (book_id,)
                ).fetchone()
                if active_loan:
                    messagebox.showwarning(
                        "Book Unavailable",
                        "This book has already been issued. "
                        "Refresh and select another book.",
                        parent=self.root
                    )
                    self.refresh_data()
                    return

                student_exists = db.execute(
                    "SELECT 1 FROM students WHERE student_id = ?",
                    (student_id,)
                ).fetchone()
                if not student_exists:
                    messagebox.showerror(
                        "Student Not Found",
                        "This student no longer exists.",
                        parent=self.root
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
                f"Due Date: {due_text}",
                parent=self.root
            )
            self.student_var.set("")
            self.book_var.set("")
            self.refresh_data()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Issue Not Completed",
                "The database rejected this issue. The book may already "
                "be on loan, or a related record may no longer exist.",
                parent=self.root
            )
            self.refresh_data()
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", f"Could not issue the book:\n{error}",
                parent=self.root
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
                        l.loan_id, s.admission_no, s.name,
                        b.accession_no, b.title, l.issue_date, l.due_date
                    FROM loans AS l
                    JOIN students AS s ON s.student_id = l.student_id
                    JOIN books AS b ON b.book_id = l.book_id
                    WHERE l.return_date IS NULL
                    ORDER BY l.due_date, s.name
                    """
                ).fetchall()

            for row in rows:
                (
                    loan_id, admission_no, student_name, accession_no,
                    book_title, issue_date, due_date
                ) = row
                status = "Overdue" if due_date < today else "On Loan"
                self.tree.insert(
                    "", "end",
                    values=(
                        loan_id, admission_no, student_name, accession_no,
                        book_title, issue_date, due_date, status
                    ),
                    tags=("overdue",) if status == "Overdue" else ("on_loan",)
                )

            count = len(rows)
            self.loan_count_label.config(
                text=f"{count} active loan{'s' if count != 1 else ''}"
            )
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", f"Could not load active loans:\n{error}",
                parent=self.root
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = IssueBookManager(root)
    root.mainloop()
