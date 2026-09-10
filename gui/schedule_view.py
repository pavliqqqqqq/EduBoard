import customtkinter as ctk
from api_client import BaseAPIClient
from models import User, Role

DAYS = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek"]
PERIODS = range(1, 6)
ADD_SUBJECT_OPTION = "+ Přidat předmět…"


class ScheduleView(ctk.CTkFrame):
    def __init__(self, master, api: BaseAPIClient, user: User):
        super().__init__(master, fg_color="transparent")
        self.api = api
        self.user = user
        self.editable = user.role == Role.TEACHER
        self._build()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        if self.editable:
            ctk.CTkLabel(
                self, text="Klikni na hodinu a uprav ji.", text_color=("gray30", "gray70")
            ).grid(row=0, column=0, columnspan=len(DAYS) + 1, sticky="w", padx=5, pady=(0, 8))
            header_row = 1
        else:
            header_row = 0

        items = self.api.get_schedule(self.user.class_id)
        by_slot = {(i.day, i.period): i for i in items}

        for col, day in enumerate(DAYS):
            ctk.CTkLabel(self, text=day, font=("Arial", 13, "bold")).grid(
                row=header_row, column=col + 1, padx=5, pady=5
            )

        for row, period in enumerate(PERIODS, start=header_row + 1):
            ctk.CTkLabel(self, text=f"{period}.").grid(row=row, column=0, padx=5, pady=5)
            for col, _ in enumerate(DAYS):
                item = by_slot.get((col, period))
                text = f"{item.subject}\n{item.room}" if item else "–"
                cell = ctk.CTkLabel(
                    self, text=text, fg_color=("gray85", "gray20"), corner_radius=6,
                    width=120, height=50, cursor="hand2" if self.editable else "arrow",
                )
                cell.grid(row=row, column=col + 1, padx=5, pady=5, sticky="nsew")
                if self.editable:
                    cell.bind("<Button-1>", lambda e, d=col, p=period, it=item: self._open_editor(d, p, it))

    def _open_editor(self, day: int, period: int, item):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"{DAYS[day]}, {period}. hodina")
        dialog.geometry("320x300")
        dialog.grab_set()
        dialog.resizable(False, False)

        subjects = self.api.get_subjects(self.user.class_id)

        ctk.CTkLabel(dialog, text="Předmět:").pack(pady=(15, 2))
        subject_menu = ctk.CTkOptionMenu(dialog, values=(subjects or ["Žádný předmět"]) + [ADD_SUBJECT_OPTION])
        subject_menu.pack()
        if item:
            subject_menu.set(item.subject)
        elif subjects:
            subject_menu.set(subjects[0])

        def on_subject_change(value):
            if value != ADD_SUBJECT_OPTION:
                return
            input_dialog = ctk.CTkInputDialog(text="Název nového předmětu:", title="Přidat předmět")
            name = (input_dialog.get_input() or "").strip()
            if name:
                if name not in subjects:
                    self.api.add_subject(self.user.class_id, name)
                    subjects.append(name)
                subject_menu.configure(values=subjects + [ADD_SUBJECT_OPTION])
                subject_menu.set(name)
            else:
                subject_menu.set(subjects[0] if subjects else "Žádný předmět")

        subject_menu.configure(command=on_subject_change)

        ctk.CTkLabel(dialog, text="Místnost:").pack(pady=(10, 2))
        room_entry = ctk.CTkEntry(dialog)
        room_entry.pack()
        if item:
            room_entry.insert(0, item.room)

        ctk.CTkLabel(dialog, text="Vyučující:").pack(pady=(10, 2))
        teacher_entry = ctk.CTkEntry(dialog)
        teacher_entry.pack()
        teacher_entry.insert(0, item.teacher if item else self.user.name)

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(pady=18)

        def save():
            subject = subject_menu.get()
            if subject in (ADD_SUBJECT_OPTION, "Žádný předmět", ""):
                return
            self.api.set_schedule_item(
                self.user.class_id, day, period, subject,
                room_entry.get().strip(), teacher_entry.get().strip(),
            )
            dialog.destroy()
            self._build()

        def delete():
            self.api.delete_schedule_item(self.user.class_id, day, period)
            dialog.destroy()
            self._build()

        ctk.CTkButton(btns, text="Uložit", command=save).pack(side="left", padx=5)
        if item:
            ctk.CTkButton(
                btns, text="Smazat", fg_color="firebrick3", hover_color="firebrick4", command=delete
            ).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Zrušit", fg_color="gray40", command=dialog.destroy).pack(side="left", padx=5)
