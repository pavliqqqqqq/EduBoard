import customtkinter as ctk
from theme import AppTheme

DEFAULT_NAV_ITEMS = [
    ("home", "🏠", "Domů"),
    ("schedule", "📅", "Rozvrh"),
    ("grades", "📖", "Žákovská knížka"),
]

EXPANDED_WIDTH = 216
COLLAPSED_WIDTH = 64
ANIMATION_STEPS = 8
ANIMATION_DELAY_MS = 8

# Tlačítka mají v klidu vlastní (byť jemné) pozadí - transparentní tlačítko
# splývá s panelem, dokud na něj uživatel nenajede myší.
BTN_IDLE = ("gray80", "gray24")
BTN_HOVER = ("gray68", "gray32")
TEXT_COLOR = ("gray10", "gray92")


class Sidebar(ctk.CTkFrame):
    """Postranní navigace. Lze sbalit na úzký pruh s ikonami a zase vysunout."""

    def __init__(self, master, user_name: str, user_role: str, expanded: bool,
                 on_navigate, on_logout, nav_items=None, initial_key: str = "home"):
        super().__init__(master, width=EXPANDED_WIDTH if expanded else COLLAPSED_WIDTH, corner_radius=0)
        self.grid_propagate(False)
        self.on_navigate = on_navigate
        self.expanded = expanded
        self._current_key = initial_key
        self._nav_buttons = {}
        self.nav_items = nav_items or DEFAULT_NAV_ITEMS

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # prázdný prostor mezi navigací a patičkou

        self.toggle_btn = ctk.CTkButton(
            self, text="☰", width=36, height=36, corner_radius=8,
            fg_color=BTN_IDLE, hover_color=BTN_HOVER, text_color=TEXT_COLOR,
            command=self._toggle,
        )
        self.toggle_btn.grid(row=0, column=0, padx=12, pady=(16, 4), sticky="w")

        self.brand_label = ctk.CTkLabel(
            self, text="EduBoard", font=ctk.CTkFont(size=17, weight="bold"), text_color=TEXT_COLOR
        )
        self.brand_label.grid(row=1, column=0, padx=16, pady=(4, 18), sticky="w")

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="new", padx=8)
        nav_frame.grid_columnconfigure(0, weight=1)
        for i, (key, icon, label) in enumerate(self.nav_items):
            btn = ctk.CTkButton(
                nav_frame, text=f"{icon}   {label}", anchor="w", corner_radius=8, height=38,
                fg_color=BTN_IDLE, hover_color=BTN_HOVER, text_color=TEXT_COLOR,
                command=lambda k=key: self._select(k),
            )
            btn.grid(row=i, column=0, sticky="ew", pady=3)
            self._nav_buttons[key] = (btn, icon, label)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="sew", padx=8, pady=14)
        bottom.grid_columnconfigure(0, weight=1)
        self.bottom = bottom

        self.user_label = ctk.CTkLabel(
            bottom, text=f"{user_name}\n{user_role}", justify="left", anchor="w",
            font=ctk.CTkFont(size=12), text_color=("gray25", "gray75"),
        )
        self.user_label.grid(row=0, column=0, sticky="w", padx=4, pady=(0, 8))

        self.logout_btn = ctk.CTkButton(
            bottom, text="⏻   Odhlásit se", anchor="w", corner_radius=8,
            fg_color=BTN_IDLE, hover_color=BTN_HOVER, text_color=TEXT_COLOR,
            command=on_logout,
        )
        self.logout_btn.grid(row=1, column=0, sticky="ew")

        self._select(initial_key, silent=True)
        self._apply_expanded_state(animate=False)

    def _select(self, key: str, silent: bool = False):
        accent = AppTheme.instance().accent
        for k, (btn, _icon, _label) in self._nav_buttons.items():
            active = k == key
            btn.configure(
                fg_color=accent if active else BTN_IDLE,
                text_color="white" if active else TEXT_COLOR,
            )
        self._current_key = key
        if not silent:
            self.on_navigate(key)

    def _toggle(self):
        self.expanded = not self.expanded
        self._apply_expanded_state(animate=True)

    def _apply_expanded_state(self, animate: bool):
        target = EXPANDED_WIDTH if self.expanded else COLLAPSED_WIDTH

        if self.expanded:
            self.brand_label.grid()
            self.user_label.grid()
            for key, (btn, icon, label) in self._nav_buttons.items():
                btn.configure(text=f"{icon}   {label}", anchor="w")
            self.logout_btn.configure(text="⏻   Odhlásit se", anchor="w")
        else:
            self.brand_label.grid_remove()
            self.user_label.grid_remove()
            for key, (btn, icon, label) in self._nav_buttons.items():
                btn.configure(text=icon, anchor="center")
            self.logout_btn.configure(text="⏻", anchor="center")

        if animate:
            self._animate_width(target)
        else:
            self.configure(width=target)

    def _animate_width(self, target: int):
        current = self.winfo_width()
        if current <= 1:
            current = COLLAPSED_WIDTH if self.expanded else EXPANDED_WIDTH
        delta = (target - current) / ANIMATION_STEPS

        def step(i=0, w=float(current)):
            if i >= ANIMATION_STEPS:
                self.configure(width=target)
                return
            w += delta
            self.configure(width=int(w))
            self.after(ANIMATION_DELAY_MS, lambda: step(i + 1, w))

        step()
