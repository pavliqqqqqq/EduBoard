import json
from pathlib import Path
from theme import DEFAULT_ACCENT

# Nastavení se ukládá mimo repozitář (do domovské složky uživatele), takže
# přežije aktualizace appky a nekončí omylem v gitu.
SETTINGS_PATH = Path.home() / ".eduboard" / "settings.json"

DEFAULT_SETTINGS = {
    "appearance_mode": "dark",
    "accent_color": DEFAULT_ACCENT,
    "sidebar_expanded": True,
    "home_widgets": {
        "today_schedule": True,
        "grades_summary": True,
        "coming_soon": True,
    },
}


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return dict(DEFAULT_SETTINGS)
        merged = {**DEFAULT_SETTINGS, **data}
        merged["home_widgets"] = {**DEFAULT_SETTINGS["home_widgets"], **data.get("home_widgets", {})}
        return merged
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass  # ukládání nastavení není kritické, appka funguje i bez toho
