"""MFA TOTP y recuperación con bloqueo transaccional por cuenta."""
import base64
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import hmac
from secrets import token_hex, token_urlsafe
from uuid import UUID, uuid4

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.engine import RowMapping

from app.adapters.storage.identity import IdentityStore
from app.application.identity import IdentityService, SESSION_TTL, MOBILE_SESSION_PREFIX, token_hash, invalid_session
from app.config import Settings
from app.domain.identity import IdentityError
from app.domain.mfa import accepted_counter, enrollment_uri, new_secret, normalize_recovery_code

CHALLENGE_TTL = timedelta(minutes=5)
MOBILE_CHALLENGE_PREFIX = "mfc_"
SETUP_TTL = timedelta(minutes=10)
LOCK_TTL = timedelta(minutes=5)


def rejected_factor() -> IdentityError:
    return IdentityError(401, "MFA_INVALIDO", "Código inválido, ya utilizado o vencido. Usa el siguiente código o uno de recuperación.")


def rejected_challenge() -> IdentityError:
    return IdentityError(401, "DESAFIO_MFA_INVALIDO", "La comprobación de acceso venció o ya se utilizó. Inicia sesión de nuevo.")


class MfaService:
    def __init__(self, identity: IdentityService, settings: Settings):
        self.identity = identity
        self.store: IdentityStore = identity.store
        key = settings.mfa_encryption_key or base64.urlsafe_b64encode(
            hmac.digest(settings.session_secret, b"mfa-encryption-v1", sha256)
        )
        self.cipher = Fernet(key)
        self.recovery_key = hmac.digest(key, b"mfa-recovery-v1", sha256)

    def _encrypt(self, secret: str) -> str:
        return self.cipher.encrypt(secret.encode("ascii")).decode("ascii")

    def _decrypt(self, ciphertext: str) -> str:
        try:
            return self.cipher.decrypt(ciphertext.encode("ascii")).decode("ascii")
        except (InvalidToken, ValueError, UnicodeError):
            raise IdentityError(503, "MFA_NO_DISPONIBLE", "No se puede comprobar el segundo factor. Contacta al responsable del servicio.") from None

    @staticmethod
    def _available(user: RowMapping, now: datetime) -> None:
        if user["mfa_locked_until"] is not None and user["mfa_locked_until"] > now:
            raise IdentityError(429, "LIMITE_MFA", "Espera cinco minutos antes de volver a comprobar el segundo factor.")

    def _failure(self, connection, user: RowMapping, now: datetime) -> None:
        expired = user["mfa_locked_until"] is not None and user["mfa_locked_until"] <= now
        count = min(5, (0 if expired else user["mfa_failed_attempts"]) + 1)
        self.store.update_user(connection, user["id"], {
            "mfa_failed_attempts": count, "mfa_locked_until": now + LOCK_TTL if count >= 5 else None,
        })

    def _recovery_digest(self, code: str) -> str:
        return hmac.new(self.recovery_key, code.encode("ascii"), sha256).hexdigest()

    def _new_recovery_codes(self, connection, user_id: UUID) -> list[str]:
        raw = [token_hex(16).upper() for _ in range(10)]
        self.store.replace_recovery_codes(connection, user_id, [self._recovery_digest(x) for x in raw])
        return ["-".join(code[i:i+8] for i in range(0, 32, 8)) for code in raw]

    def _factor(self, connection, user: RowMapping, code: str, now: datetime) -> bool:
        counter = accepted_counter(
            self._decrypt(user["mfa_secret_ciphertext"]), code.strip(), now.timestamp(),
            user["mfa_last_counter"] if user["mfa_last_counter"] is not None else -1,
        )
        if counter is not None:
            self.store.update_user(connection, user["id"], {"mfa_last_counter": counter})
            return True
        recovery = normalize_recovery_code(code)
        return bool(recovery and self.store.consume_recovery_code(
            connection, user["id"], self._recovery_digest(recovery),
        ))

    def begin_login(self, user: RowMapping, previous_token: str | None, *, mobile: bool = False) -> dict:
        now = datetime.now(UTC)
        token = (MOBILE_CHALLENGE_PREFIX if mobile else "") + token_urlsafe(32)
        with self.store.transaction() as connection:
            locked = self.store.lock_user(connection, user["id"])
            if locked is None or locked["password_hash"] != user["password_hash"] or not locked["mfa_enabled"]:
                raise rejected_challenge()
            self._available(locked, now)
            self.store.add_mfa_challenge(connection, {
                "id": uuid4(), "user_id": user["id"], "token_hash": token_hash(token),
                "expires_at": now + CHALLENGE_TTL, "mfa_version": locked["mfa_version"],
                "previous_session_hash": token_hash(previous_token) if previous_token else None,
            })
        return {"mfa_required": True, "challenge_token": token, "expires_at": now + CHALLENGE_TTL}

    def verify_login(self, challenge_token: str, code: str, *, mobile: bool = False) -> tuple[RowMapping, str, datetime]:
        native_challenge = len(challenge_token) == 47 and challenge_token.startswith(MOBILE_CHALLENGE_PREFIX)
        if native_challenge != mobile:
            raise rejected_challenge()
        now = datetime.now(UTC)
        digest = token_hash(challenge_token)
        error = None
        result = None
        with self.store.transaction() as connection:
            user = self.store.lock_challenge_user(connection, digest)
            challenge = self.store.mfa_challenge(connection, digest) if user else None
            if (not user or not challenge or not user["mfa_enabled"] or challenge["used_at"] is not None
                    or challenge["expires_at"] <= now or challenge["attempts"] >= 5
                    or challenge["mfa_version"] != user["mfa_version"]):
                raise rejected_challenge()
            self._available(user, now)
            if not self._factor(connection, user, code, now):
                self._failure(connection, user, now)
                self.store.update_mfa_challenge(connection, challenge["id"], {"attempts": challenge["attempts"] + 1})
                error = rejected_factor()
            else:
                token = (MOBILE_SESSION_PREFIX if mobile else "") + token_urlsafe(32)
                expires_at = now + SESSION_TTL
                self.store.insert_session(connection, {
                    "id": uuid4(), "user_id": user["id"], "token_hash": token_hash(token), "expires_at": expires_at,
                }, challenge["previous_session_hash"], now)
                self.store.update_mfa_challenge(connection, challenge["id"], {"used_at": now})
                self.store.update_user(connection, user["id"], {"mfa_failed_attempts": 0, "mfa_locked_until": None})
                result = (user, token, expires_at)
        if error:
            raise error
        assert result is not None
        return result

    def status(self, actor: RowMapping) -> dict:
        return {"enabled": bool(actor["mfa_enabled"]), "recovery_codes_remaining": self.store.recovery_count(actor["id"])}

    def begin_setup(self, actor: RowMapping, password: str) -> dict:
        now = datetime.now(UTC)
        secret = new_secret()
        with self.store.transaction() as connection:
            user = self.store.lock_user(connection, actor["id"])
            if user is None:
                raise invalid_session()
            if not self.identity.passwords.verify(password, user["password_hash"]):
                raise IdentityError(401, "CREDENCIALES_INVALIDAS", "La contraseña no es correcta.")
            self._available(user, now)
            if user["contact_verified_at"] is None:
                raise IdentityError(403, "CONTACTO_NO_VERIFICADO", "Comprueba tu correo o contacto antes de activar el segundo factor.")
            if user["mfa_enabled"]:
                raise IdentityError(409, "MFA_YA_ACTIVO", "El segundo factor ya está activo.")
            self.store.update_user(connection, user["id"], {
                "mfa_pending_secret_ciphertext": self._encrypt(secret), "mfa_pending_expires_at": now + SETUP_TTL,
            })
        return {"secret": secret, "otpauth_uri": enrollment_uri(secret, user["email"]), "expires_at": now + SETUP_TTL}

    def confirm_setup(self, actor: RowMapping, code: str, session_token: str) -> dict:
        now = datetime.now(UTC)
        error = None
        codes = []
        with self.store.transaction() as connection:
            user = self.store.lock_user(connection, actor["id"])
            if user is None:
                raise invalid_session()
            self._available(user, now)
            if user["mfa_enabled"]:
                raise IdentityError(409, "MFA_YA_ACTIVO", "El segundo factor ya está activo.")
            if (not user["mfa_pending_secret_ciphertext"] or not user["mfa_pending_expires_at"]
                    or user["mfa_pending_expires_at"] <= now):
                raise IdentityError(400, "CONFIGURACION_MFA_VENCIDA", "Inicia de nuevo la configuración del segundo factor.")
            counter = accepted_counter(self._decrypt(user["mfa_pending_secret_ciphertext"]), code.strip(), now.timestamp())
            if counter is None:
                self._failure(connection, user, now)
                error = rejected_factor()
            else:
                self.store.update_user(connection, user["id"], {
                    "mfa_enabled": True, "mfa_secret_ciphertext": user["mfa_pending_secret_ciphertext"],
                    "mfa_pending_secret_ciphertext": None, "mfa_pending_expires_at": None,
                    "mfa_last_counter": counter, "mfa_failed_attempts": 0, "mfa_locked_until": None,
                    "mfa_version": user["mfa_version"] + 1,
                })
                codes = self._new_recovery_codes(connection, user["id"])
                self.store.revoke_other_sessions(connection, user["id"], token_hash(session_token), now)
                self.store.delete_mfa_challenges(connection, user["id"])
        if error:
            raise error
        return {"enabled": True, "recovery_codes": codes}

    def manage(self, actor: RowMapping, password: str, code: str, session_token: str, *, disable: bool) -> dict:
        now = datetime.now(UTC)
        error = None
        codes = []
        with self.store.transaction() as connection:
            user = self.store.lock_user(connection, actor["id"])
            if user is None:
                raise invalid_session()
            if not self.identity.passwords.verify(password, user["password_hash"]):
                raise IdentityError(401, "CREDENCIALES_INVALIDAS", "La contraseña no es correcta.")
            self._available(user, now)
            if not user["mfa_enabled"]:
                raise IdentityError(409, "MFA_NO_ACTIVO", "El segundo factor no está activo.")
            if not self._factor(connection, user, code, now):
                self._failure(connection, user, now)
                error = rejected_factor()
            else:
                changes = {"mfa_failed_attempts": 0, "mfa_locked_until": None, "mfa_version": user["mfa_version"] + 1}
                if disable:
                    changes.update({
                        "mfa_enabled": False, "mfa_secret_ciphertext": None, "mfa_pending_secret_ciphertext": None,
                        "mfa_pending_expires_at": None, "mfa_last_counter": None,
                    })
                    self.store.replace_recovery_codes(connection, user["id"], [])
                else:
                    codes = self._new_recovery_codes(connection, user["id"])
                self.store.update_user(connection, user["id"], changes)
                self.store.revoke_other_sessions(connection, user["id"], token_hash(session_token), now)
                self.store.delete_mfa_challenges(connection, user["id"])
        if error:
            raise error
        return {"id": actor["id"], "state": "DESACTIVADA"} if disable else {"enabled": True, "recovery_codes": codes}
