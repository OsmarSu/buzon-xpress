from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import InterfaceError, OperationalError
from starlette.exceptions import HTTPException

from app.adapters.api.admin import admin_router
from app.adapters.api.auth import auth_router
from app.adapters.api.custody import custody_router
from app.adapters.api.dto import Error, Health
from app.adapters.api.in_person import in_person_router
from app.adapters.api.notifications import notifications_router
from app.adapters.api.pickup import pickup_router
from app.adapters.api.recovery import recovery_router
from app.adapters.api.security import API_PATH, ApiSecurity
from app.adapters.mail.smtp import SmtpIdentityMail
from app.adapters.storage.identity import IdentityStore
from app.adapters.storage.operations import OperationsStore
from app.application.identity import IdentityService
from app.config import Settings
from app.domain.identity import IdentityError
from app.ports.mail import IdentityMail, MailUnavailable


def create_app(settings: Settings | None = None, *, mail: IdentityMail | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    store = IdentityStore(settings.database_url)
    service = IdentityService(store, mail if mail is not None else (
        SmtpIdentityMail(settings) if settings.smtp_host else None
    ))

    operations = OperationsStore(store.engine, smtp_enabled=bool(settings.smtp_host))
    security = ApiSecurity(service, settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            store.engine.dispose()

    app = FastAPI(title="BUZON Xpress", version="0.1.0", lifespan=lifespan)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH"],
            allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key"],
            expose_headers=["X-Correlation-ID"],
        )
    app.include_router(auth_router(service, settings), prefix=API_PATH)
    for router in (in_person_router, custody_router, admin_router, recovery_router, notifications_router, pickup_router):
        app.include_router(router(operations, security), prefix=API_PATH)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.correlation_id = uuid4()
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = str(request.state.correlation_id)
        if request.url.path.startswith(f"{API_PATH}/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    def failure(request: Request, status: int, code: str, message: str) -> JSONResponse:
        error = Error(code=code, message=message, correlation_id=request.state.correlation_id)
        return JSONResponse(error.model_dump(mode="json"), status_code=status)

    @app.exception_handler(IdentityError)
    async def identity_error(request: Request, error: IdentityError):
        return failure(request, error.status, error.code, error.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _error: RequestValidationError):
        return failure(request, 422, "PETICION_INVALIDA", "Revisa los campos enviados.")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        return failure(request, error.status_code, "PETICION_RECHAZADA", "No se pudo atender la petición.")

    @app.exception_handler(OperationalError)
    @app.exception_handler(InterfaceError)
    async def database_error(request: Request, _error):
        return failure(request, 503, "BASE_NO_DISPONIBLE", "La base de datos no está disponible.")

    @app.exception_handler(MailUnavailable)
    async def mail_error(request: Request, _error: MailUnavailable):
        return failure(request, 503, "CORREO_NO_DISPONIBLE", "No se pudo enviar el enlace. Vuelve a intentarlo.")

    @app.get(f"{API_PATH}/health", response_model=Health, tags=["Servicio"])
    def health() -> Health:
        with store.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return Health(status="OK", database_checked=True)

    return app
