"""Las 4 pruebas de aceptación de la guía, automatizadas contra la API (con Prefect real)."""

import time

import totp_core
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PASSWORD = "contrasena-segura"


def register_and_activate(email: str) -> tuple[bytes, list[str], str]:
    assert client.post("/auth/register", json={"email": email, "password": PASSWORD}).status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()
    assert login["next_step"] == "setup-2fa"

    setup = client.post("/2fa/setup", json={"pre_auth_token": login["pre_auth_token"]}).json()
    assert setup["totp_status"] == "PENDING_VERIFICATION"
    assert setup["qr_svg_data_uri"].startswith("data:image/svg+xml")
    assert totp_core.parse_otpauth_uri(setup["otpauth_uri"])["secret"] == setup["secret"]
    key = totp_core.base32_decode(setup["secret"])

    # PENDING_VERIFICATION todavía no exige 2FA: un nuevo login vuelve a pedir el aprovisionamiento.
    again = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()
    assert again["next_step"] == "setup-2fa"

    r = client.post("/2fa/activate", json={"pre_auth_token": login["pre_auth_token"], "code": "000000"})
    assert r.status_code == 401
    activation_code = totp_core.totp(key, time.time())
    r = client.post("/2fa/activate", json={"pre_auth_token": login["pre_auth_token"], "code": activation_code})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["backup_codes"]) == 8
    return key, body["backup_codes"], activation_code


def pre_auth(email: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200 and r.json()["next_step"] == "verify-2fa"
    return r.json()["pre_auth_token"]


def test_totp_core_loaded():
    assert totp_core.self_test() >= 20


def test_step_up_and_vault():
    email = "stepup@example.com"
    key, _, _ = register_and_activate(email)
    token = pre_auth(email)

    # El pre_auth_token NO abre la bóveda.
    assert client.get("/api/boveda-secreta", headers={"Authorization": f"Bearer {token}"}).status_code == 401

    # Reloj del celular adelantado un paso -> match en la ventana C+1.
    code = totp_core.totp(key, time.time() + 30)
    r = client.post("/auth/verify-2fa", json={"pre_auth_token": token, "code": code})
    assert r.status_code == 200, r.text
    assert r.json()["window"] == "C+1" and r.json()["mfa_verified"] is True

    vault = client.get("/api/boveda-secreta", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert vault.status_code == 200 and "bóveda" in vault.json()["mensaje"]


def test_anti_replay():
    email = "replay@example.com"
    key, _, activation_code = register_and_activate(email)
    # Un código distinto al de la activación (los flows tardan y la ventana pudo avanzar).
    code = next(c for c in (totp_core.totp(key, time.time() + d) for d in (0, 30)) if c != activation_code)
    assert client.post("/auth/verify-2fa", json={"pre_auth_token": pre_auth(email), "code": code}).status_code == 200
    r = client.post("/auth/verify-2fa", json={"pre_auth_token": pre_auth(email), "code": code})
    assert r.status_code == 409 and r.json()["error"] == "ReplayAttackDetected"


def test_backup_code_strategy_single_use():
    email = "backup@example.com"
    _, backup_codes, _ = register_and_activate(email)
    body = {"pre_auth_token": pre_auth(email), "code": backup_codes[0].lower(), "method": "backup"}
    r = client.post("/auth/verify-2fa", json=body)
    assert r.status_code == 200 and r.json()["method"] == "backup"
    # Mismo código de respaldo en otro login: rechazado (anti-replay y, después, por estar usado).
    body["pre_auth_token"] = pre_auth(email)
    assert client.post("/auth/verify-2fa", json=body).status_code in (401, 409)


def test_wrong_password_and_time_endpoint():
    assert client.post("/auth/login", json={"email": "nadie@example.com", "password": "x" * 8}).status_code == 401
    t = client.get("/time").json()
    assert abs(t["server_time_ms"] - time.time() * 1000) < 2000 and t["period"] == 30
