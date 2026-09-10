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
        self.geometry("880x620")
        self.minsize(720, 520)

        # Grid místo pack: tabview se roztahuje (weight=1), patička s tlačítkem
        # má vlastní pevný řádek a nezmizí, ani když je obsah dlouhý.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        tabview = ctk.CTkTabview(self)
        tabview.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        tab_schedule = tabview.add("Rozvrh")
        tab_grades = tabview.add("Žákovská knížka")

        ScheduleView(tab_schedule, api, user).pack(fill="both", expand=True, padx=10, pady=10)
        GradesView(tab_grades, api, user).pack(fill="both", expand=True, padx=10, pady=10)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(footer, text=f"Přihlášen(a): {user.name}").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(footer, text="Odhlásit se", command=self._logout).grid(row=0, column=1, sticky="e")

    def _logout(self):
        SessionManager.instance().clear()
        from gui.login_window import LoginWindow
        self.destroy()
        LoginWindow(self.api).mainloop()
