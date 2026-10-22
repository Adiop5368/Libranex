import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database import connect_db


# LIBRANEX light theme
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
ORANGE = "#B7791F"


NO_SELECTION_TEXT = "Select one or more loans to record their return."
RETURN_BUTTON_TEXT = "\u2713  Record Return"


class ReturnBooksApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX | Return Books")
        self.root.configure(bg=BG)
        # The root is laid out with grid: header and summary keep their natural
        # height (weight 0) and the main panel (row 2) absorbs all extra space.
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)

        self.search_var = tk.StringVar()
        self.selected_loan_ids = []
        self.active_count_var = tk.StringVar(value="0 active loans")
        self.selection_var = tk.StringVar(value=NO_SELECTION_TEXT)

        self._configure_styles()
        self._build_interface()
        self.load_active_loans()
        self._size_window()

    def _size_window(self):
        """Pick a sensible start size and a minimum size derived from the content.

        The minimum height is the height the widgets actually need (header,
        summary, toolbar, a few table rows and the full footer), so the footer
        can never be squeezed out by a window that is too short.
        """
        self.root.update_idletasks()
        min_w = 900
        min_h = self.root.winfo_reqheight()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        min_w = min(min_w, screen_w - 80)
        min_h = min(min_h, screen_h - 120)
        start_w = max(min_w, min(1120, screen_w - 80))
        start_h = max(min_h, min(720, screen_h - 120))
        self.root.minsize(min_w, min_h)
        self.root.geometry(f"{start_w}x{start_h}")

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Library.Treeview",
            background=PANEL,
            foreground=TEXT,
            fieldbackground=PANEL,
            borderwidth=0,
            rowheight=34,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Library.Treeview.Heading",
            background=PANEL_LIGHT,
            foreground=MUTED,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padding=(10, 10),
        )
        style.map(
            "Library.Treeview",
            background=[("selected", "#E0E7FF")],
            foreground=[("selected", TEXT)],
        )
        style.configure(
            "Library.Vertical.TScrollbar",
            background="#CBD5E1",
            troughcolor=PANEL_LIGHT,
            bordercolor=PANEL_LIGHT,
            arrowcolor=MUTED,
        )

    def _build_interface(self):
        # Header
        header = tk.Frame(self.root, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 16))

        header_inner = tk.Frame(header, bg=PANEL)
        header_inner.pack(fill="x", padx=22, pady=18)

        title_area = tk.Frame(header_inner, bg=PANEL)
        title_area.pack(side="left", fill="x", expand=True)

        tk.Label(
            title_area, text="Return Books", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 21, "bold")
        ).pack(anchor="w")
        tk.Label(
            title_area,
            text="Record returned books and keep the borrowing history accurate.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(4, 0))

        tk.Button(
            header_inner, text="↻  Refresh", command=self.load_active_loans,
            bg=PANEL_LIGHT, fg=TEXT, activebackground="#EEF2F7",
            activeforeground=TEXT, relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"), padx=16, pady=10
        ).pack(side="right")

        # Summary strip
        summary = tk.Frame(self.root, bg=BG)
        summary.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 14))

        summary_card = tk.Frame(summary, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        summary_card.pack(side="left", fill="x", expand=True)

        summary_inner = tk.Frame(summary_card, bg=PANEL)
        summary_inner.pack(fill="x", padx=18, pady=14)
        tk.Label(
            summary_inner, text="BOOKS CURRENTLY ON LOAN",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")
        tk.Label(
            summary_inner, textvariable=self.active_count_var,
            bg=PANEL, fg=ACCENT, font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", pady=(4, 0))

        # Main panel
        panel = tk.Frame(self.root, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        panel.grid(row=2, column=0, sticky="nsew", padx=22, pady=(0, 22))

        # Panel layout (grid): toolbar and footer keep their natural height,
        # only the table row (weight 1) grows or shrinks with the window.
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=0)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_rowconfigure(2, weight=0)

        toolbar = tk.Frame(panel, bg=PANEL)
        toolbar.grid(row=0, column=0, sticky="ew", padx=18, pady=(17, 12))

        tk.Label(
            toolbar, text="Active loans", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(side="left")

        search_box = tk.Frame(toolbar, bg=PANEL_LIGHT, highlightbackground=BORDER, highlightthickness=1)
        search_box.pack(side="right")

        for label, command in (("Clear", self.clear_selection), ("Select all shown", self.select_all_visible)):
            tk.Button(
                toolbar, text=label, command=command,
                bg=PANEL_LIGHT, fg=TEXT, activebackground="#EEF2F7",
                activeforeground=TEXT, relief="flat", bd=0, cursor="hand2",
                highlightbackground=BORDER, highlightthickness=1,
                font=("Segoe UI", 9, "bold"), padx=12, pady=8
            ).pack(side="right", padx=(0, 10))
        tk.Label(search_box, text="⌕", bg=PANEL_LIGHT, fg=MUTED, font=("Segoe UI", 14)).pack(side="left", padx=(10, 4))
        search_entry = tk.Entry(
            search_box, textvariable=self.search_var, width=29,
            bg=PANEL_LIGHT, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, font=("Segoe UI", 10)
        )
        search_entry.pack(side="left", padx=(0, 10), ipady=9)
        search_entry.insert(0, "")
        self.search_var.trace_add("write", lambda *_: self._apply_filter())

        table_frame = tk.Frame(panel, bg=PANEL)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 14))

        columns = ("loan_id", "admission_no", "student", "class_name", "accession_no", "book", "issue_date", "due_date", "status")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            style="Library.Treeview", selectmode="extended", height=4
        )

        headings = {
            "loan_id": "LOAN ID",
            "admission_no": "ADMISSION NO.",
            "student": "STUDENT",
            "class_name": "CLASS",
            "accession_no": "ACCESSION NO.",
            "book": "BOOK TITLE",
            "issue_date": "ISSUED",
            "due_date": "DUE DATE",
            "status": "STATUS",
        }
        widths = {
            "loan_id": 75, "admission_no": 120, "student": 170,
            "class_name": 80, "accession_no": 120, "book": 220,
            "issue_date": 105, "due_date": 105, "status": 100,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], minwidth=65, anchor="w", stretch=(col == "book"))

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview, style="Library.Vertical.TScrollbar")
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("overdue", foreground=RED)
        self.tree.tag_configure("on_time", foreground=TEXT)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda _event: self.return_selected())
        self.tree.bind("<Control-a>", self._select_all_event)
        self.tree.bind("<Control-A>", self._select_all_event)

        footer = tk.Frame(panel, bg=PANEL_LIGHT, highlightbackground=BORDER, highlightthickness=1)
        footer.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=0)

        self.selection_label = tk.Label(
            footer, textvariable=self.selection_var, bg=PANEL_LIGHT, fg=MUTED,
            font=("Segoe UI", 10), anchor="w", justify="left"
        )
        self.selection_label.grid(row=0, column=0, sticky="ew", padx=18, pady=14)
        # Wrap long "Selected: ..." text instead of pushing the button out.
        self.selection_label.bind(
            "<Configure>",
            lambda e: self.selection_label.configure(wraplength=max(e.width - 4, 100))
        )

        self.return_button = tk.Button(
            footer, text=RETURN_BUTTON_TEXT, command=self.return_selected,
            bg=ACCENT, fg="#FFFFFF", activebackground=ACCENT_HOVER,
            activeforeground="#FFFFFF", disabledforeground="#DDE3FF",
            relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 17, "bold"), padx=36, pady=12,
            state="disabled"
        )
        self.return_button.grid(row=0, column=1, sticky="e", padx=16, pady=12)

    def load_active_loans(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with connect_db() as db:
                rows = db.execute("""
                    SELECT
                        l.loan_id,
                        s.admission_no,
                        s.name,
                        s.class_name,
                        b.accession_no,
                        b.title,
                        l.issue_date,
                        l.due_date
                    FROM loans AS l
                    JOIN students AS s ON s.student_id = l.student_id
                    JOIN books AS b ON b.book_id = l.book_id
                    WHERE l.return_date IS NULL
                    ORDER BY l.due_date ASC, s.name COLLATE NOCASE ASC
                """).fetchall()
        except Exception as exc:
            messagebox.showerror("Database Error", f"Could not load active loans.\n\n{exc}", parent=self.root)
            return

        today = date.today()
        self.all_rows = []
        for row in rows:
            loan_id, admission_no, student, class_name, accession_no, book, issue_date, due_date = row
            try:
                is_overdue = date.fromisoformat(due_date) < today
            except (TypeError, ValueError):
                is_overdue = False

            status = "Overdue" if is_overdue else "On time"
            values = (
                loan_id, admission_no, student, class_name, accession_no,
                book, issue_date, due_date, status
            )
            self.all_rows.append((values, "overdue" if is_overdue else "on_time"))

        self.active_count_var.set(f"{len(self.all_rows)} active loan{'s' if len(self.all_rows) != 1 else ''}")
        self.selected_loan_ids = []
        self._apply_filter()

    def _apply_filter(self):
        if not hasattr(self, "all_rows"):
            return

        query = self.search_var.get().strip().casefold()
        selected_before = set(self.selected_loan_ids)

        for item in self.tree.get_children():
            self.tree.delete(item)

        keep_selected = []
        for values, tag in self.all_rows:
            searchable = " ".join(str(value) for value in values).casefold()
            if query and query not in searchable:
                continue
            self.tree.insert("", "end", iid=str(values[0]), values=values, tags=(tag,))
            if values[0] in selected_before:
                keep_selected.append(str(values[0]))

        # Loans hidden by the filter are dropped from the selection, so a
        # return can never be recorded for a row the librarian cannot see.
        if keep_selected:
            self.tree.selection_set(*keep_selected)
        self._on_select()

    def _on_select(self, _event=None):
        selection = self.tree.selection()
        self.selected_loan_ids = [int(item) for item in selection]
        count = len(selection)

        if count == 0:
            self.selection_var.set(NO_SELECTION_TEXT)
            self.return_button.configure(text=RETURN_BUTTON_TEXT, state="disabled")
        elif count == 1:
            values = self.tree.item(selection[0], "values")
            self.selection_var.set(f"Selected: {values[2]} \u2014 {values[5]}")
            self.return_button.configure(text=RETURN_BUTTON_TEXT, state="normal")
        else:
            self.selection_var.set(f"{count} loans selected. Click Record Return to return them all.")
            self.return_button.configure(text=f"\u2713  Record {count} Returns", state="normal")

    def select_all_visible(self):
        self.tree.selection_set(self.tree.get_children())

    def clear_selection(self):
        self.tree.selection_remove(self.tree.selection())

    def _select_all_event(self, _event=None):
        self.select_all_visible()
        return "break"

    def return_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select a Loan", "Please select at least one active loan first.", parent=self.root)
            return

        loans = []
        for item in selection:
            values = self.tree.item(item, "values")
            loans.append((int(item), values[2], values[5]))  # loan_id, student, book

        today = date.today().isoformat()
        max_listed = 8
        listing = "\n".join(f"\u2022 {book} \u2014 {student}" for _id, student, book in loans[:max_listed])
        if len(loans) > max_listed:
            listing += f"\n\u2026 and {len(loans) - max_listed} more"

        if len(loans) == 1:
            question = (
                f"Record this book as returned?\n\nBook: {loans[0][2]}\n"
                f"Student: {loans[0][1]}\n\nReturn date: {today}"
            )
        else:
            question = f"Record these {len(loans)} books as returned?\n\n{listing}\n\nReturn date: {today}"

        if not messagebox.askyesno("Confirm Return", question, parent=self.root):
            return

        updated = 0
        try:
            # One transaction: either every selected return is saved, or none.
            with connect_db() as db:
                for loan_id, _student, _book in loans:
                    cursor = db.execute("""
                        UPDATE loans
                        SET return_date = ?
                        WHERE loan_id = ? AND return_date IS NULL
                    """, (today, loan_id))
                    updated += cursor.rowcount
        except Exception as exc:
            messagebox.showerror("Database Error", f"Could not record the return.\n\n{exc}", parent=self.root)
            self.load_active_loans()
            return

        skipped = len(loans) - updated
        self.load_active_loans()

        if updated == 0:
            messagebox.showwarning(
                "Already Returned",
                "The selected loans are no longer active. The list has been refreshed.",
                parent=self.root
            )
            return

        if len(loans) == 1:
            message = f'"{loans[0][2]}" has been marked as returned.\nThe borrowing history has been preserved.'
        else:
            message = f"{updated} books have been marked as returned.\nThe borrowing history has been preserved."
            if skipped:
                message += f"\n\n{skipped} loan(s) were already returned and were skipped."
        messagebox.showinfo("Return Recorded", message, parent=self.root)


def main():
    root = tk.Tk()
    ReturnBooksApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()