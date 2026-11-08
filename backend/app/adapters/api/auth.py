from hashlib import sha256
import hmac
import re
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.engine import RowMapping

from app.adapters.api.dto import Csrf, Login, Register, Resource, Session, TokenAction, User
from app.adapters.api.limits import IdentityRateLimit
from app.application.identity import IdentityService, SESSION_TTL
from app.config import Settings
from app.domain.identity import IdentityError


SESSION_COOKIE = "buzon_session"
API_PATH = "/api/v1"
OPAQUE = re.compile(r"[A-Za-z0-9_-]{43}")


def serialize_user(user: RowMapping) -> User:
    return User(
        id=user["id"],
        full_name=user["full_name"],
        role=user["role"],
        contact_verified=user["contact_verified_at"] is not None,
    )


def auth_router(service: IdentityService, settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Identidad"])
    csrf_cookie = "__Host-buzon_csrf" if settings.secure_cookies else "buzon_csrf"
    csrf_path = "/" if settings.secure_cookies else API_PATH
    cookie_flags = {"secure": settings.secure_cookies, "httponly": True, "samesite": "lax"}
    limits = IdentityRateLimit()

    def limit(request: Request, operation: str, maximum: int) -> None:
        origin = request.client.host if request.client is not None else "unknown"
        limits.check(operation, origin, maximum)

    def cookie_value(request: Request, name: str) -> str | None:
        value = request.cookies.get(name, "")
        return value if OPAQUE.fullmatch(value) else None

    def signed_context(context: str, session: str | None) -> str:
        # The cookie values have fixed ASCII length and the delimiter is outside their alphabet.
        message = f"csrf-v1:{context}:{session or ''}".encode("ascii")
        return hmac.new(settings.session_secret, message, sha256).hexdigest()

    def require_csrf(request: Request) -> None:
        if request.headers.get("origin") not in settings.allowed_origins:
            raise IdentityError(403, "ORIGEN_NO_AUTORIZADO", "El origen de la petición no está autorizado.")
        context = cookie_value(request, csrf_cookie)
        session = cookie_value(request, SESSION_COOKIE)
        presented = request.headers.get("x-csrf-token", "")
        if not context or not re.fullmatch(r"[0-9a-f]{64}", presented):
            raise IdentityError(403, "CSRF_INVALIDO", "Actualiza la página y vuelve a intentarlo.")
        if not hmac.compare_digest(presented, signed_context(context, session)):
            raise IdentityError(403, "CSRF_INVALIDO", "Actualiza la página y vuelve a intentarlo.")

    @router.get("/csrf", response_model=Csrf)
    def csrf(request: Request, response: Response) -> Csrf:
        context = cookie_value(request, csrf_cookie)
        if context is None:
            context = token_urlsafe(32)
            response.set_cookie(csrf_cookie, context, path=csrf_path, **cookie_flags)
        return Csrf(csrf_token=signed_context(context, cookie_value(request, SESSION_COOKIE)))

    @router.post("/register", status_code=201, response_model=User, dependencies=[Depends(require_csrf)])
    def register(body: Register, request: Request) -> User:
        limit(request, "register", 8)
        return serialize_user(
            service.register(str(body.email), body.full_name, body.password.get_secret_value(), body.phone)
        )

    @router.post("/verify-contact", response_model=Resource, dependencies=[Depends(require_csrf)])
    def verify_contact(body: TokenAction, request: Request) -> Resource:
        limit(request, "verify-contact", 12)
        return Resource(id=service.verify_contact(body.token.get_secret_value()), state="VERIFICADO")

    @router.post("/login", response_model=Session, dependencies=[Depends(require_csrf)])
    def login(body: Login, request: Request, response: Response) -> Session:
        limit(request, "login", 10)
        user, token, expires_at = service.login(
            str(body.email), body.password.get_secret_value(), cookie_value(request, SESSION_COOKIE)
        )
        response.set_cookie(SESSION_COOKIE, token, max_age=int(SESSION_TTL.total_seconds()), path=API_PATH, **cookie_flags)
        response.delete_cookie(csrf_cookie, path=csrf_path, **cookie_flags)
        return Session(user=serialize_user(user), expires_at=expires_at)

    @router.get("/me", response_model=User)
    def me(request: Request) -> User:
        return serialize_user(service.current_user(cookie_value(request, SESSION_COOKIE)))

    @router.post("/logout", response_model=Resource, dependencies=[Depends(require_csrf)])
    def logout(request: Request, response: Response) -> Resource:
        session_id = service.logout(cookie_value(request, SESSION_COOKIE))
        response.delete_cookie(SESSION_COOKIE, path=API_PATH, **cookie_flags)
        response.delete_cookie(csrf_cookie, path=csrf_path, **cookie_flags)
        return Resource(id=session_id, state="REVOCADA")

    return router
