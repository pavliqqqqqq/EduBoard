import customtkinter as ctk
from api_client import BaseAPIClient
from models import User

DAYS = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek"]
PERIODS = range(1, 6)


class ScheduleView(ctk.CTkFrame):
    def __init__(self, master, api: BaseAPIClient, user: User):
        super().__init__(master, fg_color="transparent")
        self.api = api
        self.user = user
        self._build()

    def _build(self):
        items = self.api.get_schedule(self.user.class_id)
        by_slot = {(i.day, i.period): i for i in items}

        for col, day in enumerate(DAYS):
            ctk.CTkLabel(self, text=day, font=("Arial", 13, "bold")).grid(row=0, column=col + 1, padx=5, pady=5)

        for row, period in enumerate(PERIODS, start=1):
            ctk.CTkLabel(self, text=f"{period}.").grid(row=row, column=0, padx=5, pady=5)
            for col, _ in enumerate(DAYS):
                item = by_slot.get((col, period))
                text = f"{item.subject}\n{item.room}" if item else "–"
                ctk.CTkLabel(self, text=text, fg_color=("gray85", "gray20"), corner_radius=6,
                             width=120, height=50).grid(row=row, column=col + 1, padx=5, pady=5, sticky="nsew")