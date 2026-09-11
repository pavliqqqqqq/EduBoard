import customtkinter as ctk
from api_client import BaseAPIClient
from models import User, Role
from gui.sidebar import Sidebar
from gui.home_view import HomeView
from gui.schedule_view import ScheduleView
from gui.grades_view import GradesView
from gui.messages_view import MessagesView
from gui.students_view import StudentsView
from auth import SessionManager
import settings as settings_module


class MainWindow(ctk.CTk):
    def __init__(self, api: BaseAPIClient, user: User):
        super().__init__()
        self.api = api
        self.user = user
        self.settings = settings_module.load_settings()
        ctk.set_appearance_mode(self.settings.get("appearance_mode", "dark"))

        self.title(f"EduBoard – {user.name} ({user.role.value})")
        self.geometry("1040x680")
        self.minsize(800, 560)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        nav_items = [
            ("home", "🏠", "Domů"),
            ("schedule", "📅", "Rozvrh"),
            ("grades", "📖", "Žákovská knížka"),
            ("messages", "✉️", "Zprávy"),
        ]
        if user.role == Role.TEACHER:
            nav_items.append(("students", "👥", "Žáci"))

        self.sidebar = Sidebar(
            self,
            nav_items=nav_items,
            user_name=user.name,
            user_role="Učitel" if user.role == Role.TEACHER else "Žák",
            expanded=self.settings.get("sidebar_expanded", True),
            appearance_mode=self.settings.get("appearance_mode", "dark"),
            on_navigate=self._navigate,
            on_toggle_theme=self._on_theme_changed,
            on_logout=self._logout,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=28, pady=28)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        self.pages = {
            "home": HomeView(content, api, user, self.settings, self._on_settings_changed),
            "schedule": self._build_page(content, "📅  Rozvrh", ScheduleView),
            "grades": self._build_page(content, "📖  Žákovská knížka", GradesView),
            "messages": self._build_page(content, "✉️  Zprávy", MessagesView),
        }
        if user.role == Role.TEACHER:
            self.pages["students"] = self._build_page(content, "👥  Žáci", StudentsView)

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self._navigate("home")

    def _build_page(self, content, title: str, view_cls) -> ctk.CTkFrame:
        page = ctk.CTkFrame(content, fg_color="transparent")
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(page, text=title, font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 16)
        )
        view_cls(page, self.api, self.user).grid(row=1, column=0, sticky="nsew")
        return page

    def _navigate(self, key: str):
        page = self.pages.get(key)
        if page is None:
            return
        page.tkraise()
        if key == "home":
            self.pages["home"].refresh()

    def _on_theme_changed(self, mode: str):
        self.settings["appearance_mode"] = mode
        settings_module.save_settings(self.settings)

    def _on_settings_changed(self, settings: dict):
        settings_module.save_settings(settings)

    def _logout(self):
        self.settings["sidebar_expanded"] = self.sidebar.expanded
        settings_module.save_settings(self.settings)
        SessionManager.instance().clear()
        from gui.login_window import LoginWindow
        self.destroy()
        LoginWindow(self.api).mainloop()
