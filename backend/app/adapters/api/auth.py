from hashlib import sha256
import hmac
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from sqlalchemy.engine import RowMapping

from app.adapters.api.dto import Csrf, Login, Register, ResetComplete, ResetRequest, Resource, Session, TokenAction, User
from app.adapters.api.limits import IdentityRateLimit
from app.adapters.api.security import ApiSecurity
from app.application.identity import IdentityService, SESSION_TTL
from app.config import Settings


def serialize_user(user: RowMapping) -> User:
    return User(
        id=user["id"],
        full_name=user["full_name"],
        role=user["role"],
        contact_verified=user["contact_verified_at"] is not None,
    )


def auth_router(service: IdentityService, settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Identidad"])
    security = ApiSecurity(service, settings)
    limits = IdentityRateLimit()

    def limit(request: Request, operation: str, maximum: int) -> None:
        origin = request.client.host if request.client is not None else "unknown"
        limits.check(operation, origin, maximum)

    @router.get("/csrf", response_model=Csrf)
    def csrf(request: Request, response: Response) -> Csrf:
        return Csrf(csrf_token=security.issue_csrf(request, response))

    @router.post("/register", status_code=201, response_model=User, dependencies=[Depends(security.csrf)])
    def register(body: Register, request: Request) -> User:
        limit(request, "register", 8)
        return serialize_user(
            service.register(str(body.email), body.full_name, body.password.get_secret_value(), body.phone)
        )

    @router.post("/verify-contact", response_model=Resource, dependencies=[Depends(security.csrf)])
    def verify_contact(body: TokenAction, request: Request) -> Resource:
        limit(request, "verify-contact", 12)
        return Resource(id=service.verify_contact(body.token.get_secret_value()), state="VERIFICADO")

    @router.post("/password-reset/request", response_model=Resource, dependencies=[Depends(security.csrf)])
    def request_password_reset(body: ResetRequest, request: Request, tasks: BackgroundTasks) -> Resource:
        limit(request, "password-reset-request", 8)
        email = str(body.email).casefold()
        email_key = hmac.new(settings.session_secret, b"reset-rate-v1:" + email.encode(), sha256).hexdigest()
        limits.check("password-reset-address", email_key, 3)
        tasks.add_task(service.request_password_reset, email)
        return Resource(id=uuid4(), state="SOLICITADA")

    @router.post("/password-reset/complete", response_model=Resource, dependencies=[Depends(security.csrf)])
    def complete_password_reset(body: ResetComplete, request: Request, response: Response) -> Resource:
        limit(request, "password-reset-complete", 10)
        user_id = service.complete_password_reset(body.token.get_secret_value(), body.password.get_secret_value())
        security.write_session(request, response)
        security.clear_csrf(request, response)
        return Resource(id=user_id, state="RESTABLECIDA")

    @router.post("/login", response_model=Session, dependencies=[Depends(security.csrf)])
    def login(body: Login, request: Request, response: Response) -> Session:
        limit(request, "login", 10)
        user, token, expires_at = service.login(
            str(body.email), body.password.get_secret_value(), security.session_token(request)
        )
        security.write_session(request, response, token, max_age=int(SESSION_TTL.total_seconds()))
        security.clear_csrf(request, response)
        return Session(user=serialize_user(user), expires_at=expires_at)

    @router.get("/me", response_model=User)
    def me(request: Request) -> User:
        return serialize_user(service.current_user(security.session_token(request)))

    @router.post("/logout", response_model=Resource, dependencies=[Depends(security.csrf)])
    def logout(request: Request, response: Response) -> Resource:
        session_id = service.logout(security.session_token(request))
        security.write_session(request, response)
        security.clear_csrf(request, response)
        return Resource(id=session_id, state="REVOCADA")

    return router
