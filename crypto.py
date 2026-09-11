"""
End-to-server šifrování obsahu zpráv symetrickou šifrou Fernet (AES-128 v CBC
módu + HMAC integrita, knihovna `cryptography`). Text zprávy se zašifruje
ještě v klientovi před odesláním na Supabase - server tedy v tabulce
`messages` vidí jen nečitelný ciphertext, ne skutečný obsah konverzace.

Toto je ukázková implementace se sdíleným klíčem (MESSAGE_ENCRYPTION_KEY).
Pro skutečné nasazení s citlivými daty by šel klíč typicky odvozovat
per-uživatel / párovat asymetricky, ne sdílet jeden pevný klíč pro všechny.
"""
from cryptography.fernet import Fernet, InvalidToken
import config

_fernet = Fernet(config.MESSAGE_ENCRYPTION_KEY.encode())


def encrypt(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return "[Zprávu se nepodařilo dešifrovat]"
