from abc import ABC, abstractmethod
from typing import List, Tuple
from models import User, Role, Grade, ScheduleItem


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


class MockAPIClient(BaseAPIClient):
    """Simuluje chování backendu (Supabase RLS + RPC) lokálně pro vývoj/demo."""

    def __init__(self):
        self._users = {
            "ucitel@skola.cz": User("t1", "Mgr. Jana Nováková", Role.TEACHER, "3.B"),
            "student@skola.cz": User("s1", "Petr Svoboda", Role.STUDENT, "3.B"),
        }
        self._passwords = {"ucitel@skola.cz": "heslo123", "student@skola.cz": "heslo123"}
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

    def get_schedule(self, class_id):
        return self._schedule.get(class_id, [])

    def get_students(self, class_id):
        return [u for u in self._users.values() if u.role == Role.STUDENT and u.class_id == class_id]


class SupabaseAPIClient(BaseAPIClient):
    """
    Očekávané Supabase objekty: tabulky profiles/grades/schedule + RLS
    + RPC funkce get_student_grades_with_average (viz sql/schema.sql).
    Vážený průměr se počítá v DB, klient jen zobrazuje výsledek.
    """

    def __init__(self, url: str, key: str):
        from supabase import create_client
        self.sb = create_client(url, key)

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