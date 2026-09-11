import customtkinter as ctk
from api_client import BaseAPIClient
from auth import SessionManager
from theme import AppTheme


class LoginWindow(ctk.CTk):
    def __init__(self, api: BaseAPIClient):
        super().__init__()
        self.api = api
        self.title("EduBoard – přihlášení")
        self.geometry("400x460")
        self.resizable(False, False)

        card = ctk.CTkFrame(self, corner_radius=18)
        card.pack(expand=True, fill="both", padx=30, pady=30)

        ctk.CTkLabel(
            card, text="EduBoard", font=("Arial", 26, "bold"), text_color=AppTheme.instance().accent
        ).pack(pady=(40, 26))

        self.email_entry = ctk.CTkEntry(card, placeholder_text="E-mail", width=280, height=38)
        self.email_entry.pack(pady=8)
        self.email_entry.insert(0, "psvoboda@skola.cz")

        self.pass_entry = ctk.CTkEntry(card, placeholder_text="Heslo", show="•", width=280, height=38)
        self.pass_entry.pack(pady=8)
        self.pass_entry.insert(0, "1234")

        self.error_label = ctk.CTkLabel(card, text="", text_color="#ff6b6b")
        self.error_label.pack(pady=4)

        ctk.CTkButton(card, text="Přihlásit se", width=280, height=40, command=self._login).pack(pady=20)

    def _login(self):
        try:
            user = self.api.login(self.email_entry.get().strip(), self.pass_entry.get())
        except Exception as e:
            self.error_label.configure(text=str(e))
            return

        SessionManager.instance().set_session(user)
        from gui.main_window import MainWindow
        self.destroy()
        MainWindow(self.api, user).mainloop()