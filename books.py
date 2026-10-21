import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from database import connect_db, initialize_database


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


class BookManager:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX | Book Management")
        self.root.geometry("1120x740")
        self.root.minsize(900, 620)
        self.root.configure(bg=BG)

        initialize_database()

        self.accession_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.count_var = tk.StringVar(value="0 books")

        self.configure_styles()
        self.create_widgets()
        self.display_books()

    # -------------------- STYLES --------------------

    def configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Books.Treeview",
            background=PANEL,
            foreground=TEXT,
            fieldbackground=PANEL,
            borderwidth=0,
            rowheight=36,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Books.Treeview.Heading",
            background=PANEL_LIGHT,
            foreground=MUTED,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padding=(10, 11),
        )
        style.map(
            "Books.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", WHITE)],
        )
        style.map(
            "Books.Treeview.Heading",
            background=[("active", "#EEF2F7")],
        )
        style.configure(
            "Books.Vertical.TScrollbar",
            background="#DCE3EC",
            troughcolor=BG,
            bordercolor=BG,
            arrowcolor=MUTED,
            relief="flat",
        )

    # -------------------- UI HELPERS --------------------

    def make_button(self, parent, text, command, primary=False, danger=False):
        if primary:
            bg, active_bg, fg = ACCENT, ACCENT_HOVER, WHITE
        elif danger:
            bg, active_bg, fg = "#FCEEEE", "#F8DDDD", "#A94343"
        else:
            bg, active_bg, fg = PANEL_LIGHT, "#EEF2F7", TEXT

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold" if primary else "normal"),
            padx=14,
            pady=9,
        )

    def make_section(self, parent, title, subtitle=None):
        section = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        heading = tk.Frame(section, bg=PANEL)
        heading.pack(fill="x", padx=18, pady=(15, 10))

        tk.Label(
            heading,
            text=title,
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                heading,
                text=subtitle,
                bg=PANEL,
                fg=MUTED,
                font=("Segoe UI", 9),
            ).pack(anchor="w", pady=(3, 0))

        return section

    def make_label(self, parent, text):
        return tk.Label(
            parent,
            text=text,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
        )

    def make_entry(self, parent, variable):
        return tk.Entry(
            parent,
            textvariable=variable,
            bg=WHITE,
            fg=TEXT,
            insertbackground=TEXT,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            font=("Segoe UI", 10),
        )

    # -------------------- BUILD UI --------------------

    def create_widgets(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=26, pady=22)

        # Header
        header = tk.Frame(main, bg=BG)
        header.pack(fill="x", pady=(0, 18))

        title_area = tk.Frame(header, bg=BG)
        title_area.pack(side="left", fill="x", expand=True)

        tk.Label(
            title_area,
            text="Book Management",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w")

        tk.Label(
            title_area,
            text="Add, find, and manage the library catalogue.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            header,
            text="LIBRANEX",
            bg=BG,
            fg=ACCENT,
            font=("Segoe UI", 12, "bold"),
        ).pack(side="right", anchor="n", padx=(12, 0), pady=7)

        # Book form
        form_section = self.make_section(
            main,
            "Book Details",
            "Accession number, title, and author are required.",
        )
        form_section.pack(fill="x", pady=(0, 16))

        form = tk.Frame(form_section, bg=PANEL)
        form.pack(fill="x", padx=18, pady=(0, 16))

        fields = [
            ("Accession Number", self.accession_var),
            ("Book Title", self.title_var),
            ("Author", self.author_var),
            ("Subject", self.subject_var),
        ]

        for column, (label_text, variable) in enumerate(fields):
            form.columnconfigure(column, weight=1, uniform="book_fields")
            self.make_label(form, label_text).grid(
                row=0, column=column, sticky="w", padx=(0 if column == 0 else 10, 0), pady=(0, 7)
            )
            entry = self.make_entry(form, variable)
            entry.grid(
                row=1, column=column, sticky="ew",
                padx=(0 if column == 0 else 10, 0), ipady=8
            )
            if column == 0:
                self.accession_entry = entry

        button_row = tk.Frame(form_section, bg=PANEL)
        button_row.pack(fill="x", padx=18, pady=(0, 16))

        self.make_button(
            button_row, "＋  Add Book", self.add_book, primary=True
        ).pack(side="left", padx=(0, 8))
        self.make_button(
            button_row, "Clear Form", self.clear_form
        ).pack(side="left", padx=(0, 8))
        self.make_button(
            button_row, "Remove Selected", self.remove_book, danger=True
        ).pack(side="left")

        # Catalogue and search
        catalogue = self.make_section(
            main,
            "Book Catalogue",
            "Search by accession number, title, author, or subject.",
        )
        catalogue.pack(fill="both", expand=True)

        search_row = tk.Frame(catalogue, bg=PANEL)
        search_row.pack(fill="x", padx=18, pady=(0, 13))

        tk.Label(
            search_row,
            text="Search",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 10))

        self.search_entry = self.make_entry(search_row, self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.search_entry.bind("<KeyRelease>", lambda event: self.display_books())

        self.make_button(
            search_row, "Clear Search", self.clear_search
        ).pack(side="left", padx=(8, 0))

        table_container = tk.Frame(catalogue, bg=PANEL)
        table_container.pack(fill="both", expand=True, padx=18, pady=(0, 8))

        columns = ("book_id", "accession_no", "title", "author", "subject")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Books.Treeview",
        )

        headings = {
            "book_id": "ID",
            "accession_no": "Accession No.",
            "title": "Book Title",
            "author": "Author",
            "subject": "Subject",
        }
        for column, heading in headings.items():
            self.tree.heading(column, text=heading)

        self.tree.column("book_id", width=55, minwidth=45, anchor="center", stretch=False)
        self.tree.column("accession_no", width=145, minwidth=115)
        self.tree.column("title", width=330, minwidth=180)
        self.tree.column("author", width=220, minwidth=140)
        self.tree.column("subject", width=180, minwidth=110)

        scrollbar = ttk.Scrollbar(
            table_container,
            orient="vertical",
            command=self.tree.yview,
            style="Books.Vertical.TScrollbar",
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        footer = tk.Frame(catalogue, bg=PANEL)
        footer.pack(fill="x", padx=18, pady=(5, 14))

        tk.Label(
            footer,
            textvariable=self.count_var,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="left")

        self.make_button(
            footer, "Refresh Catalogue", self.display_books
        ).pack(side="right")

        self.accession_entry.focus_set()

    # -------------------- BOOK OPERATIONS --------------------

    def add_book(self):
        accession_no = self.accession_var.get().strip()
        title = self.title_var.get().strip()
        author = self.author_var.get().strip()
        subject = self.subject_var.get().strip()

        if not accession_no or not title or not author:
            messagebox.showwarning(
                "Missing Information",
                "Accession number, book title, and author are required.",
                parent=self.root,
            )
            return

        try:
            with connect_db() as db:
                db.execute(
                    """
                    INSERT INTO books (accession_no, title, author, subject)
                    VALUES (?, ?, ?, ?)
                    """,
                    (accession_no, title, author, subject),
                )

            messagebox.showinfo(
                "Book Added",
                f"'{title}' was added to the catalogue.",
                parent=self.root,
            )
            self.clear_form()
            self.display_books()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Accession Number",
                "This accession number already exists. Please use a unique number.",
                parent=self.root,
            )
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not add the book:\n{error}",
                parent=self.root,
            )

    def display_books(self):
        if not hasattr(self, "tree"):
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        search_text = self.search_var.get().strip()
        pattern = f"%{search_text}%"

        try:
            with connect_db() as db:
                books = db.execute(
                    """
                    SELECT book_id, accession_no, title, author, COALESCE(subject, '')
                    FROM books
                    WHERE accession_no LIKE ?
                       OR title LIKE ?
                       OR author LIKE ?
                       OR COALESCE(subject, '') LIKE ?
                    ORDER BY title COLLATE NOCASE
                    """,
                    (pattern, pattern, pattern, pattern),
                ).fetchall()

            for book in books:
                self.tree.insert("", "end", values=book)

            count = len(books)
            self.count_var.set(f"{count} book{'s' if count != 1 else ''} shown")

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load the catalogue:\n{error}",
                parent=self.root,
            )

    def remove_book(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Book Selected",
                "Select a book from the catalogue first.",
                parent=self.root,
            )
            return

        values = self.tree.item(selected[0], "values")
        book_id, book_title = values[0], values[2]

        if not messagebox.askyesno(
            "Confirm Removal",
            f"Remove '{book_title}' from the catalogue?",
            parent=self.root,
        ):
            return

        try:
            with connect_db() as db:
                # Keep book records that are referenced by borrowing history.
                loan = db.execute(
                    "SELECT 1 FROM loans WHERE book_id = ? LIMIT 1",
                    (book_id,),
                ).fetchone()

                if loan:
                    messagebox.showerror(
                        "Cannot Remove Book",
                        "This book has borrowing records and cannot be deleted. "
                        "Its history must be preserved.",
                        parent=self.root,
                    )
                    return

                cursor = db.execute(
                    "DELETE FROM books WHERE book_id = ?",
                    (book_id,),
                )

                if cursor.rowcount == 0:
                    messagebox.showwarning(
                        "Book Not Found",
                        "The selected book no longer exists.",
                        parent=self.root,
                    )
                    return

            self.clear_form()
            self.display_books()
            messagebox.showinfo(
                "Book Removed",
                f"'{book_title}' was removed successfully.",
                parent=self.root,
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not remove the book:\n{error}",
                parent=self.root,
            )

    # -------------------- FORM CONTROLS --------------------

    def clear_form(self):
        self.accession_var.set("")
        self.title_var.set("")
        self.author_var.set("")
        self.subject_var.set("")
        if hasattr(self, "accession_entry"):
            self.accession_entry.focus_set()

    def clear_search(self):
        self.search_var.set("")
        self.display_books()
        self.search_entry.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    app = BookManager(root)
    root.mainloop()
