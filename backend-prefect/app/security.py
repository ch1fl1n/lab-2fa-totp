"""Contraseñas (PBKDF2), tokens (JWT), cifrado del secreto TOTP (Fernet) y códigos de respaldo."""

import base64
import hashlib
import hmac
import secrets
import time

import jwt
from cryptography.fernet import Fernet

from . import config

PBKDF2_ITERATIONS = 600_000
_fernet = Fernet(config.FERNET_KEY.encode())

# Scopes de los JWT (Step-Up Authentication)
PRE_AUTH = "pre_auth"  # contraseña OK, falta el segundo factor
ACCESS = "access"  # sesión completa (mfa_verified: true)


# --- Contraseñas -------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS, base64.b64encode(salt).decode(), base64.b64encode(digest).decode()
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_b64, hash_b64 = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(salt_b64), int(iterations)
        )
        return hmac.compare_digest(digest, base64.b64decode(hash_b64))
    except (ValueError, TypeError):
        return False


# --- JWT ---------------------------------------------------------------------
def create_token(user_id: str, scope: str, minutes: int, **claims) -> str:
    now = int(time.time())
    payload = {"sub": user_id, "scope": scope, "iat": now, "exp": now + minutes * 60, **claims}
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str, scope: str) -> dict:
    """Devuelve el payload si el token es válido y tiene el scope esperado."""
    payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    if payload.get("scope") != scope:
        raise jwt.InvalidTokenError(f"se esperaba un token '{scope}'")
    return payload


# --- Secreto TOTP (cifrado en reposo) ------------------------------------------
def generate_totp_secret() -> bytes:
    """160 bits aleatorios, el tamaño recomendado por RFC 4226 para HMAC-SHA1."""
    return secrets.token_bytes(20)


def encrypt_secret(raw: bytes) -> str:
    return _fernet.encrypt(raw).decode()


def decrypt_secret(token: str) -> bytes:
    return _fernet.decrypt(token.encode())


# --- Códigos de respaldo -------------------------------------------------------
_BACKUP_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O ni 1/I para evitar confusiones


def generate_backup_codes(count: int) -> list[str]:
    raw = ["".join(secrets.choice(_BACKUP_ALPHABET) for _ in range(8)) for _ in range(count)]
    return [f"{c[:4]}-{c[4:]}" for c in raw]


def normalize_backup_code(code: str) -> str:
    return code.strip().upper().replace("-", "").replace(" ", "")


def hash_backup_code(code: str) -> str:
    # Los códigos son aleatorios de 40 bits y de un solo uso: basta SHA-256 con pepper (JWT_SECRET).
    return hashlib.sha256((config.JWT_SECRET + normalize_backup_code(code)).encode()).hexdigest()
