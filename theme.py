"""
Centrální správa vzhledu appky.

CustomTkinter čte výchozí barvy widgetů z `customtkinter.ThemeManager.theme`
(dict načtený z assets/themes/*.json) v okamžiku, kdy se widget vytváří.
Proto při změně accent barvy nejdřív přepíšeme tenhle dict a pak se celé
okno musí znovu vytvořit (viz MainWindow.rebuild) - už vytvořené widgety
mají svou barvu "zamčenou" z doby svého vzniku a samy se nepřebarví.
"""
import customtkinter as ctk

DEFAULT_ACCENT = "#8B5CF6"

# Tmavší/světlejší varianta pozadí a karet, laděná do fialova podle reference.
_SURFACES = {
    "CTk": {"fg_color": ["#f5f3fb", "#111116"]},
    "CTkToplevel": {"fg_color": ["#f5f3fb", "#111116"]},
    "CTkFrame": {
        "fg_color": ["#ffffff", "#1a1a22"],
        "top_fg_color": ["#efeaf9", "#211f2b"],
        "border_color": ["#ded6f5", "#2c2a38"],
    },
}

# Widgety, jejichž hlavní/hover barva se řídí vybranou accent barvou.
_ACCENT_TARGETS = [
    ("CTkButton", "fg_color", "hover_color"),
    ("CTkCheckBox", "fg_color", "hover_color"),
    ("CTkRadioButton", "fg_color", "hover_color"),
    ("CTkSwitch", "progress_color", None),
    ("CTkProgressBar", "progress_color", None),
    ("CTkSlider", "button_color", "button_hover_color"),
    ("CTkOptionMenu", "fg_color", "button_color"),
    ("CTkSegmentedButton", "selected_color", "selected_hover_color"),
]


def shade(hex_color: str, factor: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


class AppTheme:
    _instance = None

    def __init__(self):
        self.accent = DEFAULT_ACCENT
        self._apply_surfaces()
        self._apply_accent()

    @classmethod
    def instance(cls) -> "AppTheme":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def hover(self) -> str:
        return shade(self.accent, 0.8)

    def set_accent(self, hex_color: str):
        self.accent = hex_color
        self._apply_accent()

    def _apply_surfaces(self):
        for widget, values in _SURFACES.items():
            ctk.ThemeManager.theme.setdefault(widget, {}).update(values)

    def _apply_accent(self):
        pair = [self.accent, self.accent]
        hover_pair = [self.hover(), self.hover()]
        for widget, main_key, hover_key in _ACCENT_TARGETS:
            entry = ctk.ThemeManager.theme.setdefault(widget, {})
            entry[main_key] = pair
            if hover_key:
                entry[hover_key] = hover_pair
