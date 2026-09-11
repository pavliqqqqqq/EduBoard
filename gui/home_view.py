import customtkinter as ctk
from datetime import datetime
from api_client import BaseAPIClient
from models import User, Role

WIDGET_LABELS = {
    "today_schedule": "Dnešní rozvrh",
    "grades_summary": "Přehled známek",
    "coming_soon": "Připravujeme",
}


class HomeView(ctk.CTkFrame):
    """Přehledová domovská stránka - obsah karet si uživatel zapíná/vypíná sám."""

    def __init__(self, master, api: BaseAPIClient, user: User, settings: dict, on_settings_change):
        super().__init__(master, fg_color="transparent")
        self.api = api
        self.user = user
        self.settings = settings
        self.on_settings_change = on_settings_change

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))
        first_name = self.user.name.split()[0] if self.user.name.split() else self.user.name
        ctk.CTkLabel(header, text=f"Vítej, {first_name}!", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="⚙  Upravit přehled", width=160, command=self._open_settings).pack(side="right")

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        for w in self.body.winfo_children():
            w.destroy()

        w_settings = self.settings.get("home_widgets", {})
        builders = []
        if w_settings.get("today_schedule", True):
            builders.append(self._render_today_schedule_card)
        if w_settings.get("grades_summary", True):
            builders.append(self._render_grades_card)
        if w_settings.get("coming_soon", True):
            builders.append(self._render_coming_soon_card)

        if not builders:
            ctk.CTkLabel(
                self.body, text="Žádné widgety nejsou zapnuté. Klikni na „Upravit přehled“.",
                text_color=("gray40", "gray60"),
            ).grid(row=0, column=0, pady=40)
            return

        for col in range(len(builders)):
            self.body.grid_columnconfigure(col, weight=1, uniform="cards")
        self.body.grid_rowconfigure(0, weight=1)

        for col, build in enumerate(builders):
            card = build(self.body)
            card.grid(row=0, column=col, sticky="nsew", padx=(0, 14) if col < len(builders) - 1 else 0)

    def _card(self, parent) -> ctk.CTkFrame:
        return ctk.CTkFrame(parent, corner_radius=14)

    def _card_title(self, card, text):
        ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=18, pady=(16, 10))

    def _render_today_schedule_card(self, parent):
        card = self._card(parent)
        self._card_title(card, "📅  Dnešní rozvrh")

        weekday = datetime.now().weekday()
        if weekday > 4:
            ctk.CTkLabel(card, text="Dnes je víkend – žádná výuka.", text_color=("gray40", "gray60")).pack(
                anchor="w", padx=18, pady=(0, 16)
            )
            return card

        items = sorted(
            (i for i in self.api.get_schedule(self.user.class_id) if i.day == weekday),
            key=lambda i: i.period,
        )
        if not items:
            ctk.CTkLabel(card, text="Dnes nemáš žádné hodiny.", text_color=("gray40", "gray60")).pack(
                anchor="w", padx=18, pady=(0, 16)
            )
            return card

        for it in items:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=3)
            ctk.CTkLabel(row, text=f"{it.period}.", width=22, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(row, text=it.subject, anchor="w").pack(side="left", padx=(6, 0))
            ctk.CTkLabel(row, text=it.room, text_color=("gray40", "gray60")).pack(side="right")
        ctk.CTkFrame(card, height=14, fg_color="transparent").pack()
        return card

    def _render_grades_card(self, parent):
        card = self._card(parent)
        self._card_title(card, "📖  Přehled známek")

        if self.user.role == Role.STUDENT:
            grades, avg = self.api.get_grades(self.user.id)
            ctk.CTkLabel(card, text=f"Vážený průměr: {avg}", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=18)
            recent = list(reversed(grades[-3:]))
            if not recent:
                ctk.CTkLabel(card, text="Zatím žádné známky.", text_color=("gray40", "gray60")).pack(
                    anchor="w", padx=18, pady=(8, 16)
                )
            else:
                ctk.CTkLabel(card, text="Poslední známky:", text_color=("gray40", "gray60")).pack(
                    anchor="w", padx=18, pady=(10, 2)
                )
                for g in recent:
                    ctk.CTkLabel(card, text=f"{g.subject} — {g.value}").pack(anchor="w", padx=18)
                ctk.CTkFrame(card, height=10, fg_color="transparent").pack()
        else:
            students = self.api.get_students(self.user.class_id)
            ctk.CTkLabel(card, text=f"Počet žáků ve třídě: {len(students)}").pack(anchor="w", padx=18, pady=(0, 4))
            ctk.CTkLabel(
                card, text="Přehled a zápis známek najdeš v sekci „Žákovská knížka“.",
                text_color=("gray40", "gray60"), wraplength=220, justify="left",
            ).pack(anchor="w", padx=18, pady=(0, 16))
        return card

    def _render_coming_soon_card(self, parent):
        card = self._card(parent)
        self._card_title(card, "🚧  Připravujeme")
        for feature in ("Docházka", "Zprávy pro rodiče a učitele", "Statistiky prospěchu"):
            ctk.CTkLabel(card, text=f"•  {feature}", text_color=("gray40", "gray60")).pack(anchor="w", padx=18, pady=1)
        ctk.CTkFrame(card, height=14, fg_color="transparent").pack()
        return card

    def _open_settings(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Upravit přehled")
        dialog.geometry("300x260")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        # zpoždění grab_set kvůli macOS - viz oprava v schedule_view.py
        dialog.after(150, dialog.lift)
        dialog.after(150, dialog.focus_force)
        dialog.after(200, dialog.grab_set)

        ctk.CTkLabel(
            dialog, text="Co se má zobrazovat na domovské stránce:", wraplength=260, justify="left"
        ).pack(padx=18, pady=(18, 10), anchor="w")

        w_settings = self.settings.setdefault("home_widgets", {})
        vars_ = {}
        for key, label in WIDGET_LABELS.items():
            var = ctk.BooleanVar(value=w_settings.get(key, True))
            ctk.CTkCheckBox(dialog, text=label, variable=var).pack(anchor="w", padx=22, pady=5)
            vars_[key] = var

        def apply_and_close():
            for key, var in vars_.items():
                w_settings[key] = bool(var.get())
            self.on_settings_change(self.settings)
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="Uložit", command=apply_and_close).pack(pady=18)
