import customtkinter as ctk
from theme import AppTheme
from gui.color_wheel import ColorWheel


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, settings: dict, on_settings_change):
        super().__init__(master, fg_color="transparent")
        self.settings = settings
        self.on_settings_change = on_settings_change
        self.theme = AppTheme.instance()

        appearance_card = ctk.CTkFrame(self, corner_radius=14)
        appearance_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(appearance_card, text="Vzhled", font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=18, pady=(16, 10)
        )
        mode_row = ctk.CTkFrame(appearance_card, fg_color="transparent")
        mode_row.pack(fill="x", padx=18, pady=(0, 18))
        ctk.CTkLabel(mode_row, text="Tmavý režim").pack(side="left")
        self.mode_switch = ctk.CTkSwitch(mode_row, text="", command=self._on_mode_toggle)
        self.mode_switch.pack(side="right")
        if self.settings.get("appearance_mode", "dark") == "dark":
            self.mode_switch.select()

        color_card = ctk.CTkFrame(self, corner_radius=14)
        color_card.pack(fill="x")
        ctk.CTkLabel(color_card, text="Barva zvýraznění", font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=18, pady=(16, 4)
        )
        ctk.CTkLabel(
            color_card,
            text="Vyber si vlastní odstín – projeví se ve všech tlačítkách a přepínačích v appce.",
            text_color=("gray40", "gray60"), wraplength=340, justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        body = ctk.CTkFrame(color_card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 20))

        self.preview = ctk.CTkFrame(body, width=44, height=44, corner_radius=10, fg_color=self.theme.accent)
        self.preview.pack(side="left", padx=(0, 24))
        self.preview.pack_propagate(False)

        is_dark = self.settings.get("appearance_mode", "dark") == "dark"
        wheel_bg = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1 if is_dark else 0]

        self.wheel = ColorWheel(
            body, initial_hex=self.theme.accent, wheel_bg=wheel_bg,
            on_change=self._on_color_change, on_commit=self._on_color_commit,
        )
        self.wheel.pack(side="left")

    def _on_mode_toggle(self):
        mode = "dark" if self.mode_switch.get() else "light"
        ctk.set_appearance_mode(mode)
        self.settings["appearance_mode"] = mode
        self.on_settings_change(self.settings)

    def _on_color_change(self, hex_color: str):
        self.preview.configure(fg_color=hex_color)

    def _on_color_commit(self, hex_color: str):
        self.settings["accent_color"] = hex_color
        self.on_settings_change(self.settings)
        self.theme.set_accent(hex_color)
        self.winfo_toplevel().rebuild(initial_page="settings")
