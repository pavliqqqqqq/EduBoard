import os
import sys
import subprocess
import customtkinter as ctk
from api_client import BaseAPIClient, generate_login
from models import User
import credentials_log


class StudentsView(ctk.CTkFrame):
    """Založení nového žákovského účtu učitelem + přehled dočasných hesel."""

    def __init__(self, master, api: BaseAPIClient, user: User):
        super().__init__(master, fg_color="transparent")
        self.api = api
        self.user = user
        self._build()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(top, text="+  Přidat žáka", command=self._open_add_dialog).pack(side="left")
        ctk.CTkButton(
            top, text="📄  Otevřít soubor s hesly", command=self._open_credentials_file,
            fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40"),
        ).pack(side="left", padx=8)

        ctk.CTkLabel(
            self,
            text=f"Nová hesla se ukládají do: {credentials_log.CREDENTIALS_PATH}",
            text_color=("gray40", "gray60"), wraplength=600, justify="left",
        ).pack(anchor="w", pady=(0, 16))

        list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        list_frame.pack(fill="both", expand=True)
        list_frame.grid_columnconfigure(0, weight=1)

        students = self.api.get_students(self.user.class_id)
        if not students:
            ctk.CTkLabel(list_frame, text="Zatím žádní žáci.", text_color=("gray40", "gray60")).grid(
                row=0, column=0, pady=20
            )
        for r, s in enumerate(students):
            row = ctk.CTkFrame(list_frame, corner_radius=10)
            row.grid(row=r, column=0, sticky="ew", pady=4)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=s.name, anchor="w", font=ctk.CTkFont(size=13)).grid(
                row=0, column=0, sticky="w", padx=14, pady=10
            )

    def _open_add_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Přidat žáka")
        dialog.geometry("320x320")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.after(150, dialog.lift)
        dialog.after(150, dialog.focus_force)
        dialog.after(200, dialog.grab_set)

        ctk.CTkLabel(dialog, text="Jméno:").pack(pady=(18, 2))
        first_entry = ctk.CTkEntry(dialog, width=220)
        first_entry.pack()

        ctk.CTkLabel(dialog, text="Příjmení:").pack(pady=(10, 2))
        last_entry = ctk.CTkEntry(dialog, width=220)
        last_entry.pack()

        preview_label = ctk.CTkLabel(dialog, text="", text_color=("gray40", "gray60"))
        preview_label.pack(pady=(10, 0))

        def update_preview(*_):
            login = generate_login(first_entry.get().strip(), last_entry.get().strip())
            preview_label.configure(text=f"Přihlašovací e-mail: {login}@skola.cz" if login else "")

        first_entry.bind("<KeyRelease>", update_preview)
        last_entry.bind("<KeyRelease>", update_preview)

        error_label = ctk.CTkLabel(dialog, text="", text_color="red", wraplength=260, justify="left")
        error_label.pack(pady=(8, 0))

        def create():
            first = first_entry.get().strip()
            last = last_entry.get().strip()
            if not first or not last:
                error_label.configure(text="Vyplň jméno i příjmení.")
                return
            try:
                new_user, email, password = self.api.add_student(first, last, self.user.class_id)
            except Exception as e:
                error_label.configure(text=str(e))
                return
            credentials_log.record_new_account(new_user.name, email, password)
            dialog.destroy()
            self._build()

        ctk.CTkButton(dialog, text="Vytvořit účet", command=create).pack(pady=20)

    def _open_credentials_file(self):
        path = credentials_log.CREDENTIALS_PATH
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Zatím nebyl vytvořen žádný nový účet.\n", encoding="utf-8")
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            elif sys.platform.startswith("win"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except OSError:
            pass  # appka funguje dál i když se soubor nepodaří otevřít v OS
