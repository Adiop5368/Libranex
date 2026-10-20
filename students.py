
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from database import initialize_database, connect_db


class StudentManager:
    def __init__(self, root):
        self.root = root
        self.root.title("LIBRANEX - Student Management")
        self.root.geometry("1000x650")
        self.root.minsize(850, 550)

        initialize_database()

        # Student form variables
        self.admission_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.class_var = tk.StringVar()
        self.search_var = tk.StringVar()

        # Tracks which student is being edited
        self.editing_student_id = None

        self.create_widgets()
        self.load_students()

    def create_widgets(self):
        ttk.Label(
            self.root,
            text="LIBRANEX - Student Management",
            font=("Arial", 20, "bold")
        ).pack(pady=15)

        # Student details form
        form = ttk.LabelFrame(
            self.root,
            text="Student Details",
            padding=15
        )
        form.pack(fill="x", padx=20, pady=10)

        for column in range(3):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="Admission Number:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(
            form, textvariable=self.admission_var
        ).grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        ttk.Label(form, text="Student Name:").grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(
            form, textvariable=self.name_var
        ).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form, text="Class / Section:").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(
            form, textvariable=self.class_var
        ).grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # Action buttons
        button_frame = ttk.Frame(form)
        button_frame.grid(
            row=2, column=0, columnspan=3, pady=12
        )

        self.save_button = ttk.Button(
            button_frame,
            text="Add Student",
            command=self.save_student
        )
        self.save_button.pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Load Selected to Edit",
            command=self.load_selected_for_edit
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Cancel Edit / Clear",
            command=self.clear_form
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Remove Selected Student",
            command=self.remove_student
        ).pack(side="left", padx=5)

        # Search area
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(
            search_frame,
            text="Search Students:"
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
            lambda event: self.load_students()
        )

        ttk.Button(
            search_frame,
            text="Clear Search",
            command=self.clear_search
        ).pack(side="left", padx=5)

        # Student table
        table_frame = ttk.LabelFrame(
            self.root,
            text="Registered Students",
            padding=10
        )
        table_frame.pack(
            fill="both", expand=True, padx=20, pady=(0, 20)
        )

        columns = (
            "student_id",
            "admission_no",
            "name",
            "class_name"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("student_id", text="ID")
        self.tree.heading("admission_no", text="Admission No.")
        self.tree.heading("name", text="Student Name")
        self.tree.heading("class_name", text="Class / Section")

        self.tree.column("student_id", width=60, anchor="center")
        self.tree.column("admission_no", width=180)
        self.tree.column("name", width=350)
        self.tree.column("class_name", width=180)

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

        # Double-click a row to load its details for editing
        self.tree.bind(
            "<Double-1>",
            lambda event: self.load_selected_for_edit()
        )

    def save_student(self):
        admission_no = self.admission_var.get().strip()
        name = self.name_var.get().strip()
        class_name = self.class_var.get().strip()

        if not admission_no or not name or not class_name:
            messagebox.showwarning(
                "Missing Information",
                "Please enter the admission number, name, "
                "and class / section."
            )
            return

        try:
            with connect_db() as db:
                if self.editing_student_id is None:
                    # Register a new student
                    db.execute(
                        """
                        INSERT INTO students
                        (admission_no, name, class_name)
                        VALUES (?, ?, ?)
                        """,
                        (admission_no, name, class_name)
                    )
                    action = "registered"

                else:
                    # Update the currently selected student
                    db.execute(
                        """
                        UPDATE students
                        SET admission_no = ?,
                            name = ?,
                            class_name = ?
                        WHERE student_id = ?
                        """,
                        (
                            admission_no,
                            name,
                            class_name,
                            self.editing_student_id
                        )
                    )
                    action = "updated"

            messagebox.showinfo(
                "Success",
                f"Student details {action} successfully."
            )

            self.clear_form()
            self.load_students()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate Admission Number",
                "That admission number already belongs to "
                "another student. Please check it and try again."
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not save student details:\n{error}"
            )

    def load_selected_for_edit(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Student Selected",
                "Select a student from the table first."
            )
            return

        values = self.tree.item(selected[0], "values")

        self.editing_student_id = int(values[0])
        self.admission_var.set(values[1])
        self.name_var.set(values[2])
        self.class_var.set(values[3])

        self.save_button.config(text="Save Changes")

    def remove_student(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Student Selected",
                "Select a student from the table first."
            )
            return

        values = self.tree.item(selected[0], "values")
        student_id = int(values[0])
        student_name = values[2]

        confirm = messagebox.askyesno(
            "Confirm Removal",
            f"Remove student '{student_name}'?\n\n"
            "This action cannot be undone."
        )

        if not confirm:
            return

        try:
            with connect_db() as db:
                # Keep students who have any borrowing history
                loan = db.execute(
                    """
                    SELECT 1
                    FROM loans
                    WHERE student_id = ?
                    LIMIT 1
                    """,
                    (student_id,)
                ).fetchone()

                if loan:
                    messagebox.showerror(
                        "Cannot Remove Student",
                        "This student has borrowing records. "
                        "The student cannot be deleted because "
                        "those records must be preserved."
                    )
                    return

                db.execute(
                    "DELETE FROM students WHERE student_id = ?",
                    (student_id,)
                )

            if self.editing_student_id == student_id:
                self.clear_form()

            self.load_students()

            messagebox.showinfo(
                "Success",
                f"Student '{student_name}' was removed."
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not remove the student:\n{error}"
            )

    def load_students(self):
        # Clear the table
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_text = self.search_var.get().strip()

        try:
            with connect_db() as db:
                students = db.execute(
                    """
                    SELECT student_id, admission_no, name, class_name
                    FROM students
                    WHERE admission_no LIKE ?
                       OR name LIKE ?
                       OR class_name LIKE ?
                    ORDER BY name COLLATE NOCASE
                    """,
                    (
                        f"%{search_text}%",
                        f"%{search_text}%",
                        f"%{search_text}%"
                    )
                ).fetchall()

            for student in students:
                self.tree.insert("", "end", values=student)

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load students:\n{error}"
            )

    def clear_form(self):
        self.admission_var.set("")
        self.name_var.set("")
        self.class_var.set("")
        self.editing_student_id = None
        self.save_button.config(text="Add Student")

    def clear_search(self):
        self.search_var.set("")
        self.load_students()


if __name__ == "__main__":
    root = tk.Tk()
    app = StudentManager(root)
    root.mainloop()
