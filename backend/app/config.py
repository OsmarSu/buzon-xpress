from dataclasses import dataclass
from os import environ
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url


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
        sender = environ.get("BUZON_SMTP_FROM", "")
        smtp_host = environ.get("BUZON_SMTP_HOST", "")
        if smtp_host and not sender:
            raise RuntimeError("Configura BUZON_SMTP_FROM para habilitar el correo.")
        return cls(
            database_url=database_url(),
            session_secret=secret,
            allowed_origins=origins,
            public_origin=origins[0],
            secure_cookies=all(origin.startswith("https://") for origin in origins),
            smtp_host=smtp_host,
            smtp_port=int(environ.get("BUZON_SMTP_PORT", "587")),
            smtp_sender=sender,
            smtp_user=environ.get("BUZON_SMTP_USER", ""),
            smtp_password=environ.get("BUZON_SMTP_PASSWORD", ""),
            credential_key=credential_key,
            request_key=request_key,
            cors_origins=cors_origins,
        )
