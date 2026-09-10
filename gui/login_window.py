import customtkinter as ctk
from api_client import BaseAPIClient
from auth import SessionManager


class LoginWindow(ctk.CTk):
    def __init__(self, api: BaseAPIClient):
        super().__init__()
        self.api = api
        self.title("EduBoard – přihlášení")
        self.geometry("380x300")
        self.resizable(False, False)

        ctk.CTkLabel(self, text="EduBoard", font=("Arial", 24, "bold")).pack(pady=(30, 10))

        self.email_entry = ctk.CTkEntry(self, placeholder_text="E-mail", width=260)
        self.email_entry.pack(pady=8)
        self.email_entry.insert(0, "student@skola.cz")

        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Heslo", show="•", width=260)
        self.pass_entry.pack(pady=8)
        self.pass_entry.insert(0, "heslo123")

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack(pady=4)

        ctk.CTkButton(self, text="Přihlásit se", width=260, command=self._login).pack(pady=12)

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