import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
from pathlib import Path
from datetime import date

from database import connect_db


# -------------------- THEME --------------------

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
WHITE = "#FFFFFF"


class LibranexDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX | Library Dashboard")
        self.root.geometry("1180x760")
        self.root.minsize(900, 620)
        self.root.configure(bg=BG)

        self.project_dir = Path(__file__).resolve().parent

        self.configure_styles()
        self.build_ui()
        self.refresh_dashboard()

    # -------------------- STYLES --------------------

    def configure_styles(self):
        style = ttk.Style(self.root)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "App.Treeview",
            background=PANEL,
            foreground=TEXT,
            fieldbackground=PANEL,
            borderwidth=0,
            rowheight=36,
            font=("Segoe UI", 10),
        )
        style.configure(
            "App.Treeview.Heading",
            background=PANEL_LIGHT,
            foreground=MUTED,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padding=(10, 11),
        )
        style.map(
            "App.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", WHITE)],
        )
        style.map(
            "App.Treeview.Heading",
            background=[("active", "#EEF2F7")],
        )
        style.configure(
            "App.Vertical.TScrollbar",
            background="#DCE3EC",
            troughcolor=BG,
            bordercolor=BG,
            arrowcolor=MUTED,
            relief="flat",
        )
        style.configure(
            "App.Horizontal.TScrollbar",
            background="#DCE3EC",
            troughcolor=BG,
            bordercolor=BG,
            arrowcolor=MUTED,
            relief="flat",
        )

    # -------------------- UI HELPERS --------------------

    def make_button(self, parent, text, command, primary=False):
        bg = ACCENT if primary else PANEL_LIGHT
        active_bg = ACCENT_HOVER if primary else "#EEF2F7"
        foreground = WHITE if primary else TEXT

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=foreground,
            activebackground=active_bg,
            activeforeground=foreground,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold" if primary else "normal"),
            padx=15,
            pady=9,
        )

    def make_card(self, parent, title, value, subtitle, accent):
        card = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )

        tk.Frame(card, bg=accent, height=4).pack(fill="x")

        content = tk.Frame(card, bg=PANEL)
        content.pack(fill="both", expand=True, padx=16, pady=14)

        tk.Label(
            content,
            text=title.upper(),
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x")

        value_label = tk.Label(
            content,
            text=str(value),
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 27, "bold"),
            anchor="w",
        )
        value_label.pack(fill="x", pady=(8, 3))

        tk.Label(
            content,
            text=subtitle,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="x")

        return card, value_label

    # -------------------- BUILD DASHBOARD --------------------

    def build_ui(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=24, pady=20)

        # Header
        header = tk.Frame(main, bg=BG)
        header.pack(fill="x", pady=(0, 22))

        title_area = tk.Frame(header, bg=BG)
        title_area.pack(side="left", fill="x", expand=True)

        tk.Label(
            title_area,
            text="LIBRANEX",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 27, "bold"),
        ).pack(anchor="w")

        tk.Label(
            title_area,
            text="SCHOOL LIBRARY MANAGEMENT SYSTEM",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(4, 0))

        right_header = tk.Frame(header, bg=BG)
        right_header.pack(side="right", anchor="center")

        self.date_label = tk.Label(
            right_header,
            text=date.today().strftime("%d %B %Y"),
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        )
        self.date_label.pack(anchor="e", pady=(0, 8))

        self.make_button(
            right_header,
            "↻  Refresh",
            self.refresh_dashboard,
            primary=True,
        ).pack(anchor="e")

        # Statistics cards
        tk.Label(
            main,
            text="Library Overview",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        cards = tk.Frame(main, bg=BG)
        cards.pack(fill="x", pady=(0, 24))

        card_definitions = [
            ("books", "Total Books", "In catalogue", "#5B78D1"),
            ("students", "Students", "Registered members", "#8874B8"),
            ("issued", "Books Issued", "Currently on loan", GREEN),
            ("overdue", "Overdue", "Past their due date", RED),
        ]

        self.stat_labels = {}

        for index, (key, title, subtitle, accent) in enumerate(card_definitions):
            card, value_label = self.make_card(
                cards, title, 0, subtitle, accent
            )
            left_pad = 0 if index == 0 else 7
            right_pad = 0 if index == len(card_definitions) - 1 else 7
            card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(left_pad, right_pad),
            )
            cards.columnconfigure(index, weight=1, uniform="stats")
            self.stat_labels[key] = value_label

        # Navigation
        nav_section = tk.Frame(main, bg=BG)
        nav_section.pack(fill="x", pady=(0, 24))

        tk.Label(
            nav_section,
            text="Library Operations",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        nav_panel = tk.Frame(
            nav_section,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        nav_panel.pack(fill="x", ipady=8)

        modules = [
            ("01", "Manage Books", "books.py"),
            ("02", "Manage Students", "students.py"),
            ("03", "Issue Books", "issue_books.py"),
            ("04", "Return Books", "return_books.py"),
        ]

        for index, (number, label, filename) in enumerate(modules):
            item = tk.Frame(nav_panel, bg=PANEL)
            item.grid(row=0, column=index, sticky="nsew", padx=10, pady=10)

            tk.Label(
                item,
                text=number,
                bg=PANEL,
                fg=ACCENT,
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", pady=(0, 8))

            self.make_button(
                item,
                label,
                lambda f=filename: self.open_module(f),
                primary=(index == 2),
            ).pack(fill="x")

            nav_panel.columnconfigure(index, weight=1, uniform="modules")

        # Active loans table
        loans_panel = tk.Frame(
            main,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        loans_panel.pack(fill="both", expand=True)

        table_header = tk.Frame(loans_panel, bg=PANEL)
        table_header.pack(fill="x", padx=16, pady=(15, 12))

        tk.Label(
            table_header,
            text="Currently Issued Books",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        self.loan_count_label = tk.Label(
            table_header,
            text="0 active loans",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
        )
        self.loan_count_label.pack(side="right")

        table_container = tk.Frame(loans_panel, bg=PANEL)
        table_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        columns = (
            "student", "admission", "book", "accession", "due_date", "status"
        )

        self.loan_table = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            style="App.Treeview",
            selectmode="browse",
        )

        headings = {
            "student": "STUDENT",
            "admission": "ADMISSION NO.",
            "book": "BOOK TITLE",
            "accession": "ACCESSION NO.",
            "due_date": "DUE DATE",
            "status": "STATUS",
        }
        widths = {
            "student": 165,
            "admission": 125,
            "book": 230,
            "accession": 125,
            "due_date": 115,
            "status": 95,
        }

        for column in columns:
            self.loan_table.heading(column, text=headings[column])
            self.loan_table.column(
                column,
                width=widths[column],
                minwidth=70,
                anchor="w" if column in ("student", "book") else "center",
            )

        self.loan_table.tag_configure("overdue", foreground=RED)
        self.loan_table.tag_configure("issued", foreground=GREEN)

        y_scroll = ttk.Scrollbar(
            table_container,
            orient="vertical",
            command=self.loan_table.yview,
            style="App.Vertical.TScrollbar",
        )
        x_scroll = ttk.Scrollbar(
            table_container,
            orient="horizontal",
            command=self.loan_table.xview,
            style="App.Horizontal.TScrollbar",
        )

        self.loan_table.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self.loan_table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

        # Footer
        footer = tk.Frame(main, bg=BG)
        footer.pack(fill="x", pady=(14, 0))

        tk.Label(
            footer,
            text="LIBRANEX  •  School Library System",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="left")

        tk.Label(
            footer,
            text="Local Database",
            bg=BG,
            fg=GREEN,
            font=("Segoe UI", 9),
        ).pack(side="right")

    # -------------------- LOAD DASHBOARD DATA --------------------

    def refresh_dashboard(self):
        today = date.today().isoformat()

        try:
            with connect_db() as db:
                total_books = db.execute(
                    "SELECT COUNT(*) FROM books"
                ).fetchone()[0]

                total_students = db.execute(
                    "SELECT COUNT(*) FROM students"
                ).fetchone()[0]

                active_loans = db.execute(
                    "SELECT COUNT(*) FROM loans WHERE return_date IS NULL"
                ).fetchone()[0]

                overdue_loans = db.execute(
                    """
                    SELECT COUNT(*)
                    FROM loans
                    WHERE return_date IS NULL AND due_date < ?
                    """,
                    (today,),
                ).fetchone()[0]

                rows = db.execute(
                    """
                    SELECT
                        s.name,
                        s.admission_no,
                        b.title,
                        b.accession_no,
                        l.due_date
                    FROM loans l
                    JOIN students s ON s.student_id = l.student_id
                    JOIN books b ON b.book_id = l.book_id
                    WHERE l.return_date IS NULL
                    ORDER BY l.issue_date DESC, l.loan_id DESC
                    """
                ).fetchall()

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to load dashboard information.\n\n{error}",
                parent=self.root,
            )
            return

        self.stat_labels["books"].config(text=str(total_books))
        self.stat_labels["students"].config(text=str(total_students))
        self.stat_labels["issued"].config(text=str(active_loans))
        self.stat_labels["overdue"].config(text=str(overdue_loans))

        for item in self.loan_table.get_children():
            self.loan_table.delete(item)

        for student, admission, book, accession, due_date in rows:
            is_overdue = due_date < today
            status = "Overdue" if is_overdue else "Issued"
            tag = "overdue" if is_overdue else "issued"

            self.loan_table.insert(
                "",
                "end",
                values=(student, admission, book, accession, due_date, status),
                tags=(tag,),
            )

        self.loan_count_label.config(
            text=f"{active_loans} active loan" + ("" if active_loans == 1 else "s")
        )
        self.date_label.config(text=date.today().strftime("%d %B %Y"))

    # -------------------- OPEN MODULES --------------------

    def open_module(self, filename):
        module_path = self.project_dir / filename

        if not module_path.is_file():
            messagebox.showerror(
                "Module Not Found",
                f"Could not find:\n{module_path}\n\n"
                "Ensure the module is in the same folder as dashboard.py.",
                parent=self.root,
            )
            return

        try:
            subprocess.Popen(
                [sys.executable, str(module_path)],
                cwd=str(self.project_dir),
            )
        except Exception as error:
            messagebox.showerror(
                "Unable to Open Module",
                f"Could not open {filename}.\n\n{error}",
                parent=self.root,
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = LibranexDashboard(root)
    root.mainloop()
