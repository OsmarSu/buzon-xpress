from dataclasses import dataclass
from os import environ
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url
from cryptography.fernet import Fernet


def database_url() -> str:
    url = environ.get("BUZON_DATABASE_URL", "")
    if not url or make_url(url).drivername != "postgresql+psycopg":
        raise RuntimeError("Configura BUZON_DATABASE_URL con postgresql+psycopg.")
    return url


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    session_secret: bytes
    allowed_origins: tuple[str, ...]
    public_origin: str
    secure_cookies: bool = True
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_sender: str = ""
    smtp_user: str = ""
    smtp_password: str = ""
    credential_key: bytes = b""
    request_key: bytes = b""
    cors_origins: tuple[str, ...] = ()
    mfa_encryption_key: bytes = b""
    mail_provider: str = "smtp"

    @classmethod
    def from_env(cls) -> "Settings":
        env = environ.get("BUZON_ENV", "piloto")
        origins = tuple(item.strip() for item in environ.get("BUZON_ALLOWED_ORIGINS", "").split(",") if item.strip())
        cors_origins = tuple(item.strip() for item in environ.get("BUZON_CORS_ORIGINS", "").split(",") if item.strip())
        secret = environ.get("BUZON_SESSION_SECRET", "").encode()
        if not origins or len(secret) < 32:
            raise RuntimeError("Configura BUZON_ALLOWED_ORIGINS y BUZON_SESSION_SECRET (al menos 32 bytes).")
        local = env in {"desarrollo", "pruebas"}
        for origin in origins:
            url = urlsplit(origin)
            is_local_http = local and url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1", "::1"}
            if not url.hostname or origin != f"{url.scheme}://{url.netloc}" or url.username is not None:
                raise RuntimeError("BUZON_ALLOWED_ORIGINS debe contener orígenes exactos sin ruta ni credenciales.")
            if url.scheme != "https" and not is_local_http:
                raise RuntimeError("Solo se permite HTTP de loopback en desarrollo y pruebas.")
        if len({urlsplit(origin).scheme for origin in origins}) != 1:
            raise RuntimeError("Separa los orígenes HTTP de desarrollo y HTTPS en entornos distintos.")
        if any(origin not in origins or not origin.startswith("https://") for origin in cors_origins):
            raise RuntimeError("BUZON_CORS_ORIGINS debe incluir solo orígenes HTTPS autorizados.")
        credential_key = environ.get("BUZON_CREDENTIAL_HMAC_KEY", "").encode()
        request_key = environ.get("BUZON_REQUEST_HMAC_KEY", "").encode()
        keys = (secret, credential_key, request_key)
        if not local and (any(len(key) < 32 for key in keys) or len(set(keys)) != len(keys)):
            raise RuntimeError("Configura tres secretos distintos de al menos 32 bytes para el piloto.")
        if any(key and len(key) < 32 for key in (credential_key, request_key)):
            raise RuntimeError("Las claves HMAC configuradas requieren al menos 32 bytes.")
        mfa_key = environ.get("BUZON_MFA_ENCRYPTION_KEY", "").encode()
        if mfa_key:
            try:
                Fernet(mfa_key)
            except (ValueError, TypeError):
                raise RuntimeError("BUZON_MFA_ENCRYPTION_KEY debe ser una clave Fernet válida.") from None
            if mfa_key == secret:
                raise RuntimeError("La clave de cifrado MFA debe ser distinta del secreto de sesión.")
        elif not local:
            raise RuntimeError("Configura BUZON_MFA_ENCRYPTION_KEY para conservar el segundo factor de forma segura.")

        sender = environ.get("BUZON_SMTP_FROM", "").strip()
        smtp_host = environ.get("BUZON_SMTP_HOST", "").strip()
        smtp_user = environ.get("BUZON_SMTP_USER", "").strip()
        smtp_password = environ.get("BUZON_SMTP_PASSWORD", "")
        provider = environ.get("BUZON_MAIL_PROVIDER", "smtp" if smtp_host else (
            "gmail" if smtp_user or smtp_password else "none"
        )).casefold()
        if provider not in {"gmail", "smtp", "none"}:
            raise RuntimeError("BUZON_MAIL_PROVIDER admite gmail, smtp o none.")
        smtp_port = int(environ.get("BUZON_SMTP_PORT", "587"))
        if provider == "gmail":
            smtp_password = smtp_password.replace(" ", "")
            if not smtp_user or "@" not in smtp_user or len(smtp_password) != 16 or not smtp_password.isascii() or not smtp_password.isalnum():
                raise RuntimeError("Gmail requiere BUZON_SMTP_USER y una contraseña de aplicación de 16 caracteres.")
            if sender and sender.casefold() != smtp_user.casefold():
                raise RuntimeError("En Gmail, BUZON_SMTP_FROM debe coincidir con BUZON_SMTP_USER.")
            if smtp_port not in {465, 587}:
                raise RuntimeError("Gmail usa el puerto 587 con STARTTLS o 465 con TLS directo.")
            smtp_host, sender = "smtp.gmail.com", smtp_user
        elif provider == "none":
            smtp_host, sender, smtp_user, smtp_password = "", "", "", ""
        if smtp_host and not sender:
            raise RuntimeError("Configura BUZON_SMTP_FROM para habilitar el correo.")
        return cls(
            database_url=database_url(),
            session_secret=secret,
            allowed_origins=origins,
            public_origin=origins[0],
            secure_cookies=all(origin.startswith("https://") for origin in origins),
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_sender=sender,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            credential_key=credential_key,
            request_key=request_key,
            cors_origins=cors_origins,
            mfa_encryption_key=mfa_key,
            mail_provider=provider,
        )
