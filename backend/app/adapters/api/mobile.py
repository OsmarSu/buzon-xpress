"""Native session transport; browser sessions remain cookie and CSRF protected."""
from hashlib import sha256
import hmac
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import Field, SecretStr

from app.adapters.api.auth import serialize_user
from app.adapters.api.dto import Login, Register, Resource, ResetRequest, Session, MfaChallenge, MfaCode, User
from app.adapters.api.limits import IdentityRateLimit
from app.adapters.api.security import ApiSecurity
from app.application.identity import IdentityService, MOBILE_SESSION_PREFIX
from app.application.mfa import MfaService
from app.config import Settings
from app.domain.identity import IdentityError


class MobileSession(Session):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"


class MobileMfaVerify(MfaCode):
    challenge_token: Annotated[SecretStr, Field(min_length=47, max_length=47)]


def native_request(request: Request) -> None:
    # No ambient browser credentials and no cookie-changing response.
    if request.headers.get("origin") is not None or request.headers.get("cookie") is not None:
        raise IdentityError(403, "CLIENTE_NO_ADMITIDO", "Utiliza el formulario de acceso correspondiente.")
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
        raise IdentityError(415, "PETICION_INVALIDA", "Revisa los campos enviados.")


def mobile_router(service: IdentityService, settings: Settings, limits: IdentityRateLimit) -> APIRouter:
    router = APIRouter(prefix="/mobile/auth", tags=["Identidad móvil"], dependencies=[Depends(native_request)])
    security = ApiSecurity(service, settings)
    mfa = MfaService(service, settings)

    def limit(request: Request, operation: str, maximum: int) -> None:
        limits.check(operation, request.client.host if request.client else "unknown", maximum)

    @router.post("/register", response_model=User, status_code=201)
    def register(body: Register, request: Request):
        limit(request, "register", 8)
        return serialize_user(service.register(str(body.email), body.full_name, body.password.get_secret_value(), body.phone))

    @router.post("/login", response_model=MobileSession | MfaChallenge)
    def login(body: Login, request: Request):
        limit(request, "login", 10)
        key = hmac.new(settings.session_secret, b"login-rate-v1:" + str(body.email).casefold().encode(), sha256).hexdigest()
        limits.check("login-account", key, 10)
        user = service.authenticate(str(body.email), body.password.get_secret_value())
        if user["mfa_enabled"]:
            return MfaChallenge(**mfa.begin_login(user, None, mobile=True))
        user, token, expires = service.issue_session(user, None, token_prefix=MOBILE_SESSION_PREFIX)
        return MobileSession(user=serialize_user(user), access_token=token, expires_at=expires)

    @router.post("/mfa/verify", response_model=MobileSession)
    def verify(body: MobileMfaVerify, request: Request):
        limit(request, "mfa-verify", 20)
        user, token, expires = mfa.verify_login(body.challenge_token.get_secret_value(), body.code.get_secret_value(), mobile=True)
        return MobileSession(user=serialize_user(user), access_token=token, expires_at=expires)

    @router.post("/password-reset/request", response_model=Resource)
    def reset(body: ResetRequest, request: Request, tasks: BackgroundTasks):
        limit(request, "password-reset-request", 8)
        key = hmac.new(settings.session_secret, b"reset-rate-v1:" + str(body.email).casefold().encode(), sha256).hexdigest()
        limits.check("password-reset-address", key, 3)
        tasks.add_task(service.request_password_reset, str(body.email).casefold())
        return Resource(id=uuid4(), state="SOLICITADA")

    @router.post("/logout", response_model=Resource)
    def logout(request: Request):
        security.actor(request)
        return Resource(id=service.logout(security.session_token(request)), state="REVOCADA")

    return router
