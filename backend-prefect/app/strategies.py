"""Strategy Pattern para el segundo factor: TOTP o código de respaldo, intercambiables."""

import hmac
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import totp_core

from . import security
from .db import User, now_iso, users


@dataclass(frozen=True)
class StrategyResult:
    method: str  # "totp" | "backup"
    detail: str  # ventana que hizo match ("C-1", "C", "C+1") o "backup"


class SecondFactorStrategy(ABC):
    method: str

    @abstractmethod
    def verify(self, user: User, code: str) -> StrategyResult | None:
        """Devuelve el resultado si el código es válido, o None si no lo es."""

    def commit(self, user: User, code: str) -> None:
        """Efectos tras una verificación exitosa (por defecto, ninguno)."""


class TOTPStrategy(SecondFactorStrategy):
    """Valida el código de 6 dígitos evaluando las ventanas C-1, C y C+1 (totp-core)."""

    method = "totp"

    def __init__(self, now: float | None = None) -> None:
        self.now = now

    def verify(self, user: User, code: str) -> StrategyResult | None:
        key = security.decrypt_secret(user["totp_secret_enc"])
        match = totp_core.find_match(key, code, self.now if self.now is not None else time.time())
        return StrategyResult(self.method, match.window) if match else None


class BackupCodeStrategy(SecondFactorStrategy):
    """Códigos de emergencia de un solo uso (por si se pierde el teléfono)."""

    method = "backup"

    def _find(self, user: User, code: str) -> int | None:
        wanted = security.hash_backup_code(code)
        for i, entry in enumerate(user.get("backup_codes") or []):
            if entry.get("used_at") is None and hmac.compare_digest(entry["hash"], wanted):
                return i
        return None

    def verify(self, user: User, code: str) -> StrategyResult | None:
        return StrategyResult(self.method, "backup") if self._find(user, code) is not None else None

    def commit(self, user: User, code: str) -> None:
        index = self._find(user, code)
        if index is None:
            return
        codes = [dict(c) for c in user["backup_codes"]]
        codes[index]["used_at"] = now_iso()
        users.update(str(user["id"]), {"backup_codes": codes})


def get_strategy(method: str) -> SecondFactorStrategy:
    strategies: dict[str, type[SecondFactorStrategy]] = {"totp": TOTPStrategy, "backup": BackupCodeStrategy}
    if method not in strategies:
        raise ValueError(f"Método de segundo factor desconocido: {method}")
    return strategies[method]()
