import os

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta la variable de entorno {name} (revisa backend-prefect/.env)")
    return value


USE_MEMORY_DB = os.getenv("USE_MEMORY_DB", "0") == "1"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
JWT_SECRET = _required("JWT_SECRET")
FERNET_KEY = _required("FERNET_KEY")
TOTP_ISSUER = os.getenv("TOTP_ISSUER", "Lab2FA")

PRE_AUTH_TOKEN_MINUTES = 5  # solo sirve para /auth/verify-2fa y el aprovisionamiento
ACCESS_TOKEN_MINUTES = 60
ANTI_REPLAY_SECONDS = 90  # (user_id, código) usado queda bloqueado este tiempo
BACKUP_CODES_COUNT = 8
