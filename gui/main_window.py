import customtkinter as ctk
from api_client import BaseAPIClient
from models import User
from gui.schedule_view import ScheduleView
from gui.grades_view import GradesView
from auth import SessionManager


class MainWindow(ctk.CTk):
    def __init__(self, api: BaseAPIClient, user: User):
        super().__init__()
        self.api = api
        self.user = user
        self.title(f"EduBoard – {user.name} ({user.role.value})")
        self.geometry("780x480")

        tabview = ctk.CTkTabview(self, width=760, height=430)
        tabview.pack(padx=10, pady=10, fill="both", expand=True)

        tab_schedule = tabview.add("Rozvrh")
        tab_grades = tabview.add("Žákovská knížka")

        ScheduleView(tab_schedule, api, user).pack(fill="both", expand=True, padx=10, pady=10)
        GradesView(tab_grades, api, user).pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkButton(self, text="Odhlásit se", command=self._logout).pack(pady=(0, 10))

    def _logout(self):
        SessionManager.instance().clear()
        from gui.login_window import LoginWindow
        self.destroy()
        LoginWindow(self.api).mainloop()