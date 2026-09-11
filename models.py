from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Role(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


@dataclass
class User:
    id: str
    name: str
    role: Role
    class_id: Optional[str] = None


@dataclass
class Grade:
    id: str
    subject: str
    value: int
    weight: int
    note: str = ""


@dataclass
class ScheduleItem:
    day: int          # 0=Po .. 4=Pá
    period: int
    subject: str
    room: str = ""
    teacher: str = ""


@dataclass
class Message:
    id: str
    student_id: str    # identifikuje konverzační vlákno (žák <-> jeho učitel)
    sender_id: str
    sender_name: str
    content: str        # už dešifrovaný, čitelný text (pro zobrazení v GUI)
    created_at: str = ""