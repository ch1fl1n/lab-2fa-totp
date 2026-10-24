"""Excepciones de dominio. Las lanzan las tasks de Prefect (el Flow queda en rojo, `Failed`)
y la API las traduce a códigos HTTP en main.py."""


class AuthError(Exception):
    status_code = 401


class InvalidCredentials(AuthError):
    pass


class InvalidPreAuthState(AuthError):
    """El pre_auth_token no es válido, expiró o el estado 2FA no permite esta operación."""


class ReplayAttackDetected(AuthError):
    """La combinación (user_id, código) ya se usó dentro de la ventana anti-replay."""

    status_code = 409


class InvalidSecondFactor(AuthError):
    pass
