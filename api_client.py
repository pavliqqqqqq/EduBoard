import unicodedata
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple
from models import User, Role, Grade, ScheduleItem, Message

DEFAULT_STUDENT_PASSWORD = "1234"


def _slugify(text: str) -> str:
    """'Šimon' -> 'simon' - odstraní diakritiku a nealfanumerické znaky."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return "".join(ch for ch in ascii_text.lower() if ch.isalnum())


def generate_login(first_name: str, last_name: str) -> str:
    """Petr Svoboda -> psvoboda (první písmeno jména + celé příjmení)."""
    first_letter = _slugify(first_name)[:1]
    return f"{first_letter}{_slugify(last_name)}"


class BaseAPIClient(ABC):
    @abstractmethod
    def login(self, email: str, password: str) -> User: ...

    @abstractmethod
    def get_grades(self, student_id: str) -> Tuple[List[Grade], float]: ...

    @abstractmethod
    def add_grade(self, student_id: str, subject: str, value: int, weight: int, note: str) -> None: ...

    @abstractmethod
    def get_schedule(self, class_id: str) -> List[ScheduleItem]: ...

    @abstractmethod
    def get_students(self, class_id: str) -> List[User]: ...

    @abstractmethod
    def add_student(self, first_name: str, last_name: str, class_id: str) -> Tuple[User, str, str]:
        """Vytvoří nový žákovský účet. Vrátí (User, e-mail, heslo)."""
        ...

    @abstractmethod
    def get_teacher(self, class_id: str) -> Optional[User]: ...

    @abstractmethod
    def get_subjects(self, class_id: str) -> List[str]: ...

    @abstractmethod
    def add_subject(self, class_id: str, name: str) -> None: ...

    @abstractmethod
    def set_schedule_item(self, class_id: str, day: int, period: int,
                           subject: str, room: str, teacher: str) -> None: ...

    @abstractmethod
    def delete_schedule_item(self, class_id: str, day: int, period: int) -> None: ...

    @abstractmethod
    def get_messages(self, student_id: str) -> List[Message]: ...

    @abstractmethod
    def send_message(self, student_id: str, sender: User, content: str) -> None: ...


class MockAPIClient(BaseAPIClient):
    """Simuluje chování backendu (Supabase RLS + RPC) lokálně pro vývoj/demo."""

    def __init__(self):
        self._users = {
            "ucitel@skola.cz": User("t1", "Mgr. Jana Nováková", Role.TEACHER, "3.B"),
            "psvoboda@skola.cz": User("s1", "Petr Svoboda", Role.STUDENT, "3.B"),
        }
        self._passwords = {"ucitel@skola.cz": "heslo123", "psvoboda@skola.cz": DEFAULT_STUDENT_PASSWORD}
        self._grades = {
            "s1": [
                Grade("g1", "Matematika", 1, 2, "Test"),
                Grade("g2", "Matematika", 2, 1, "Ústní"),
                Grade("g3", "Český jazyk", 3, 3, "Sloh"),
            ]
        }
        self._schedule = {
            "3.B": [
                ScheduleItem(0, 1, "Matematika", "12", "Nováková"),
                ScheduleItem(0, 2, "Český jazyk", "12", "Dvořák"),
                ScheduleItem(1, 1, "Fyzika", "F1", "Král"),
                ScheduleItem(2, 3, "Angličtina", "05", "Smith"),
                ScheduleItem(4, 2, "Tělocvik", "Hala", "Novák"),
            ]
        }
        self._subjects = {
            "3.B": ["Matematika", "Český jazyk", "Fyzika", "Angličtina", "Tělocvik"],
        }
        self._messages = {}  # student_id -> List[Message]
        self._next_student_num = 2

    def login(self, email, password):
        if email not in self._users or self._passwords[email] != password:
            raise ValueError("Neplatné přihlašovací údaje")
        return self._users[email]

    def get_grades(self, student_id):
        grades = self._grades.get(student_id, [])
        total_w = sum(g.weight for g in grades)
        avg = round(sum(g.value * g.weight for g in grades) / total_w, 2) if total_w else 0.0
        return grades, avg

    def add_grade(self, student_id, subject, value, weight, note):
        self._grades.setdefault(student_id, []).append(
            Grade(f"g{len(self._grades.get(student_id, [])) + 1}", subject, value, weight, note)
        )
        class_id = self._class_id_for_student(student_id)
        if class_id and subject not in self._subjects.setdefault(class_id, []):
            self._subjects[class_id].append(subject)

    def _class_id_for_student(self, student_id):
        for u in self._users.values():
            if u.id == student_id:
                return u.class_id
        return None

    def get_schedule(self, class_id):
        return list(self._schedule.get(class_id, []))

    def get_students(self, class_id):
        return [u for u in self._users.values() if u.role == Role.STUDENT and u.class_id == class_id]

    def add_student(self, first_name, last_name, class_id):
        base_login = generate_login(first_name, last_name)
        if not base_login:
            raise ValueError("Zadej platné jméno a příjmení.")
        email = f"{base_login}@skola.cz"
        suffix = 2
        while email in self._users:
            email = f"{base_login}{suffix}@skola.cz"
            suffix += 1

        student_id = f"s{self._next_student_num}"
        self._next_student_num += 1
        full_name = f"{first_name.strip()} {last_name.strip()}"
        user = User(student_id, full_name, Role.STUDENT, class_id)

        self._users[email] = user
        self._passwords[email] = DEFAULT_STUDENT_PASSWORD
        self._grades[student_id] = []
        return user, email, DEFAULT_STUDENT_PASSWORD

    def get_teacher(self, class_id):
        for u in self._users.values():
            if u.role == Role.TEACHER and u.class_id == class_id:
                return u
        return None

    def get_subjects(self, class_id):
        return list(self._subjects.get(class_id, []))

    def add_subject(self, class_id, name):
        subjects = self._subjects.setdefault(class_id, [])
        if name not in subjects:
            subjects.append(name)

    def set_schedule_item(self, class_id, day, period, subject, room, teacher):
        items = self._schedule.setdefault(class_id, [])
        for i, it in enumerate(items):
            if it.day == day and it.period == period:
                items[i] = ScheduleItem(day, period, subject, room, teacher)
                return
        items.append(ScheduleItem(day, period, subject, room, teacher))

    def delete_schedule_item(self, class_id, day, period):
        items = self._schedule.get(class_id, [])
        self._schedule[class_id] = [it for it in items if not (it.day == day and it.period == period)]

    def get_messages(self, student_id):
        # V mock režimu se nikam po síti neposílá, takže se zde záměrně
        # neřeší šifrování - je jen pro reálnou komunikaci se serverem
        # (viz SupabaseAPIClient níže a modul crypto.py).
        return list(self._messages.get(student_id, []))

    def send_message(self, student_id, sender, content):
        msgs = self._messages.setdefault(student_id, [])
        msgs.append(Message(
            id=f"m{len(msgs) + 1}",
            student_id=student_id,
            sender_id=sender.id,
            sender_name=sender.name,
            content=content,
            created_at=datetime.now().strftime("%d.%m. %H:%M"),
        ))


class SupabaseAPIClient(BaseAPIClient):
    """
    Očekávané Supabase objekty: tabulky profiles/grades/schedule/subjects/messages
    + RLS + RPC funkce get_student_grades_with_average (viz sql/schema.sql).
    Obsah zpráv se šifruje/dešifruje v `crypto.py` ještě před odesláním/po
    přijetí - server tak vidí jen ciphertext, nikdy čitelný text zprávy.
    """

    def __init__(self, url: str, key: str):
        from supabase import create_client
        self.sb = create_client(url, key)
        self._admin_sb = None  # lazy - vytvoří se jen když je potřeba (add_student)

    def _admin_client(self):
        import config
        if not config.SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                "Zakládání nových účtů vyžaduje servisní (service role) klíč Supabase. "
                "Nastav proměnnou prostředí SUPABASE_SERVICE_KEY. Tento klíč nikdy "
                "nesdílej ani nenahrávej do repozitáře - patří jen do bezpečného, "
                "učitelem/administrátorem spravovaného prostředí."
            )
        if self._admin_sb is None:
            from supabase import create_client
            import config as cfg
            self._admin_sb = create_client(cfg.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
        return self._admin_sb

    def login(self, email, password):
        res = self.sb.auth.sign_in_with_password({"email": email, "password": password})
        profile = self.sb.table("profiles").select("*").eq("id", res.user.id).single().execute().data
        return User(id=res.user.id, name=profile["full_name"], role=Role(profile["role"]), class_id=profile.get("class_id"))

    def get_grades(self, student_id):
        res = self.sb.rpc("get_student_grades_with_average", {"p_student_id": student_id}).execute().data
        if not res:
            return [], 0.0
        grades = [Grade(r["id"], r["subject"], r["value"], r["weight"], r.get("note", "")) for r in res]
        avg = float(res[0]["weighted_average"] or 0.0)
        return grades, avg

    def add_grade(self, student_id, subject, value, weight, note):
        # RLS policie ověří, že insert provádí učitel dané třídy
        self.sb.table("grades").insert({
            "student_id": student_id, "subject": subject,
            "value": value, "weight": weight, "note": note,
        }).execute()

    def get_schedule(self, class_id):
        res = self.sb.table("schedule").select("*").eq("class_id", class_id).execute().data
        return [ScheduleItem(r["day"], r["period"], r["subject"], r.get("room", ""), r.get("teacher", "")) for r in res]

    def get_students(self, class_id):
        res = self.sb.table("profiles").select("*").eq("role", "student").eq("class_id", class_id).execute().data
        return [User(r["id"], r["full_name"], Role.STUDENT, class_id) for r in res]

    def add_student(self, first_name, last_name, class_id):
        base_login = generate_login(first_name, last_name)
        if not base_login:
            raise ValueError("Zadej platné jméno a příjmení.")
        email = f"{base_login}@skola.cz"
        full_name = f"{first_name.strip()} {last_name.strip()}"

        admin = self._admin_client()
        # unikátnost e-mailu si ověří samo Supabase auth (vyhodí chybu při kolizi)
        result = admin.auth.admin.create_user({
            "email": email,
            "password": DEFAULT_STUDENT_PASSWORD,
            "email_confirm": True,
        })
        admin.table("profiles").insert({
            "id": result.user.id, "full_name": full_name, "role": "student", "class_id": class_id,
        }).execute()
        return User(result.user.id, full_name, Role.STUDENT, class_id), email, DEFAULT_STUDENT_PASSWORD

    def get_teacher(self, class_id):
        res = self.sb.table("profiles").select("*").eq("role", "teacher").eq("class_id", class_id).limit(1).execute().data
        if not res:
            return None
        r = res[0]
        return User(r["id"], r["full_name"], Role.TEACHER, class_id)

    def get_subjects(self, class_id):
        res = self.sb.table("subjects").select("name").eq("class_id", class_id).order("name").execute().data
        return [r["name"] for r in res]

    def add_subject(self, class_id, name):
        # RLS policie ověří, že insert provádí učitel dané třídy
        self.sb.table("subjects").upsert(
            {"class_id": class_id, "name": name}, on_conflict="class_id,name"
        ).execute()

    def set_schedule_item(self, class_id, day, period, subject, room, teacher):
        # vyžaduje unikátní constraint (class_id, day, period), viz sql/schema.sql
        self.sb.table("schedule").upsert({
            "class_id": class_id, "day": day, "period": period,
            "subject": subject, "room": room, "teacher": teacher,
        }, on_conflict="class_id,day,period").execute()

    def delete_schedule_item(self, class_id, day, period):
        self.sb.table("schedule").delete().eq("class_id", class_id).eq("day", day).eq("period", period).execute()

    def get_messages(self, student_id):
        import crypto
        res = self.sb.table("messages").select("*").eq("student_id", student_id).order("created_at").execute().data
        messages = []
        for r in res:
            content = crypto.decrypt(r["content"])  # dešifrování až v klientovi
            created_at = r.get("created_at", "")
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%d.%m. %H:%M")
            except (ValueError, AttributeError):
                pass
            messages.append(Message(r["id"], student_id, r["sender_id"], r["sender_name"], content, created_at))
        return messages

    def send_message(self, student_id, sender, content):
        import crypto
        self.sb.table("messages").insert({
            "student_id": student_id,
            "sender_id": sender.id,
            "sender_name": sender.name,
            "content": crypto.encrypt(content),  # šifrováno ještě před odesláním na server
        }).execute()
