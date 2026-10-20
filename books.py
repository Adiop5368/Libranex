
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from database import initialize_database, connect_db


class BookManager:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX - Book Management")
        self.root.geometry("1000x650")
        self.root.minsize(850, 550)

        initialize_database()

        # Variables for the book form
        self.accession_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.search_var = tk.StringVar()

        self.create_widgets()
        self.display_books()

    def create_widgets(self):
        # Main heading
        heading = ttk.Label(
            self.root,
            text="LIBRANEX - Book Management",
            font=("Arial", 20, "bold")
        )
        heading.pack(pady=15)

        # Book entry form
        form = ttk.LabelFrame(
            self.root,
            text="Book Details",
            padding=15
        )
        form.pack(fill="x", padx=20, pady=10)

        for column in range(4):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="Accession Number:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(
            form, textvariable=self.accession_var
        ).grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        ttk.Label(form, text="Book Title:").grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(
            form, textvariable=self.title_var
        ).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form, text="Author:").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(
            form, textvariable=self.author_var
        ).grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        ttk.Label(form, text="Subject:").grid(
            row=0, column=3, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(
            form, textvariable=self.subject_var
        ).grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Form buttons
        button_frame = ttk.Frame(form)
        button_frame.grid(
            row=2, column=0, columnspan=4, pady=12
        )

        ttk.Button(
            button_frame,
            text="Add Book",
            command=self.add_book
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Clear Form",
            command=self.clear_form
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Remove Selected Book",
            command=self.remove_book
        ).pack(side="left", padx=5)

        # Search section
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(
            search_frame,
            text="Search Catalogue:"
        ).pack(side="left", padx=(0, 10))

        self.search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var
        )
        self.search_entry.pack(
            side="left", fill="x", expand=True
        )

        self.search_entry.bind(
            "<KeyRelease>",
            lambda event: self.display_books()
        )

        ttk.Button(
            search_frame,
            text="Clear Search",
            command=self.clear_search
        ).pack(side="left", padx=5)

        # Catalogue table
        table_frame = ttk.LabelFrame(
            self.root,
            text="Book Catalogue",
            padding=10
        )
        table_frame.pack(
            fill="both", expand=True, padx=20, pady=(0, 20)
        )

        columns = (
            "book_id",
            "accession_no",
            "title",
            "author",
            "subject"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("book_id", text="ID")
        self.tree.heading("accession_no", text="Accession No.")
        self.tree.heading("title", text="Book Title")
        self.tree.heading("author", text="Author")
        self.tree.heading("subject", text="Subject")

        self.tree.column("book_id", width=50, anchor="center")
        self.tree.column("accession_no", width=130)
        self.tree.column("title", width=300)
        self.tree.column("author", width=200)
        self.tree.column("subject", width=150)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(
            side="left", fill="both", expand=True
        )
        scrollbar.pack(side="right", fill="y")

    def add_book(self):
        accession_no = self.accession_var.get().strip()
        title = self.title_var.get().strip()
        author = self.author_var.get().strip()
        subject = self.subject_var.get().strip()

        if not accession_no or not title or not author:
            messagebox.showwarning(
                "Missing Information",
                "Accession number, book title, and author are required."
            )
            return

        try:
            with connect_db() as db:
                db.execute(
                    """
                    INSERT INTO books
                    (accession_no, title, author, subject)
                    VALUES (?, ?, ?, ?)
                    """,
                    (accession_no, title, author, subject)
                )

            messagebox.showinfo(
                "Success",
                f"'{title}' was added to the catalogue."
            )

            self.clear_form()
            self.display_books()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Accession Number",
                "This accession number already exists. "
                "Please use a unique number."
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not add the book:\n{error}"
            )

    def display_books(self):
        # Clear the current table
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_text = self.search_var.get().strip()

        try:
            with connect_db() as db:
                books = db.execute(
                    """
                    SELECT book_id, accession_no, title, author, subject
                    FROM books
                    WHERE accession_no LIKE ?
                       OR title LIKE ?
                       OR author LIKE ?
                       OR subject LIKE ?
                    ORDER BY title COLLATE NOCASE
                    """,
                    (
                        f"%{search_text}%",
                        f"%{search_text}%",
                        f"%{search_text}%",
                        f"%{search_text}%"
                    )
                ).fetchall()

            for book in books:
                self.tree.insert("", "end", values=book)

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load the catalogue:\n{error}"
            )

    def remove_book(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Book Selected",
                "Select a book from the catalogue first."
            )
            return

        values = self.tree.item(selected[0], "values")
        book_id = values[0]
        book_title = values[2]

        confirm = messagebox.askyesno(
            "Confirm Removal",
            f"Remove '{book_title}' from the catalogue?"
        )

        if not confirm:
            return

        try:
            with connect_db() as db:
                # Preserve any book with borrowing history
                loan = db.execute(
                    """
                    SELECT 1
                    FROM loans
                    WHERE book_id = ?
                    LIMIT 1
                    """,
                    (book_id,)
                ).fetchone()

                if loan:
                    messagebox.showerror(
                        "Cannot Remove Book",
                        "This book has borrowing records and cannot "
                        "be deleted. Its history must be preserved."
                    )
                    return

                cursor = db.execute(
                    "DELETE FROM books WHERE book_id = ?",
                    (book_id,)
                )

                if cursor.rowcount == 0:
                    messagebox.showwarning(
                        "Book Not Found",
                        "The selected book no longer exists."
                    )
                    return

            self.clear_form()
            self.display_books()

            messagebox.showinfo(
                "Success",
                f"'{book_title}' was removed successfully."
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not remove the book:\n{error}"
            )

    def clear_form(self):
        self.accession_var.set("")
        self.title_var.set("")
        self.author_var.set("")
        self.subject_var.set("")

    def clear_search(self):
        self.search_var.set("")
        self.display_books()


if __name__ == "__main__":
    root = tk.Tk()
    app = BookManager(root)
    root.mainloop()
