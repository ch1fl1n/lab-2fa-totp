"""HOTP (RFC 4226) y TOTP (RFC 6238). Parámetros tomados de totp-core/spec.json."""

import hashlib
import hmac
import struct
from dataclasses import dataclass

from .selftest import SPEC

ALGORITHM: str = SPEC["algorithm"]
DIGITS: int = SPEC["digits"]
PERIOD: int = SPEC["period"]
WINDOW: int = SPEC["window"]


def hotp(key: bytes, counter: int, digits: int = DIGITS) -> str:
    # 1. HMAC-SHA1(secreto, contador como entero de 8 bytes big-endian)
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    # 2. Truncamiento dinámico: los 4 bits bajos del último byte indican el offset.
    offset = mac[-1] & 0x0F
    # 3. 4 bytes desde el offset, sin el bit de signo.
    binary = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
    # 4. Módulo 10^digits con ceros a la izquierda.
    return str(binary % (10**digits)).zfill(digits)


def counter_at(unix_seconds: float, period: int = PERIOD) -> int:
    """C = floor(UnixTime / 30)."""
    return int(unix_seconds // period)


def totp(key: bytes, unix_seconds: float, digits: int = DIGITS, period: int = PERIOD) -> str:
    return hotp(key, counter_at(unix_seconds, period), digits)


@dataclass(frozen=True)
class Match:
    counter: int
    offset: int  # -1, 0 o +1

    @property
    def window(self) -> str:
        """'C-1', 'C' o 'C+1': en qué ventana hizo match el código."""
        return "C" if self.offset == 0 else f"C{self.offset:+d}"


def find_match(key: bytes, code: str, unix_seconds: float, window: int = WINDOW) -> Match | None:
    """Evalúa las ventanas C-1, C y C+1 (con window=1) y devuelve cuál coincidió."""
    code = code.strip().replace(" ", "")
    if len(code) != DIGITS or not code.isdigit():
        return None
    current = counter_at(unix_seconds)
    for offset in sorted(range(-window, window + 1), key=abs):  # C primero, luego C-1 y C+1
        if hmac.compare_digest(hotp(key, current + offset), code):
            return Match(counter=current + offset, offset=offset)
    return None
