import customtkinter as ctk
from api_client import BaseAPIClient
from models import User, Role

ADD_SUBJECT_OPTION = "+ Přidat předmět…"
ALL_SUBJECTS_OPTION = "Všechny předměty"


def _weighted_avg(grades) -> float:
    total_w = sum(g.weight for g in grades)
    if not total_w:
        return 0.0
    return round(sum(g.value * g.weight for g in grades) / total_w, 2)


class GradesView(ctk.CTkFrame):
    def __init__(self, master, api: BaseAPIClient, user: User):
        super().__init__(master, fg_color="transparent")
        self.api = api
        self.user = user
        self.selected_student: User | None = None
        self.current_filter = ALL_SUBJECTS_OPTION
        self._all_grades = []

        if user.role == Role.STUDENT:
            self._build_student_view(user.id)
        else:
            self._build_teacher_view()

    # ------------------------------------------------------------------
    # Žák: vlastní známky + filtr předmětu
    # ------------------------------------------------------------------
    def _build_student_view(self, student_id: str):
        self.student_id = student_id

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(top, text="Filtr předmětu:").pack(side="left", padx=(0, 5))
        self.filter_menu = ctk.CTkOptionMenu(
            top, values=[ALL_SUBJECTS_OPTION], command=self._on_filter_changed
        )
        self.filter_menu.pack(side="left")

        self.table_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True)

        self.avg_label = ctk.CTkLabel(self, text="", font=("Arial", 16, "bold"))
        self.avg_label.pack(pady=15)

        self._reload_student_grades()

    def _reload_student_grades(self):
        grades, server_avg = self.api.get_grades(self.student_id)
        self._all_grades = grades
        self._server_avg = server_avg
        subjects = sorted({g.subject for g in grades})
        self.filter_menu.configure(values=[ALL_SUBJECTS_OPTION] + subjects)
        if self.current_filter not in ([ALL_SUBJECTS_OPTION] + subjects):
            self.current_filter = ALL_SUBJECTS_OPTION
        self.filter_menu.set(self.current_filter)
        self._render_student_filtered()

    def _on_filter_changed(self, value):
        self.current_filter = value
        self._render_student_filtered()

    def _render_student_filtered(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
        grades = self._all_grades
        if self.current_filter == ALL_SUBJECTS_OPTION:
            avg = self._server_avg
        else:
            grades = [g for g in grades if g.subject == self.current_filter]
            avg = _weighted_avg(grades)
        self._render_grades_table(self.table_frame, grades, row_start=0)
        self.avg_label.configure(text=f"Vážený průměr: {avg}")

    # ------------------------------------------------------------------
    # Učitel: výběr žáka, zápis známky (předmět ze seznamu), filtr
    # ------------------------------------------------------------------
    def _build_teacher_view(self):
        self.class_id = self.user.class_id
        students = self.api.get_students(self.class_id)
        names = [s.name for s in students]
        self._students_by_name = {s.name: s for s in students}

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=10)

        self.student_menu = ctk.CTkOptionMenu(top, values=names or ["–"], command=self._on_student_selected)
        self.student_menu.pack(side="left", padx=5)
        if names:
            self.student_menu.set(names[0])

        self.subjects = self.api.get_subjects(self.class_id)
        self.subject_menu = ctk.CTkOptionMenu(
            top, values=(self.subjects or ["Žádný předmět"]) + [ADD_SUBJECT_OPTION],
            command=self._on_subject_menu_changed, width=170,
        )
        self.subject_menu.pack(side="left", padx=5)
        if self.subjects:
            self.subject_menu.set(self.subjects[0])

        self.value_menu = ctk.CTkOptionMenu(top, values=["1", "2", "3", "4", "5"], width=55)
        self.value_menu.pack(side="left", padx=5)

        self.weight_entry = ctk.CTkEntry(top, placeholder_text="Váha", width=55)
        self.weight_entry.pack(side="left", padx=5)

        self.note_entry = ctk.CTkEntry(top, placeholder_text="Poznámka", width=130)
        self.note_entry.pack(side="left", padx=5)

        ctk.CTkButton(top, text="Zapsat známku", command=self._add_grade).pack(side="left", padx=5)

        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(filter_bar, text="Filtr předmětu:").pack(side="left", padx=(0, 5))
        self.filter_menu = ctk.CTkOptionMenu(
            filter_bar, values=[ALL_SUBJECTS_OPTION], command=self._on_filter_changed
        )
        self.filter_menu.pack(side="left")

        self.table_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, pady=10)

        self.avg_label = ctk.CTkLabel(self, text="", font=("Arial", 14, "bold"))
        self.avg_label.pack(pady=(0, 10))

        if names:
            self._on_student_selected(names[0])

    def _on_subject_menu_changed(self, value):
        if value == ADD_SUBJECT_OPTION:
            self._prompt_new_subject()

    def _prompt_new_subject(self):
        dialog = ctk.CTkInputDialog(text="Název nového předmětu:", title="Přidat předmět")
        name = (dialog.get_input() or "").strip()
        if not name:
            self.subject_menu.set(self.subjects[0] if self.subjects else "Žádný předmět")
            return
        if name not in self.subjects:
            self.api.add_subject(self.class_id, name)
            self.subjects = self.api.get_subjects(self.class_id)
        self.subject_menu.configure(values=self.subjects + [ADD_SUBJECT_OPTION])
        self.subject_menu.set(name)

    def _on_student_selected(self, name: str):
        self.selected_student = self._students_by_name[name]
        self.current_filter = ALL_SUBJECTS_OPTION
        self._reload_teacher_grades()

    def _reload_teacher_grades(self):
        grades, server_avg = self.api.get_grades(self.selected_student.id)
        self._all_grades = grades
        self._server_avg = server_avg
        subjects = sorted({g.subject for g in grades})
        self.filter_menu.configure(values=[ALL_SUBJECTS_OPTION] + subjects)
        if self.current_filter not in ([ALL_SUBJECTS_OPTION] + subjects):
            self.current_filter = ALL_SUBJECTS_OPTION
        self.filter_menu.set(self.current_filter)
        self._render_teacher_filtered()

    def _on_filter_changed(self, value):
        self.current_filter = value
        self._render_teacher_filtered()

    def _render_teacher_filtered(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
        grades = self._all_grades
        if self.current_filter == ALL_SUBJECTS_OPTION:
            avg = self._server_avg
        else:
            grades = [g for g in grades if g.subject == self.current_filter]
            avg = _weighted_avg(grades)
        self._render_grades_table(self.table_frame, grades, row_start=0)
        self.avg_label.configure(text=f"Vážený průměr: {avg}")

    def _add_grade(self):
        if not self.selected_student:
            return
        subject = self.subject_menu.get()
        if subject in (ADD_SUBJECT_OPTION, "Žádný předmět", ""):
            return
        weight = self.weight_entry.get().strip() or "1"
        if not weight.isdigit():
            return
        self.api.add_grade(
            self.selected_student.id,
            subject,
            int(self.value_menu.get()),
            int(weight),
            self.note_entry.get().strip(),
        )
        self.note_entry.delete(0, "end")
        self._reload_teacher_grades()

    # ------------------------------------------------------------------
    # Sdílené vykreslení tabulky (vždy jen přes grid v samostatném frame)
    # ------------------------------------------------------------------
    def _render_grades_table(self, parent, grades, row_start: int):
        if not grades:
            ctk.CTkLabel(parent, text="Žádné známky v tomto výběru.").grid(
                row=row_start, column=0, columnspan=4, pady=10
            )
            return
        headers = ["Předmět", "Známka", "Váha", "Poznámka"]
        for c, h in enumerate(headers):
            ctk.CTkLabel(parent, text=h, font=("Arial", 12, "bold")).grid(row=row_start, column=c, padx=8, pady=4)
        for r, g in enumerate(grades, start=row_start + 1):
            ctk.CTkLabel(parent, text=g.subject).grid(row=r, column=0, padx=8, pady=2)
            ctk.CTkLabel(parent, text=str(g.value)).grid(row=r, column=1, padx=8, pady=2)
            ctk.CTkLabel(parent, text=str(g.weight)).grid(row=r, column=2, padx=8, pady=2)
            ctk.CTkLabel(parent, text=g.note).grid(row=r, column=3, padx=8, pady=2)
