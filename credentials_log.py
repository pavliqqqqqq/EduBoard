"""
Dočasný textový soubor s přihlašovacími údaji účtů, které učitel v appce
nově vytvořil. Slouží k jednorázovému předání hesla žákovi - po prvním
přihlášení by si ho měl změnit a tenhle soubor je dobré smazat.
"""
from pathlib import Path
from datetime import datetime

CREDENTIALS_PATH = Path.home() / ".eduboard" / "nove_ucty.txt"

_HEADER = (
    "Dočasný přehled nově vytvořených účtů EduBoard\n"
    "Po prvním přihlášení doporuč žákovi heslo změnit a tento soubor smaž.\n"
    + "=" * 60 + "\n\n"
)


def record_new_account(full_name: str, email: str, password: str) -> None:
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    is_new_file = not CREDENTIALS_PATH.exists()
    with CREDENTIALS_PATH.open("a", encoding="utf-8") as f:
        if is_new_file:
            f.write(_HEADER)
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        f.write(f"[{timestamp}] {full_name}\n    e-mail: {email}\n    heslo:  {password}\n\n")
