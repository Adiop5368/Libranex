
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database import connect_db


class ReturnBooks:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX - Return Books")
        self.root.geometry("1050x600")
        self.root.minsize(800, 450)

        self.search_var = tk.StringVar()

        self.build_ui()
        self.load_active_loans()

    # -------------------- USER INTERFACE --------------------

    def build_ui(self):
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="Return Books",
            font=("Arial", 20, "bold")
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            main,
            text="Select an active loan to record a book return."
        ).pack(anchor="w", pady=(0, 15))

        search_frame = ttk.Frame(main)
        search_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            search_frame,
            text="Search:"
        ).pack(side="left", padx=(0, 8))

        self.search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=35
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_var.trace_add(
            "write",
            lambda *_: self.load_active_loans()
        )

        ttk.Button(
            search_frame,
            text="Refresh",
            command=self.load_active_loans
        ).pack(side="left", padx=(8, 0))

        table_frame = ttk.Frame(main)
        table_frame.pack(fill="both", expand=True)

        columns = (
            "loan_id",
            "admission_no",
            "student",
            "accession_no",
            "book",
            "issue_date",
            "due_date",
            "status"
        )

        self.loan_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "loan_id": "Loan ID",
            "admission_no": "Admission No.",
            "student": "Student",
            "accession_no": "Accession No.",
            "book": "Book Title",
            "issue_date": "Issue Date",
            "due_date": "Due Date",
            "status": "Status"
        }

        widths = {
            "loan_id": 65,
            "admission_no": 110,
            "student": 150,
            "accession_no": 110,
            "book": 200,
            "issue_date": 100,
            "due_date": 100,
            "status": 90
        }

        for column in columns:
            self.loan_table.heading(
                column,
                text=headings[column]
            )
            self.loan_table.column(
                column,
                width=widths[column],
                minwidth=60,
                anchor="center"
            )

        vertical_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.loan_table.yview
        )

        horizontal_scroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.loan_table.xview
        )

        self.loan_table.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set
        )

        self.loan_table.grid(
            row=0, column=0, sticky="nsew"
        )
        vertical_scroll.grid(
            row=0, column=1, sticky="ns"
        )
        horizontal_scroll.grid(
            row=1, column=0, sticky="ew"
        )

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        button_frame = ttk.Frame(main)
        button_frame.pack(fill="x", pady=(12, 0))

        ttk.Button(
            button_frame,
            text="Return Selected Book",
            command=self.return_book
        ).pack(side="right")

    # -------------------- LOAD ACTIVE LOANS --------------------

    def load_active_loans(self):
        if not hasattr(self, "loan_table"):
            return

        for item in self.loan_table.get_children():
            self.loan_table.delete(item)

        search_text = self.search_var.get().strip().lower()
        today = date.today().isoformat()

        try:
            with connect_db() as db:
                rows = db.execute("""
                    SELECT
                        l.loan_id,
                        s.admission_no,
                        s.name,
                        b.accession_no,
                        b.title,
                        l.issue_date,
                        l.due_date
                    FROM loans l
                    JOIN students s
                        ON s.student_id = l.student_id
                    JOIN books b
                        ON b.book_id = l.book_id
                    WHERE l.return_date IS NULL
                    ORDER BY l.due_date, s.name
                """).fetchall()

            for row in rows:
                (
                    loan_id,
                    admission_no,
                    student,
                    accession_no,
                    book,
                    issue_date,
                    due_date
                ) = row

                searchable_text = " ".join([
                    str(loan_id),
                    admission_no,
                    student,
                    accession_no,
                    book,
                    issue_date,
                    due_date
                ]).lower()

                if search_text and search_text not in searchable_text:
                    continue

                status = (
                    "Overdue"
                    if due_date < today
                    else "Issued"
                )

                self.loan_table.insert(
                    "",
                    "end",
                    iid=str(loan_id),
                    values=(
                        loan_id,
                        admission_no,
                        student,
                        accession_no,
                        book,
                        issue_date,
                        due_date,
                        status
                    )
                )

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load active loans.\n\n{error}"
            )

    # -------------------- RETURN SELECTED BOOK --------------------

    def return_book(self):
        selected_items = self.loan_table.selection()

        if not selected_items:
            messagebox.showwarning(
                "No Loan Selected",
                "Please select a book from the active loans table."
            )
            return

        loan_id = int(selected_items[0])
        values = self.loan_table.item(
            selected_items[0],
            "values"
        )

        student = values[2]
        book = values[4]
        due_date = values[6]
        return_date = date.today().isoformat()

        confirmed = messagebox.askyesno(
            "Confirm Return",
            f"Record this book as returned?\n\n"
            f"Student: {student}\n"
            f"Book: {book}\n"
            f"Due Date: {due_date}\n"
            f"Return Date: {return_date}"
        )

        if not confirmed:
            return

        try:
            with connect_db() as db:
                # Update only if this loan is still active.
                cursor = db.execute("""
                    UPDATE loans
                    SET return_date = ?
                    WHERE loan_id = ?
                      AND return_date IS NULL
                """, (return_date, loan_id))

                if cursor.rowcount == 0:
                    messagebox.showwarning(
                        "Already Returned",
                        "This loan is no longer active. Refresh and try again."
                    )
                    self.load_active_loans()
                    return

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                f"Could not record the return.\n\n{error}"
            )
            return

        messagebox.showinfo(
            "Return Successful",
            f'"{book}" has been returned successfully.'
        )

        self.load_active_loans()


if __name__ == "__main__":
    root = tk.Tk()
    app = ReturnBooks(root)
    root.mainloop()
