from typing import Optional
from models import User


class SessionManager:
    """Drží session pouze v paměti procesu, nikdy na disku."""
    _instance: Optional["SessionManager"] = None

    def __init__(self):
        self.user: Optional[User] = None
        self.token: Optional[str] = None

    @classmethod
    def instance(cls) -> "SessionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_session(self, user: User, token: Optional[str] = None):
        self.user = user
        self.token = token

    def clear(self):
        self.user = None
        self.token = None