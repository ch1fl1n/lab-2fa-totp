import jwt
import segno
import totp_core
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import SecretStr

from .. import config, security
from ..db import TotpStatus, users
from ..deps import code_limiter
from ..flows import activate_2fa_flow
from ..schemas import CodeIn, PreAuthIn, SessionOut, SetupOut

router = APIRouter(prefix="/2fa", tags=["2fa"])


@router.post("/setup", response_model=SetupOut)
def setup(body: PreAuthIn):
    """Genera el secreto y deja el 2FA en PENDING_VERIFICATION (aún no bloquea el login)."""
    try:
        payload = security.decode_token(body.pre_auth_token, security.PRE_AUTH)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "El token temporal es inválido o expiró")
    user = users.get_by_id(payload["sub"])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no existe")
    if user["totp_status"] == TotpStatus.ACTIVE.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "El 2FA ya está activo")

    raw = security.generate_totp_secret()
    users.update(str(user["id"]), {
        "totp_secret_enc": security.encrypt_secret(raw),
        "totp_status": TotpStatus.PENDING_VERIFICATION.value,
    })
    secret = totp_core.base32_encode(raw)
    uri = totp_core.build_otpauth_uri(secret, user["email"], config.TOTP_ISSUER)
    return SetupOut(
        secret=secret,
        secret_grouped=totp_core.base32_group(secret),
        otpauth_uri=uri,
        qr_svg_data_uri=segno.make(uri, error="m").svg_data_uri(scale=6, border=2),
        issuer=config.TOTP_ISSUER,
        account=user["email"],
        totp_status=TotpStatus.PENDING_VERIFICATION.value,
    )


@router.post("/activate", response_model=SessionOut)
def activate(body: CodeIn, request: Request):
    """Primer código válido: PENDING_VERIFICATION -> ACTIVE. Devuelve sesión + códigos de respaldo."""
    code_limiter.check(request.client.host if request.client else "local")
    result = activate_2fa_flow(SecretStr(body.pre_auth_token), body.code)
    return SessionOut(method="totp", **result)
