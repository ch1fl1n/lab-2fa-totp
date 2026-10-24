import time
from collections import defaultdict, deque

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import security
from .db import User, users

_bearer = HTTPBearer(auto_error=False)


def elevated_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> User:
    """Solo deja pasar access_tokens con mfa_verified=true (nunca un pre_auth_token)."""
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el access_token")
    try:
        payload = security.decode_token(creds.credentials, security.ACCESS)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido, expirado o sin segundo factor")
    if payload.get("mfa_verified") is not True:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Se requiere mfa_verified")
    user = users.get_by_id(payload["sub"])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no existe")
    return user


class RateLimiter:
    """Limita intentos de código por pre_auth_token/IP (evita adivinar 6 dígitos por fuerza bruta)."""

    def __init__(self, max_attempts: int = 20, per_seconds: int = 300) -> None:
        self.max_attempts = max_attempts
        self.per_seconds = per_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.per_seconds:
            hits.popleft()
        if len(hits) >= self.max_attempts:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")
        hits.append(now)


code_limiter = RateLimiter()
