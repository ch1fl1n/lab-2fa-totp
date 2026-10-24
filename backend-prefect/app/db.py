"""Tabla `users` en Supabase (usada solo como base de datos; no se usa Supabase Auth ni su MFA).

Con USE_MEMORY_DB=1 se usa un diccionario en memoria (la guía lo permite) para probar sin Supabase.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from . import config

User = dict[str, Any]


class TotpStatus(str, Enum):
    """Máquina de estados del aprovisionamiento 2FA (Process Manager)."""

    DISABLED = "DISABLED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"  # secreto generado, falta el primer código válido
    ACTIVE = "ACTIVE"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SupabaseUsers:
    def __init__(self) -> None:
        from supabase import create_client

        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en backend-prefect/.env")
        self._client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)

    def _table(self):
        return self._client.table("users")

    def get_by_email(self, email: str) -> User | None:
        rows = self._table().select("*").eq("email", email).limit(1).execute().data
        return rows[0] if rows else None

    def get_by_id(self, user_id: str) -> User | None:
        rows = self._table().select("*").eq("id", user_id).limit(1).execute().data
        return rows[0] if rows else None

    def create(self, email: str, password_hash: str) -> User:
        return self._table().insert({"email": email, "password_hash": password_hash}).execute().data[0]

    def update(self, user_id: str, fields: dict[str, Any]) -> None:
        self._table().update(fields).eq("id", user_id).execute()


class MemoryUsers:
    def __init__(self) -> None:
        self._rows: dict[str, User] = {}

    def get_by_email(self, email: str) -> User | None:
        return next((dict(u) for u in self._rows.values() if u["email"] == email), None)

    def get_by_id(self, user_id: str) -> User | None:
        row = self._rows.get(user_id)
        return dict(row) if row else None

    def create(self, email: str, password_hash: str) -> User:
        user = {
            "id": str(uuid.uuid4()),
            "email": email,
            "password_hash": password_hash,
            "totp_status": TotpStatus.DISABLED.value,
            "totp_secret_enc": None,
            "backup_codes": [],
            "totp_activated_at": None,
            "created_at": now_iso(),
        }
        self._rows[user["id"]] = user
        return dict(user)

    def update(self, user_id: str, fields: dict[str, Any]) -> None:
        self._rows[user_id].update(fields)


users = MemoryUsers() if config.USE_MEMORY_DB else SupabaseUsers()
