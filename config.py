import os

USE_MOCK_API = os.getenv("EDUBOARD_USE_MOCK", "1") == "1"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "public-anon-key")

# Servisní (service role) klíč Supabase - POUZE pro operace, které anon klíč
# nesmí dělat (např. založení nového přihlašovacího účtu žáka učitelem).
# NIKDY ho nedávej do veřejného repozitáře ani do appky distribuované žákům -
# patří jen do prostředí, ke kterému má přístup výhradně učitel/administrátor.
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Symetrický klíč pro šifrování obsahu zpráv (Fernet, knihovna cryptography)
# předtím, než odejdou na Supabase server - server tak nikdy neuvidí čitelný
# text zprávy. V produkci patří do bezpečně spravovaného úložiště tajných
# klíčů (a měl by ho mít každý nasazený server jiný), ne natvrdo v kódu -
# tady je jen ukázkový vývojový výchozí klíč, aby appka fungovala rovnou.
MESSAGE_ENCRYPTION_KEY = os.getenv(
    "EDUBOARD_MESSAGE_KEY", "asMfc7ocKFGHbNCENyksUbbiwtWdD_Y4opweshEWrwU="
)
