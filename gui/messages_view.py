import customtkinter as ctk
from api_client import BaseAPIClient, MockAPIClient
from models import User, Role


class MessagesView(ctk.CTkFrame):
    """
    Konverzace žák <-> jeho učitel. Přes MockAPIClient (lokální demo) se text
    posílá v čitelné podobě, protože nikam po síti neputuje. Přes
    SupabaseAPIClient se obsah šifruje/dešifruje v crypto.py - server tedy
    vidí jen ciphertext, viz poznámka pod polem pro psaní.
    """

    def __init__(self, master, api: BaseAPIClient, user: User):
        super().__init__(master, fg_color="transparent")
        self.api = api
        self.user = user
        self.thread_student_id = None
        self._students_by_name = {}
        self._build()

    def _build(self):
        if self.user.role == Role.STUDENT:
            self._build_student_header()
        else:
            self._build_teacher_header()
        self._build_thread_area()
        self._reload_messages()

    def _build_student_header(self):
        self.thread_student_id = self.user.id
        teacher = self.api.get_teacher(self.user.class_id)
        text = f"Konverzace s: {teacher.name}" if teacher else "Třídě zatím není přiřazený učitel."
        ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 10))

    def _build_teacher_header(self):
        students = self.api.get_students(self.user.class_id)
        self._students_by_name = {s.name: s for s in students}
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(top, text="Konverzace s žákem:").pack(side="left", padx=(0, 8))
        names = list(self._students_by_name)
        self.student_menu = ctk.CTkOptionMenu(top, values=names or ["–"], command=self._on_student_change)
        self.student_menu.pack(side="left")
        if names:
            self.student_menu.set(names[0])
            self.thread_student_id = self._students_by_name[names[0]].id

    def _on_student_change(self, name: str):
        self.thread_student_id = self._students_by_name[name].id
        self._reload_messages()

    def _build_thread_area(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=("gray95", "gray15"), corner_radius=12)
        self.scroll.pack(fill="both", expand=True, pady=(0, 10))
        self.scroll.grid_columnconfigure(0, weight=1)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x")
        self.entry = ctk.CTkEntry(bottom, placeholder_text="Napiš zprávu…")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self._send())
        ctk.CTkButton(bottom, text="Odeslat", width=90, command=self._send).pack(side="left")

        if not isinstance(self.api, MockAPIClient):
            ctk.CTkLabel(
                self, text="🔒  Zprávy se šifrují ještě před odesláním na server.",
                text_color=("gray40", "gray60"), font=ctk.CTkFont(size=11),
            ).pack(anchor="w", pady=(6, 0))

    def _reload_messages(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not self.thread_student_id:
            ctk.CTkLabel(self.scroll, text="Vyber žáka pro zahájení konverzace.",
                         text_color=("gray40", "gray60")).grid(row=0, column=0, pady=20)
            return

        messages = self.api.get_messages(self.thread_student_id)
        if not messages:
            ctk.CTkLabel(self.scroll, text="Zatím žádné zprávy - napiš tu první.",
                         text_color=("gray40", "gray60")).grid(row=0, column=0, pady=20)
            return

        for r, m in enumerate(messages):
            mine = m.sender_id == self.user.id
            bubble = ctk.CTkFrame(
                self.scroll, corner_radius=12,
                fg_color=("#3f8ce0", "#1f5fa8") if mine else ("gray85", "gray25"),
            )
            bubble.grid(row=r, column=0, sticky="e" if mine else "w", padx=8, pady=4, ipadx=2)
            text_color = ("gray98", "gray98") if mine else ("gray10", "gray92")
            meta_color = ("gray90", "gray80") if mine else ("gray40", "gray60")
            ctk.CTkLabel(
                bubble, text=m.content, wraplength=340, justify="left", text_color=text_color,
            ).pack(anchor="w", padx=12, pady=(8, 2))
            ctk.CTkLabel(
                bubble, text=f"{m.sender_name} · {m.created_at}", font=ctk.CTkFont(size=10),
                text_color=meta_color,
            ).pack(anchor="w", padx=12, pady=(0, 6))

        self.after(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        try:
            self.scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass  # nekritická kosmetika, appka funguje i bez auto-scrollu

    def _send(self):
        content = self.entry.get().strip()
        if not content or not self.thread_student_id:
            return
        self.api.send_message(self.thread_student_id, self.user, content)
        self.entry.delete(0, "end")
        self._reload_messages()
