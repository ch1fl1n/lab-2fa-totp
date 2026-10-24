from fastapi import APIRouter, HTTPException, Request, status
from pydantic import SecretStr

from .. import security
from ..db import TotpStatus, users
from ..deps import code_limiter
from ..flows import login_flow, verify_2fa_flow
from ..schemas import Credentials, LoginOut, SessionOut, UserOut, Verify2faIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: Credentials):
    if users.get_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese email ya está registrado")
    user = users.create(body.email, security.hash_password(body.password))
    return UserOut(id=str(user["id"]), email=user["email"], totp_status=user["totp_status"])


@router.post("/login", response_model=LoginOut)
def login(body: Credentials):
    """Step-Up, paso 1: NO da acceso. Devuelve un pre_auth_token restringido."""
    result = login_flow(body.email, SecretStr(body.password))
    next_step = "verify-2fa" if result["totp_status"] == TotpStatus.ACTIVE.value else "setup-2fa"
    return LoginOut(next_step=next_step, **result)


@router.post("/verify-2fa", response_model=SessionOut)
def verify_2fa(body: Verify2faIn, request: Request):
    """Step-Up, paso 2: pre_auth_token + código (TOTP o respaldo) -> access_token (mfa_verified)."""
    code_limiter.check(request.client.host if request.client else "local")
    result = verify_2fa_flow(SecretStr(body.pre_auth_token), body.code, body.method)
    return SessionOut(**result)
