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
WHITE = "#FFFFFF"


class StudentManager:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX | Student Management")
        self.root.geometry("1120x740")
        self.root.minsize(900, 620)
        self.root.configure(bg=BG)

        initialize_database()

        self.admission_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.class_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.count_var = tk.StringVar(value="0 students shown")
        self.editing_student_id = None

        self.configure_styles()
        self.create_widgets()
        self.load_students()

    # -------------------- STYLES --------------------

    def configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Students.Treeview",
            background=PANEL,
            foreground=TEXT,
            fieldbackground=PANEL,
            borderwidth=0,
            rowheight=36,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Students.Treeview.Heading",
            background=PANEL_LIGHT,
            foreground=MUTED,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padding=(10, 11),
        )
        style.map(
            "Students.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", WHITE)],
        )
        style.map(
            "Students.Treeview.Heading",
            background=[("active", "#EEF2F7")],
        )
        style.configure(
            "Students.Vertical.TScrollbar",
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
            text="Student Management",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w")

        tk.Label(
            title_area,
            text="Register, find, and maintain student records.",
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

        # Student details form
        form_section = self.make_section(
            main,
            "Student Details",
            "All three fields are required. Select a student to edit their details.",
        )
        form_section.pack(fill="x", pady=(0, 16))

        form = tk.Frame(form_section, bg=PANEL)
        form.pack(fill="x", padx=18, pady=(0, 14))

        fields = [
            ("Admission Number", self.admission_var),
            ("Student Name", self.name_var),
            ("Class / Section", self.class_var),
        ]

        for column, (label_text, variable) in enumerate(fields):
            form.columnconfigure(column, weight=1, uniform="student_fields")
            self.make_label(form, label_text).grid(
                row=0,
                column=column,
                sticky="w",
                padx=(0 if column == 0 else 10, 0),
                pady=(0, 7),
            )
            entry = self.make_entry(form, variable)
            entry.grid(
                row=1,
                column=column,
                sticky="ew",
                padx=(0 if column == 0 else 10, 0),
                ipady=8,
            )
            if column == 0:
                self.admission_entry = entry

        button_row = tk.Frame(form_section, bg=PANEL)
        button_row.pack(fill="x", padx=18, pady=(0, 16))

        self.save_button = self.make_button(
            button_row, "＋  Add Student", self.save_student, primary=True
        )
        self.save_button.pack(side="left", padx=(0, 8))

        self.make_button(
            button_row, "Load Selected to Edit", self.load_selected_for_edit
        ).pack(side="left", padx=(0, 8))
        self.make_button(
            button_row, "Cancel Edit / Clear", self.clear_form
        ).pack(side="left", padx=(0, 8))
        self.make_button(
            button_row, "Remove Selected", self.remove_student, danger=True
        ).pack(side="left")

        # Registered students and search
        student_section = self.make_section(
            main,
            "Registered Students",
            "Search by admission number, student name, or class / section.",
        )
        student_section.pack(fill="both", expand=True)

        search_row = tk.Frame(student_section, bg=PANEL)
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
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_students())

        self.make_button(
            search_row, "Clear Search", self.clear_search
        ).pack(side="left", padx=(8, 0))

        table_container = tk.Frame(student_section, bg=PANEL)
        table_container.pack(fill="both", expand=True, padx=18, pady=(0, 8))

        columns = ("student_id", "admission_no", "name", "class_name")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Students.Treeview",
        )

        headings = {
            "student_id": "ID",
            "admission_no": "Admission No.",
            "name": "Student Name",
            "class_name": "Class / Section",
        }
        for column, heading in headings.items():
            self.tree.heading(column, text=heading)

        self.tree.column("student_id", width=60, minwidth=45, anchor="center", stretch=False)
        self.tree.column("admission_no", width=190, minwidth=130)
        self.tree.column("name", width=360, minwidth=180)
        self.tree.column("class_name", width=190, minwidth=130)

        scrollbar = ttk.Scrollbar(
            table_container,
            orient="vertical",
            command=self.tree.yview,
            style="Students.Vertical.TScrollbar",
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._on_tree_double_click)

        footer = tk.Frame(student_section, bg=PANEL)
        footer.pack(fill="x", padx=18, pady=(5, 14))

        tk.Label(
            footer,
            textvariable=self.count_var,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="left")

        self.make_button(
            footer, "Refresh Students", self.load_students
        ).pack(side="right")

        self.admission_entry.focus_set()

    # -------------------- STUDENT OPERATIONS --------------------

    def save_student(self):
        admission_no = self.admission_var.get().strip()
        name = self.name_var.get().strip()
        class_name = self.class_var.get().strip()

        if not admission_no or not name or not class_name:
            messagebox.showwarning(
                "Missing Information",
                "Please enter the admission number, student name, and class / section.",
                parent=self.root,
            )
            return

        try:
            with connect_db() as db:
                if self.editing_student_id is None:
                    db.execute(
                        """
                        INSERT INTO students (admission_no, name, class_name)
                        VALUES (?, ?, ?)
                        """,
                        (admission_no, name, class_name),
                    )
                    action = "registered"
                else:
                    cursor = db.execute(
                        """
                        UPDATE students
                        SET admission_no = ?, name = ?, class_name = ?
                        WHERE student_id = ?
                        """,
                        (admission_no, name, class_name, self.editing_student_id),
                    )
                    if cursor.rowcount == 0:
                        messagebox.showwarning(
                            "Student Not Found",
                            "This student no longer exists. The form has been cleared.",
                            parent=self.root,
                        )
                        self.clear_form()
                        self.load_students()
                        return
                    action = "updated"

            messagebox.showinfo(
                "Student Details Saved",
                f"Student details {action} successfully.",
                parent=self.root,
            )
            self.clear_form()
            self.load_students()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Admission Number",
                "That admission number already belongs to another student. Please check it and try again.",
                parent=self.root,
            )
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not save student details:\n{error}",
                parent=self.root,
            )

    def load_selected_for_edit(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "No Student Selected",
                "Select a student from the table first.",
                parent=self.root,
            )
            return

        values = self.tree.item(selected[0], "values")
        self.editing_student_id = int(values[0])
        self.admission_var.set(values[1])
        self.name_var.set(values[2])
        self.class_var.set(values[3])
        self.save_button.config(text="Save Changes")
        self.admission_entry.focus_set()

    def _on_tree_double_click(self, event):
        # Ignore double-clicks that do not land on a table row.
        if self.tree.identify_row(event.y):
            self.load_selected_for_edit()

    def remove_student(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "No Student Selected",
                "Select a student from the table first.",
                parent=self.root,
            )
            return

        values = self.tree.item(selected[0], "values")
        student_id = int(values[0])
        student_name = values[2]

        if not messagebox.askyesno(
            "Confirm Removal",
            f"Remove student '{student_name}'?\n\nThis action cannot be undone.",
            parent=self.root,
        ):
            return

        try:
            with connect_db() as db:
                # Preserve student records referenced by any loan history.
                loan = db.execute(
                    "SELECT 1 FROM loans WHERE student_id = ? LIMIT 1",
                    (student_id,),
                ).fetchone()

                if loan:
                    messagebox.showerror(
                        "Cannot Remove Student",
                        "This student has borrowing records and cannot be deleted. Their history must be preserved.",
                        parent=self.root,
                    )
                    return

                cursor = db.execute(
                    "DELETE FROM students WHERE student_id = ?",
                    (student_id,),
                )
                if cursor.rowcount == 0:
                    messagebox.showwarning(
                        "Student Not Found",
                        "The selected student no longer exists.",
                        parent=self.root,
                    )
                    return

            if self.editing_student_id == student_id:
                self.clear_form()

            self.load_students()
            messagebox.showinfo(
                "Student Removed",
                f"Student '{student_name}' was removed successfully.",
                parent=self.root,
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not remove the student:\n{error}",
                parent=self.root,
            )

    def load_students(self):
        if not hasattr(self, "tree"):
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        pattern = f"%{self.search_var.get().strip()}%"
        try:
            with connect_db() as db:
                students = db.execute(
                    """
                    SELECT student_id, admission_no, name, class_name
                    FROM students
                    WHERE admission_no LIKE ? OR name LIKE ? OR class_name LIKE ?
                    ORDER BY name COLLATE NOCASE
                    """,
                    (pattern, pattern, pattern),
                ).fetchall()

            for student in students:
                self.tree.insert("", "end", values=student)

            count = len(students)
            self.count_var.set(f"{count} student{'s' if count != 1 else ''} shown")

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load students:\n{error}",
                parent=self.root,
            )

    # -------------------- FORM CONTROLS --------------------

    def clear_form(self):
        self.admission_var.set("")
        self.name_var.set("")
        self.class_var.set("")
        self.editing_student_id = None
        self.save_button.config(text="＋  Add Student")
        self.admission_entry.focus_set()

    def clear_search(self):
        self.search_var.set("")
        self.load_students()
        self.search_entry.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    app = StudentManager(root)
    root.mainloop()
