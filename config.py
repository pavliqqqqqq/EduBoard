import os

USE_MOCK_API = os.getenv("EDUBOARD_USE_MOCK", "1") == "1"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "public-anon-key")