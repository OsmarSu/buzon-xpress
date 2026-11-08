from hashlib import sha256
import hmac
import re
from secrets import token_urlsafe

from fastapi import Request, Response
from sqlalchemy.engine import RowMapping

from app.application.identity import IdentityService
from app.config import Settings
from app.domain.identity import IdentityError

API_PATH = "/api/v1"
SESSION_COOKIE = "buzon_session"
OPAQUE = re.compile(r"[A-Za-z0-9_-]{43}")


class ApiSecurity:
    def __init__(self, identity: IdentityService, settings: Settings) -> None:
        self.identity = identity
        self.settings = settings
        self.credential_key = settings.credential_key or hmac.digest(settings.session_secret, b"credentials-v1", sha256)
        self.request_key = settings.request_key or hmac.digest(settings.session_secret, b"idempotency-v1", sha256)
        self.csrf_cookie = "__Host-buzon_csrf" if settings.secure_cookies else "buzon_csrf"
        self.csrf_path = "/" if settings.secure_cookies else API_PATH
        self.cookie_flags = {"secure": settings.secure_cookies, "httponly": True, "samesite": "lax"}

    @staticmethod
    def cookie_value(request: Request, name: str) -> str | None:
        value = request.cookies.get(name, "")
        return value if OPAQUE.fullmatch(value) else None

    def session_token(self, request: Request) -> str | None:
        return self.cookie_value(request, SESSION_COOKIE)

    def actor(self, request: Request) -> RowMapping:
        return self.identity.current_user(self.session_token(request))

    def signed_context(self, context: str, session: str | None) -> str:
        message = f"csrf-v1:{context}:{session or ''}".encode("ascii")
        return hmac.new(self.settings.session_secret, message, sha256).hexdigest()

    def csrf(self, request: Request) -> None:
        if request.headers.get("origin") not in self.settings.allowed_origins:
            raise IdentityError(403, "ORIGEN_NO_AUTORIZADO", "El origen de la petición no está autorizado.")
        context = self.cookie_value(request, self.csrf_cookie)
        presented = request.headers.get("x-csrf-token", "")
        if not context or not re.fullmatch(r"[0-9a-f]{64}", presented):
            raise IdentityError(403, "CSRF_INVALIDO", "Actualiza la página y vuelve a intentarlo.")
        if not hmac.compare_digest(presented, self.signed_context(context, self.session_token(request))):
            raise IdentityError(403, "CSRF_INVALIDO", "Actualiza la página y vuelve a intentarlo.")

    def issue_csrf(self, request: Request, response: Response) -> str:
        context = self.cookie_value(request, self.csrf_cookie)
        if context is None:
            context = token_urlsafe(32)
            response.set_cookie(self.csrf_cookie, context, path=self.csrf_path, **self.cookie_flags)
        return self.signed_context(context, self.session_token(request))

    def clear_csrf(self, response: Response) -> None:
        response.delete_cookie(self.csrf_cookie, path=self.csrf_path, **self.cookie_flags)
