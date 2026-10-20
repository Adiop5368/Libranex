
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import subprocess
import sys
from pathlib import Path

from database import connect_db


class LibranexDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX - Library Dashboard")
        self.root.geometry("1100x720")
        self.root.minsize(850, 600)

        self.project_dir = Path(__file__).resolve().parent

        self.build_ui()
        self.refresh_dashboard()

    # -------------------- USER INTERFACE --------------------

    def build_ui(self):
        self.root.configure(bg="#f3f5f9")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Arial", 23, "bold"),
            background="#f3f5f9"
        )
        style.configure(
            "Subtitle.TLabel",
            font=("Arial", 10),
            background="#f3f5f9",
            foreground="#555555"
        )
        style.configure(
            "CardTitle.TLabel",
            font=("Arial", 10),
            foreground="#555555"
        )
        style.configure(
            "CardValue.TLabel",
            font=("Arial", 23, "bold")
        )

        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)

        # Header
        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 18))

        header_text = ttk.Frame(header)
        header_text.pack(side="left", fill="x", expand=True)

        ttk.Label(
            header_text,
            text="LIBRANEX",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            header_text,
            text="School Library Management System",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(4, 0))

        ttk.Button(
            header,
            text="Refresh Dashboard",
            command=self.refresh_dashboard
        ).pack(side="right", padx=5)

        # Statistics cards
        cards_frame = ttk.Frame(main)
        cards_frame.pack(fill="x", pady=(0, 20))

        self.stat_labels = {}

        card_data = [
            ("books", "Total Books"),
            ("students", "Registered Students"),
            ("issued", "Books Issued"),
            ("overdue", "Overdue Books")
        ]

        for index, (key, title) in enumerate(card_data):
            card = ttk.LabelFrame(
                cards_frame,
                text=title,
                padding=15
            )
            card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=5
            )

            value_label = ttk.Label(
                card,
                text="0",
                style="CardValue.TLabel"
            )
            value_label.pack(anchor="w")

            self.stat_labels[key] = value_label
            cards_frame.columnconfigure(index, weight=1)

        # Navigation
        navigation = ttk.LabelFrame(
            main,
            text="Library Operations",
            padding=12
        )
        navigation.pack(fill="x", pady=(0, 20))

        buttons = [
            ("Manage Books", "books.py"),
            ("Manage Students", "students.py"),
            ("Issue Books", "issue_books.py"),
            ("Return Books", "return_books.py")
        ]

        for index, (label, filename) in enumerate(buttons):
            ttk.Button(
                navigation,
                text=label,
                command=lambda f=filename: self.open_module(f)
            ).grid(
                row=0,
                column=index,
                sticky="ew",
                padx=5,
                pady=5,
                ipady=8
            )
            navigation.columnconfigure(index, weight=1)

        # Active loans
        loans_frame = ttk.LabelFrame(
            main,
            text="Currently Issued Books",
            padding=10
        )
        loans_frame.pack(fill="both", expand=True)

        columns = (
            "student",
            "admission",
            "book",
            "accession",
            "due_date",
            "status"
        )

        self.loan_table = ttk.Treeview(
            loans_frame,
            columns=columns,
            show="headings",
            height=10
        )

        heading_names = {
            "student": "Student",
            "admission": "Admission No.",
            "book": "Book Title",
            "accession": "Accession No.",
            "due_date": "Due Date",
            "status": "Status"
        }

        widths = {
            "student": 170,
            "admission": 120,
            "book": 230,
            "accession": 120,
            "due_date": 110,
            "status": 100
        }

        for column in columns:
            self.loan_table.heading(
                column,
                text=heading_names[column]
            )
            self.loan_table.column(
                column,
                width=widths[column],
                minwidth=60,
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            loans_frame,
            orient="vertical",
            command=self.loan_table.yview
        )
        self.loan_table.configure(
            yscrollcommand=scrollbar.set
        )

        self.loan_table.pack(
            side="left",
            fill="both",
            expand=True
        )
        scrollbar.pack(side="right", fill="y")

        # Footer
        ttk.Label(
            main,
            text="LIBRANEX | School Library System",
            style="Subtitle.TLabel"
        ).pack(anchor="center", pady=(12, 0))

    # -------------------- DASHBOARD DATA --------------------

    def refresh_dashboard(self):
        try:
            today = date.today().isoformat()

            with connect_db() as db:
                total_books = db.execute("""
                    SELECT COUNT(*) FROM books
                """).fetchone()[0]

                total_students = db.execute("""
                    SELECT COUNT(*) FROM students
                """).fetchone()[0]

                active_loans = db.execute("""
                    SELECT COUNT(*)
                    FROM loans
                    WHERE return_date IS NULL
                """).fetchone()[0]

                overdue_loans = db.execute("""
                    SELECT COUNT(*)
                    FROM loans
                    WHERE return_date IS NULL
                      AND due_date < ?
                """, (today,)).fetchone()[0]

                recent_loans = db.execute("""
                    SELECT
                        s.name,
                        s.admission_no,
                        b.title,
                        b.accession_no,
                        l.due_date
                    FROM loans l
                    JOIN students s
                        ON s.student_id = l.student_id
                    JOIN books b
                        ON b.book_id = l.book_id
                    WHERE l.return_date IS NULL
                    ORDER BY l.issue_date DESC, l.loan_id DESC
                """).fetchall()

            self.stat_labels["books"].config(
                text=str(total_books)
            )
            self.stat_labels["students"].config(
                text=str(total_students)
            )
            self.stat_labels["issued"].config(
                text=str(active_loans)
            )
            self.stat_labels["overdue"].config(
                text=str(overdue_loans)
            )

            for item in self.loan_table.get_children():
                self.loan_table.delete(item)

            for row in recent_loans:
                student, admission, book, accession, due_date = row

                status = (
                    "Overdue"
                    if due_date < today
                    else "Issued"
                )

                self.loan_table.insert(
                    "",
                    "end",
                    values=(
                        student,
                        admission,
                        book,
                        accession,
                        due_date,
                        status
                    )
                )

        except Exception as error:
            messagebox.showerror(
                "Dashboard Error",
                f"Could not load dashboard data.\n\n{error}"
            )

    # -------------------- OPEN MODULES --------------------

    def open_module(self, filename):
        module_path = self.project_dir / filename

        if not module_path.is_file():
            messagebox.showerror(
                "Module Not Found",
                f"Could not find:\n{module_path}\n\n"
                "Make sure all LIBRANEX modules are in the same folder."
            )
            return

        try:
            subprocess.Popen(
                [sys.executable, str(module_path)],
                cwd=str(self.project_dir)
            )
        except Exception as error:
            messagebox.showerror(
                "Unable to Open Module",
                f"Could not open {filename}.\n\n{error}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = LibranexDashboard(root)
    root.mainloop()
