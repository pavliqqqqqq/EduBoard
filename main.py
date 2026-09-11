import customtkinter as ctk
from config import USE_MOCK_API, SUPABASE_URL, SUPABASE_ANON_KEY
from api_client import MockAPIClient, SupabaseAPIClient
from theme import AppTheme
import gui.login_window
import settings as settings_module


def build_api_client():
    if USE_MOCK_API:
        return MockAPIClient()
    return SupabaseAPIClient(SUPABASE_URL, SUPABASE_ANON_KEY)


if __name__ == "__main__":
    # Světlý/tmavý režim je uložený z minulého spuštění, ať appka
    # naskočí rovnou ve stylu, který si uživatel naposledy zvolil.
    saved_settings = settings_module.load_settings()
    ctk.set_appearance_mode(saved_settings.get("appearance_mode", "dark"))
    ctk.set_default_color_theme("blue")
    # set_default_color_theme načte čistý blue.json, teprve teď na něj
    # navrstvíme fialovou accent barvu + tmavé "surface" pozadí (theme.py)
    AppTheme.instance().set_accent(saved_settings.get("accent_color", AppTheme.instance().accent))
    gui.login_window.LoginWindow(build_api_client()).mainloop()