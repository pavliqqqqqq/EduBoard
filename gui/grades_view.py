import customtkinter as ctk
from api_client import BaseAPIClient
from models import User, Role


class GradesView(ctk.CTkFrame):
    def __init__(self, master, api: BaseAPIClient, user: User):
        super().__init__(master, fg_color="transparent")
        self.api = api
        self.user = user
        self.selected_student: User | None = None

        if user.role == Role.STUDENT:
            self._build_student_view(user.id)
        else:
            self._build_teacher_view()

    def _build_student_view(self, student_id: str):
        grades, avg = self.api.get_grades(student_id)
        self._render_grades_table(self, grades, row_start=0)
        ctk.CTkLabel(self, text=f"Vážený průměr: {avg}", font=("Arial", 16, "bold")).pack(pady=15)

    def _build_teacher_view(self):
        students = self.api.get_students(self.user.class_id)
        names = [s.name for s in students]
        self._students_by_name = {s.name: s for s in students}

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=10)

        self.student_menu = ctk.CTkOptionMenu(top, values=names, command=self._on_student_selected)
        self.student_menu.pack(side="left", padx=5)
        if names:
            self.student_menu.set(names[0])

        self.subject_entry = ctk.CTkEntry(top, placeholder_text="Předmět", width=140)
        self.subject_entry.pack(side="left", padx=5)

        self.value_menu = ctk.CTkOptionMenu(top, values=["1", "2", "3", "4", "5"])
        self.value_menu.pack(side="left", padx=5)

        self.weight_entry = ctk.CTkEntry(top, placeholder_text="Váha", width=60)
        self.weight_entry.pack(side="left", padx=5)

        self.note_entry = ctk.CTkEntry(top, placeholder_text="Poznámka", width=140)
        self.note_entry.pack(side="left", padx=5)

        ctk.CTkButton(top, text="Zapsat známku", command=self._add_grade).pack(side="left", padx=5)

        self.table_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, pady=10)

        if names:
            self._on_student_selected(names[0])

    def _on_student_selected(self, name: str):
        self.selected_student = self._students_by_name[name]
        for w in self.table_frame.winfo_children():
            w.destroy()
        grades, avg = self.api.get_grades(self.selected_student.id)
        self._render_grades_table(self.table_frame, grades, row_start=0)
        ctk.CTkLabel(self.table_frame, text=f"Vážený průměr: {avg}",
                     font=("Arial", 14, "bold")).grid(row=len(grades) + 1, column=0, columnspan=4, pady=10)

    def _add_grade(self):
        if not self.selected_student:
            return
        weight = self.weight_entry.get().strip() or "1"
        if not weight.isdigit():
            return
        self.api.add_grade(
            self.selected_student.id,
            self.subject_entry.get().strip() or "Neuvedeno",
            int(self.value_menu.get()),
            int(weight),
            self.note_entry.get().strip(),
        )
        self._on_student_selected(self.selected_student.name)

    def _render_grades_table(self, parent, grades, row_start: int):
        headers = ["Předmět", "Známka", "Váha", "Poznámka"]
        for c, h in enumerate(headers):
            ctk.CTkLabel(parent, text=h, font=("Arial", 12, "bold")).grid(row=row_start, column=c, padx=8, pady=4)
        for r, g in enumerate(grades, start=row_start + 1):
            ctk.CTkLabel(parent, text=g.subject).grid(row=r, column=0, padx=8, pady=2)
            ctk.CTkLabel(parent, text=str(g.value)).grid(row=r, column=1, padx=8, pady=2)
            ctk.CTkLabel(parent, text=str(g.weight)).grid(row=r, column=2, padx=8, pady=2)
            ctk.CTkLabel(parent, text=g.note).grid(row=r, column=3, padx=8, pady=2)