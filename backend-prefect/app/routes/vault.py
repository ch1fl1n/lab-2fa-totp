from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..db import User
from ..deps import elevated_user

router = APIRouter(prefix="/api", tags=["vault"])


@router.get("/boveda-secreta")
def boveda_secreta(user: User = Depends(elevated_user)):
    """Ruta protegida: solo accesible con un access_token que tenga mfa_verified=true."""
    remaining = sum(1 for c in (user.get("backup_codes") or []) if c.get("used_at") is None)
    return {
        "mensaje": f"Bienvenido a la bóveda, {user['email']}. Pasaste el segundo factor.",
        "secreto": "El tesoro está enterrado bajo el servidor de Prefect 🗝️",
        "codigos_respaldo_restantes": remaining,
        "hora_servidor": datetime.now(timezone.utc).isoformat(),
    }
