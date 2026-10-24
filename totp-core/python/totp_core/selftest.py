"""Carga totp-core/spec.json y verifica la implementación contra sus vectores.

El backend llama a `self_test()` al arrancar: si algún cálculo no coincide con el estándar
(o con lo que calcula la app móvil), el servidor no arranca.
"""

import json
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parents[2] / "spec.json"
SPEC: dict = json.loads(SPEC_PATH.read_text(encoding="utf-8"))


class SelfTestError(RuntimeError):
    pass


def self_test() -> int:
    """Ejecuta todos los vectores de spec.json. Devuelve cuántos pasaron o lanza SelfTestError."""
    from . import base32
    from .totp import hotp, totp

    vectors = SPEC["vectors"]
    checks: list[tuple[str, str, str]] = []

    h = vectors["hotp_rfc4226"]
    key = h["secret_ascii"].encode()
    checks += [(f"HOTP c={i}", hotp(key, i), code) for i, code in enumerate(h["codes"])]

    t = vectors["totp_rfc6238"]
    key = t["secret_ascii"].encode()
    checks += [(f"TOTP t={c['time']}", totp(key, c["time"], digits=t["digits"]), c["code"]) for c in t["cases"]]

    for b in vectors["base32"]:
        checks.append((f"Base32 {b['ascii']}", base32.encode(b["ascii"].encode()), b["base32"]))
        checks.append((f"Base32 decode {b['base32']}", base32.decode(b["base32"]).decode(), b["ascii"]))

    for c in vectors["cross_check"]:
        checks.append((f"Cruce {c['secret_base32']}", totp(base32.decode(c["secret_base32"]), c["time"]), c["code"]))

    failed = [f"{name}: obtuvo {got}, esperaba {want}" for name, got, want in checks if got != want]
    if failed:
        raise SelfTestError("totp-core no cumple la especificación:\n" + "\n".join(failed))
    return len(checks)
