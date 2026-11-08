from datetime import UTC, datetime, timedelta
from hashlib import sha256
from logging import getLogger
from secrets import token_urlsafe
from uuid import UUID, uuid4

from pwdlib import PasswordHash
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError

from app.adapters.storage.identity import IdentityStore
from app.domain.identity import IdentityError, Role
from app.ports.mail import IdentityMail, MailUnavailable


SESSION_TTL = timedelta(hours=8)
VERIFICATION_TTL = timedelta(minutes=30)
RESET_TTL = timedelta(minutes=30)
log = getLogger(__name__)


def token_hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def invalid_session() -> IdentityError:
    return IdentityError(401, "SESION_INVALIDA", "La sesión falta, expiró o fue revocada.")


class IdentityService:
    def __init__(self, store: IdentityStore, mail: IdentityMail | None) -> None:
        self.store = store
        self.mail = mail
        self.passwords = PasswordHash.recommended()
        self.dummy_hash = self.passwords.hash(token_urlsafe(32))

    def register(self, email: str, full_name: str, password: str, phone: str | None) -> RowMapping:
        token = token_urlsafe(32) if self.mail is not None else None
        values = {
            "id": uuid4(),
            "email": email.casefold(),
            "full_name": full_name,
            "phone": phone,
            "password_hash": self.passwords.hash(password),
            "role": Role.USUARIO.value,
            "contact_verification_hash": token_hash(token) if token else None,
            "verification_expires_at": datetime.now(UTC) + VERIFICATION_TTL if token else None,
        }
        with self.store.transaction() as connection:
            user = self.store.add_user(connection, values)
            if user is None:
                raise IdentityError(409, "REGISTRO_NO_DISPONIBLE", "No se pudo registrar esa cuenta.")
            if self.mail is not None and token:
                self.mail.verify_contact(values["email"], token)
        return user

    def login(self, email: str, password: str, previous_token: str | None) -> tuple[RowMapping, str, datetime]:
        user = self.store.find_active_user(email.casefold())
        valid = self.passwords.verify(password, user["password_hash"] if user is not None else self.dummy_hash)
        if user is None or not valid:
            raise IdentityError(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos.")
        token = token_urlsafe(32)
        now = datetime.now(UTC)
        expires_at = now + SESSION_TTL
        values = {"id": uuid4(), "user_id": user["id"], "token_hash": token_hash(token), "expires_at": expires_at}
        if not self.store.add_session(user, values, token_hash(previous_token) if previous_token else None, now):
            raise IdentityError(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos.")
        return user, token, expires_at

    def current_user(self, token: str | None) -> RowMapping:
        if not token:
            raise invalid_session()
        user = self.store.current_user(token_hash(token), datetime.now(UTC))
        if user is None:
            raise invalid_session()
        return user

    def logout(self, token: str | None) -> UUID:
        if not token:
            raise invalid_session()
        session_id = self.store.revoke_session(token_hash(token), datetime.now(UTC))
        if session_id is None:
            raise invalid_session()
        return session_id

    def verify_contact(self, token: str) -> UUID:
        user_id = self.store.verify_contact(token_hash(token), datetime.now(UTC))
        if user_id is None:
            raise IdentityError(400, "ENLACE_INVALIDO", "El enlace es inválido, venció o ya se utilizó.")
        return user_id

    def request_password_reset(self, email: str) -> None:
        if self.mail is None:
            return
        email = email.casefold()
        token = token_urlsafe(32)
        try:
            with self.store.transaction() as connection:
                if self.store.set_password_reset(
                    connection, email, token_hash(token), datetime.now(UTC) + RESET_TTL
                ):
                    self.mail.password_reset(email, token)
        except (MailUnavailable, SQLAlchemyError):
            # The public response is independent of the account and channel.
            log.warning("No se pudo procesar una solicitud de recuperación.")

    def complete_password_reset(self, token: str, password: str) -> UUID:
        with self.store.transaction() as connection:
            now = datetime.now(UTC)
            user_id = self.store.lock_reset_user(connection, token_hash(token), now)
            if user_id is None:
                raise IdentityError(400, "ENLACE_INVALIDO", "El enlace es inválido, venció o ya se utilizó.")
            self.store.replace_password(connection, user_id, self.passwords.hash(password), now)
        return user_id

    def require_point_access(self, actor: RowMapping, point_id: UUID, allowed_roles: frozenset[Role]) -> None:
        if actor["role"] not in allowed_roles or not self.store.has_active_assignment(actor["id"], point_id):
            raise IdentityError(403, "PUNTO_NO_AUTORIZADO", "La cuenta no tiene acceso a ese punto.")
