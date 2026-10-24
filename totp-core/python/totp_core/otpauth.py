"""URI otpauth://totp/... (formato de Google Authenticator) que va dentro del QR."""

from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse

from . import base32
from .totp import ALGORITHM, DIGITS, PERIOD


def build_otpauth_uri(secret_b32: str, account: str, issuer: str) -> str:
    label = quote(f"{issuer}:{account}")
    params = urlencode({
        "secret": base32.normalize(secret_b32),
        "issuer": issuer,
        "algorithm": ALGORITHM,
        "digits": DIGITS,
        "period": PERIOD,
    }, quote_via=quote)
    return f"otpauth://totp/{label}?{params}"


def parse_otpauth_uri(uri: str) -> dict:
    parsed = urlparse(uri)
    if parsed.scheme != "otpauth" or parsed.netloc != "totp":
        raise ValueError("No es un URI otpauth://totp/")
    query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    label = unquote(parsed.path.lstrip("/"))
    issuer, _, account = label.rpartition(":")
    return {"secret": query["secret"], "account": account, "issuer": query.get("issuer", issuer)}
