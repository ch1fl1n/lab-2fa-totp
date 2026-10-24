from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or v.startswith("@") or v.endswith("@"):
            raise ValueError("Email inválido")
        return v


class PreAuthIn(BaseModel):
    pre_auth_token: str


class CodeIn(PreAuthIn):
    code: str = Field(min_length=6, max_length=12)

    @field_validator("code")
    @classmethod
    def strip_code(cls, v: str) -> str:
        return v.strip().replace(" ", "")


class Verify2faIn(CodeIn):
    method: Literal["totp", "backup"] = "totp"


class LoginOut(BaseModel):
    pre_auth_token: str
    totp_status: str
    next_step: str  # "verify-2fa" o "setup-2fa"


class SetupOut(BaseModel):
    secret: str
    secret_grouped: str
    otpauth_uri: str
    qr_svg_data_uri: str
    issuer: str
    account: str
    totp_status: str


class SessionOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    mfa_verified: bool = True
    method: str
    window: str
    backup_codes: list[str] | None = None  # solo al activar (se muestran una única vez)


class UserOut(BaseModel):
    id: str
    email: str
    totp_status: str


class TimeOut(BaseModel):
    server_time_ms: int
    counter: int
    period: int
    seconds_remaining: float
    server_ntp_offset_ms: float | None
