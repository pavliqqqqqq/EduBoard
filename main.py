import customtkinter as ctk
from config import USE_MOCK_API, SUPABASE_URL, SUPABASE_ANON_KEY
from api_client import MockAPIClient, SupabaseAPIClient
from gui.login_window import LoginWindow


def build_api_client():
    if USE_MOCK_API:
        return MockAPIClient()
    return SupabaseAPIClient(SUPABASE_URL, SUPABASE_ANON_KEY)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    LoginWindow(build_api_client()).mainloop()