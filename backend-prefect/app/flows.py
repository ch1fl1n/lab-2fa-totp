"""Pipelines de autenticación orquestados y observables con Prefect.

Cada endpoint de login / verificación invoca un @flow; cada paso es una @task que se ve en el
grafo de la UI de Prefect (http://127.0.0.1:4200). Si una task lanza una excepción
(p. ej. ReplayAttackDetected), esa task y el Flow quedan en rojo (`Failed`).

Los parámetros sensibles (contraseña, pre_auth_token) se reciben como SecretStr para que la UI
de Prefect los muestre enmascarados.
"""

import jwt
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from pydantic import SecretStr

from . import config, security
from .db import TotpStatus, User, now_iso, users
from .errors import InvalidCredentials, InvalidPreAuthState, InvalidSecondFactor, ReplayAttackDetected
from .replay_cache import replay_cache
from .strategies import StrategyResult, get_strategy


# --- Tasks -------------------------------------------------------------------------------------
@task(cache_policy=NO_CACHE)
def verify_credentials(email: str, password: SecretStr) -> User:
    logger = get_run_logger()
    user = users.get_by_email(email)
    if user is None or not security.verify_password(password.get_secret_value(), user["password_hash"]):
        logger.warning("Credenciales inválidas para %s", email)
        raise InvalidCredentials("Email o contraseña incorrectos")
    logger.info("Contraseña correcta para %s (estado 2FA: %s)", email, user["totp_status"])
    return user


@task(cache_policy=NO_CACHE)
def issue_pre_auth_token(user: User) -> str:
    get_run_logger().info("Emitido pre_auth_token (scope restringido, %d min)", config.PRE_AUTH_TOKEN_MINUTES)
    return security.create_token(str(user["id"]), security.PRE_AUTH, config.PRE_AUTH_TOKEN_MINUTES)


@task(cache_policy=NO_CACHE)
def validate_pre_auth_state(pre_auth_token: SecretStr, allowed: list[str]) -> User:
    """Task 1: el usuario debe venir con un pre_auth_token válido y en un estado 2FA permitido."""
    logger = get_run_logger()
    try:
        payload = security.decode_token(pre_auth_token.get_secret_value(), security.PRE_AUTH)
    except jwt.PyJWTError as exc:
        logger.error("pre_auth_token rechazado: %s", exc)
        raise InvalidPreAuthState("El token temporal es inválido o expiró; vuelve a iniciar sesión") from exc
    user = users.get_by_id(payload["sub"])
    if user is None or user["totp_status"] not in allowed:
        status = user["totp_status"] if user else "sin usuario"
        logger.error("Estado 2FA %s no permitido (se esperaba %s)", status, allowed)
        raise InvalidPreAuthState(f"Estado 2FA no permitido: {status}")
    logger.info("pre_auth_token válido para %s (estado %s)", user["email"], user["totp_status"])
    return user


@task(cache_policy=NO_CACHE)
def check_anti_replay_cache(user_id: str, code: str) -> None:
    """Task 2: (user_id, código) no puede haberse usado en los últimos 90 segundos."""
    logger = get_run_logger()
    if replay_cache.was_used(user_id, code):
        logger.error("ReplayAttackDetected: el código %s ya fue usado por este usuario", code)
        raise ReplayAttackDetected("Este código ya fue usado. Espera el siguiente.")
    logger.info("Código no visto en los últimos %d s", config.ANTI_REPLAY_SECONDS)


@task(cache_policy=NO_CACHE)
def execute_mfa_strategy(user: User, code: str, method: str) -> StrategyResult:
    """Task 3: ejecuta TOTPStrategy o BackupCodeStrategy y registra la ventana que hizo match."""
    logger = get_run_logger()
    strategy = get_strategy(method)
    logger.info("Estrategia seleccionada: %s", type(strategy).__name__)
    result = strategy.verify(user, code)
    if result is None:
        logger.error("Código inválido con %s (ninguna ventana C-1, C, C+1 coincide)", type(strategy).__name__)
        raise InvalidSecondFactor("Código incorrecto")
    if result.method == "totp":
        hint = {"C-1": "el reloj del celular va ATRASADO", "C": "relojes sincronizados",
                "C+1": "el reloj del celular va ADELANTADO"}[result.detail]
        logger.info("Match TOTP en la ventana %s (%s)", result.detail, hint)
    else:
        logger.info("Código de respaldo válido (se marcará como usado)")
    return result


@task(cache_policy=NO_CACHE)
def transition_to_active(user: User) -> list[str]:
    """Máquina de estados: PENDING_VERIFICATION -> ACTIVE. Genera los códigos de respaldo."""
    codes = security.generate_backup_codes(config.BACKUP_CODES_COUNT)
    users.update(str(user["id"]), {
        "totp_status": TotpStatus.ACTIVE.value,
        "totp_activated_at": now_iso(),
        "backup_codes": [{"hash": security.hash_backup_code(c), "used_at": None} for c in codes],
    })
    get_run_logger().info("Estado 2FA: PENDING_VERIFICATION -> ACTIVE; %d códigos de respaldo", len(codes))
    return codes


@task(cache_policy=NO_CACHE)
def issue_elevated_session(user: User, code: str, result: StrategyResult) -> str:
    """Task 4: marca el código como usado (anti-replay) y emite el JWT final con mfa_verified."""
    user_id = str(user["id"])
    replay_cache.mark_used(user_id, code)
    get_strategy(result.method).commit(user, code)
    get_run_logger().info("Sesión elevada emitida (mfa_verified=true, método=%s)", result.method)
    return security.create_token(user_id, security.ACCESS, config.ACCESS_TOKEN_MINUTES,
                                 mfa_verified=True, amr=[result.method])


# --- Flows -------------------------------------------------------------------------------------
@flow(name="login-password", flow_run_name="login-{email}")
def login_flow(email: str, password: SecretStr) -> dict:
    """Paso 1 del Step-Up: la contraseña solo entrega un pre_auth_token."""
    user = verify_credentials(email, password)
    return {"pre_auth_token": issue_pre_auth_token(user), "totp_status": user["totp_status"]}


@flow(name="verify-2fa", flow_run_name="verify-2fa-{method}")
def verify_2fa_flow(pre_auth_token: SecretStr, code: str, method: str = "totp") -> dict:
    """Paso 2 del Step-Up: pre_auth_token + segundo factor -> access_token."""
    user = validate_pre_auth_state(pre_auth_token, [TotpStatus.ACTIVE.value])
    check_anti_replay_cache(str(user["id"]), code)
    result = execute_mfa_strategy(user, code, method)
    token = issue_elevated_session(user, code, result)
    return {"access_token": token, "method": result.method, "window": result.detail}


@flow(name="activate-2fa", flow_run_name="activate-2fa")
def activate_2fa_flow(pre_auth_token: SecretStr, code: str) -> dict:
    """Aprovisionamiento: el primer código válido pasa el estado a ACTIVE y entrega la sesión."""
    user = validate_pre_auth_state(pre_auth_token, [TotpStatus.PENDING_VERIFICATION.value])
    check_anti_replay_cache(str(user["id"]), code)
    result = execute_mfa_strategy(user, code, "totp")
    backup_codes = transition_to_active(user)
    token = issue_elevated_session(user, code, result)
    return {"access_token": token, "window": result.detail, "backup_codes": backup_codes}
