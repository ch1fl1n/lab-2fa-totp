"""totp-core: implementación desde cero de Base32 (RFC 4648), HOTP (RFC 4226) y TOTP (RFC 6238).

Es la misma lógica que totp-core/ts (usada por la app móvil). Ambas leen totp-core/spec.json
y ejecutan `self_test()` al arrancar, así se garantiza que servidor y celular calculan igual.
"""

from .base32 import decode as base32_decode
from .base32 import encode as base32_encode
from .base32 import group as base32_group
from .otpauth import build_otpauth_uri, parse_otpauth_uri
from .selftest import SPEC, SelfTestError, self_test
from .totp import ALGORITHM, DIGITS, PERIOD, WINDOW, Match, counter_at, find_match, hotp, totp

__all__ = [
    "ALGORITHM", "DIGITS", "PERIOD", "WINDOW", "SPEC", "Match", "SelfTestError",
    "base32_decode", "base32_encode", "base32_group", "build_otpauth_uri", "counter_at",
    "find_match", "hotp", "parse_otpauth_uri", "self_test", "totp",
]
