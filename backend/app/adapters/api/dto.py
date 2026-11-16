from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, SecretStr, StringConstraints, Field

from app.domain.identity import Role


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Payload):
    email: EmailStr
    password: Annotated[SecretStr, Field(min_length=1, max_length=128)]


class Register(Login):
    password: Annotated[SecretStr, Field(min_length=15, max_length=128)]
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    phone: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=24)] | None = None


class TokenAction(Payload):
    token: Annotated[SecretStr, Field(min_length=43, max_length=43)]


class ResetRequest(Payload):
    email: EmailStr


class ResetComplete(TokenAction):
    password: Annotated[SecretStr, Field(min_length=15, max_length=128)]


class User(Payload):
    id: UUID
    full_name: str
    role: Role
    contact_verified: bool
    mfa_enabled: bool


class Session(Payload):
    user: User
    expires_at: datetime


class Csrf(Payload):
    csrf_token: str


class Resource(Payload):
    id: UUID
    state: str


class Error(Payload):
    code: str
    message: str
    correlation_id: UUID


class Health(Payload):
    status: Literal["OK", "DEGRADADO"]
    database_checked: bool


class MfaChallenge(Payload):
    mfa_required: Literal[True] = True
    challenge_token: str
    expires_at: datetime


class MfaStatus(Payload):
    enabled: bool
    recovery_codes_remaining: int


class MfaPassword(Payload):
    password: Annotated[SecretStr, Field(min_length=1, max_length=128)]


class MfaCode(Payload):
    code: Annotated[SecretStr, Field(min_length=6, max_length=64)]


class MfaVerify(MfaCode):
    challenge_token: Annotated[SecretStr, Field(min_length=43, max_length=43)]


class MfaManage(MfaPassword, MfaCode):
    pass


class MfaSetup(Payload):
    secret: str
    otpauth_uri: str
    expires_at: datetime


class MfaRecovery(Payload):
    enabled: Literal[True] = True
    recovery_codes: list[str]
