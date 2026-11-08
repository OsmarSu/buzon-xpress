from datetime import UTC, datetime, timedelta
from hashlib import sha256
import hmac
import re
from secrets import randbelow
from uuid import UUID, uuid4

from sqlalchemy import case, func, select

from app.adapters.storage.operations import OperationsStore
from app.application.exceptions import ExceptionsService, conflict
from app.application.operations_access import find, projected
from app.domain.identity import IdentityError

CREDENTIAL_TTL = timedelta(minutes=15)
AUTHORIZATION_TTL = timedelta(minutes=2)
MAX_FAILED_ATTEMPTS = 5
CUSTODY_FIELDS = (
    "id", "tracking_number", "state", "point_id", "description", "size_category", "version", "received_at", "due_at",
)


def custody_view(order) -> dict:
    return {**projected(order, CUSTODY_FIELDS), "service_total": f"{order['service_total']:.2f}"}


def verifier(secret: bytes, custody_id: UUID, code: str) -> str:
    return hmac.new(secret, f"retiro-v1:{custody_id}:{code}".encode("ascii"), sha256).hexdigest()


def rejected_credential(status: int) -> IdentityError:
    if status == 429:
        return IdentityError(429, "CREDENCIAL_BLOQUEADA", "La credencial está bloqueada temporalmente.")
    return IdentityError(400, "CREDENCIAL_INVALIDA", "La credencial es inválida, venció o ya no está disponible.")


class PickupService:
    def __init__(self, store: OperationsStore, credential_key: bytes) -> None:
        self.store = store
        self.credential_key = credential_key
        self.workflow = ExceptionsService(store)
        self.orders = self.workflow.orders
        self.credentials = self.workflow.credentials
        self.authorizations = self.workflow.authorizations
        self.recoveries = self.workflow.recovery

    def ensure_clear(self, conn, order_id):
        self.workflow.ensure_no_blocking_issue(conn, order_id)
        pending = conn.execute(select(self.recoveries.c.id).where(
            self.recoveries.c.custody_id == order_id,
            self.recoveries.c.state.in_(("PENDIENTE", "APROBADA")),
        ).limit(1)).scalar_one_or_none()
        if pending is not None:
            raise conflict("Resuelve el expediente de recuperación antes del retiro ordinario.")

    def check_recipient(self, conn, order, operator_id=None):
        recipient = find(conn, self.store, "users", order["recipient_id"])
        if not recipient["is_active"] or recipient["contact_verified_at"] is None:
            raise conflict("El destinatario debe tener cuenta activa y contacto comprobado.")
        if recipient["id"] == operator_id:
            raise IdentityError(403, "OPERADOR_ES_DESTINATARIO", "Otro operador debe verificar al destinatario.")

    def check_balance(self, conn, order):
        payments = self.store.table("service_payments")
        signed_amount = case((payments.c.kind == "REEMBOLSO", -payments.c.amount), else_=payments.c.amount)
        paid = conn.execute(select(func.coalesce(func.sum(signed_amount), 0)).where(
            payments.c.custody_id == order["id"], payments.c.state == "REGISTRADO",
        )).scalar_one()
        if order["received_at"] is None or paid < order["service_total"]:
            raise conflict("Concilia el saldo del servicio antes de preparar o confirmar el retiro.")

    def current_credential(self, conn, order_id):
        return conn.execute(select(self.credentials).where(
            self.credentials.c.custody_id == order_id,
            self.credentials.c.state.in_(("ACTIVA", "RETENIDA")),
        ).with_for_update()).mappings().one_or_none()

    def issue(self, conn, actor, order, reissue: bool, correlation):
        if actor["id"] != order["recipient_id"]:
            raise IdentityError(404, "CUSTODIA_NO_VISIBLE", "La custodia no está disponible para esa operación.")
        if order["state"] != "EN_CUSTODIA":
            raise conflict("La custodia debe estar disponible para emitir una credencial.")
        self.check_recipient(conn, order)
        self.ensure_clear(conn, order["id"])
        self.workflow.location_for(conn, order["id"])
        old = self.current_credential(conn, order["id"])
        now = datetime.now(UTC)
        carry_failures = 0
        if old is not None:
            if old["state"] == "RETENIDA":
                raise conflict("Resuelve la preparación de retiro antes de reemitir.")
            if old["blocked_until"] is not None and old["blocked_until"] > now:
                raise rejected_credential(429)
            if not reissue and old["expires_at"] > now:
                raise conflict("Existe una credencial activa. Confirma la reemisión para revocarla.")
            if old["expires_at"] > now and old["blocked_until"] is None:
                carry_failures = old["failed_attempts"]
            conn.execute(self.credentials.update().where(self.credentials.c.id == old["id"]).values(state="REVOCADA"))
        code = f"{randbelow(1_000_000):06d}"
        while old is not None and hmac.compare_digest(old["verifier"], verifier(self.credential_key, order["id"], code)):
            code = f"{randbelow(1_000_000):06d}"
        credential_id, expires_at = uuid4(), now + CREDENTIAL_TTL
        conn.execute(self.credentials.insert().values(
            id=credential_id, custody_id=order["id"], verifier=verifier(self.credential_key, order["id"], code),
            state="ACTIVA", failed_attempts=carry_failures, expires_at=expires_at,
        ))
        self.workflow.audit(conn, actor, order, "CREDENCIAL_EMITIDA", correlation, payload={"reemision": old is not None})
        return {"credential_id": credential_id, "code": code, "expires_at": expires_at}

    def verify(self, conn, actor, order, body, correlation, record_id):
        if order["state"] != "EN_CUSTODIA" or order["version"] != body.expected_version:
            raise conflict("Actualiza la custodia antes de verificar el retiro.")
        self.check_recipient(conn, order, actor["id"])
        self.ensure_clear(conn, order["id"])
        self.check_balance(conn, order)
        self.workflow.location_for(conn, order["id"])
        now = datetime.now(UTC)
        credential = self.current_credential(conn, order["id"])
        blocked = credential is not None and credential["blocked_until"] is not None and credential["blocked_until"] > now
        valid = credential is not None and credential["state"] == "ACTIVA" and credential["expires_at"] > now
        if blocked or not valid:
            return self.save_rejection(conn, actor, order, correlation, record_id, 429 if blocked else 400)
        candidate = verifier(self.credential_key, order["id"], body.code.get_secret_value())
        if not hmac.compare_digest(credential["verifier"], candidate):
            attempts = credential["failed_attempts"] + 1
            reached_limit = attempts >= MAX_FAILED_ATTEMPTS
            conn.execute(self.credentials.update().where(self.credentials.c.id == credential["id"]).values(
                failed_attempts=attempts, blocked_until=now + CREDENTIAL_TTL if reached_limit else None,
            ))
            return self.save_rejection(conn, actor, order, correlation, record_id, 429 if reached_limit else 400)

        conn.execute(self.credentials.update().where(self.credentials.c.id == credential["id"]).values(state="RETENIDA"))
        auth = conn.execute(self.authorizations.insert().values(
            id=uuid4(), custody_id=order["id"], operator_id=actor["id"], credential_id=credential["id"],
            purpose="RETIRO", person_check=body.recipient_check, state="VALIDADA", expires_at=now + AUTHORIZATION_TTL,
        ).returning(*self.authorizations.c)).mappings().one()
        updated = conn.execute(self.orders.update().where(self.orders.c.id == order["id"]).values(
            state="RETIRO_EN_CURSO", version=order["version"] + 1,
        ).returning(*self.orders.c)).mappings().one()
        self.workflow.audit(conn, actor, order, "RETIRO_PREPARADO", correlation, new_state="RETIRO_EN_CURSO", payload={
            "authorization_id": str(auth["id"]),
        })
        self.store.complete(conn, record_id, auth["id"])
        return self.workflow.return_view(conn, updated, auth)

    def save_rejection(self, conn, actor, order, correlation, record_id, status):
        event = self.workflow.audit(
            conn, actor, order, "VERIFICACION_RECHAZADA", correlation, payload={"status": status},
        )
        self.store.complete(conn, record_id, event)
        return rejected_credential(status)

    def retry_verification(self, conn, actor, order, prior_id):
        events = self.store.table("custody_events")
        rejected = conn.execute(select(events.c.payload).where(
            events.c.id == prior_id, events.c.custody_id == order["id"], events.c.event_type == "VERIFICACION_RECHAZADA",
        )).scalar_one_or_none()
        if rejected is not None:
            return rejected_credential(rejected["status"])
        auth = find(conn, self.store, "pickup_authorizations", prior_id)
        if auth["custody_id"] != order["id"] or auth["operator_id"] != actor["id"] or order["state"] != "RETIRO_EN_CURSO":
            raise conflict("La autorización original ya no está pendiente.")
        self.ensure_clear(conn, order["id"])
        return self.workflow.return_view(conn, order, auth)

    def authorize_actor(self, auth, actor, order):
        if auth["custody_id"] != order["id"] or auth["operator_id"] != actor["id"]:
            raise IdentityError(403, "AUTORIZACION_NO_VISIBLE", "El operador debe usar su propia autorización.")

    def confirm(self, conn, actor, order, body, correlation):
        if order["state"] != "RETIRO_EN_CURSO" or order["version"] != body.expected_version:
            raise conflict("La preparación cambió o la entrega ya se confirmó.")
        auth = find(conn, self.store, "pickup_authorizations", body.authorization_id, lock=True)
        self.authorize_actor(auth, actor, order)
        if auth["purpose"] != "RETIRO" or auth["state"] != "VALIDADA" or auth["expires_at"] <= datetime.now(UTC):
            raise conflict("La autorización venció o ya no está vigente. Si entregaste, abre una conciliación.")
        credential = find(conn, self.store, "pickup_credentials", auth["credential_id"], lock=True)
        if credential["state"] != "RETENIDA":
            raise conflict("La credencial no está retenida para este retiro.")
        self.check_recipient(conn, order, actor["id"])
        self.ensure_clear(conn, order["id"])
        self.check_balance(conn, order)
        return self.workflow.complete_handover(conn, actor, order, auth, correlation)

    def abort(self, conn, actor, order, body, correlation):
        auth = find(conn, self.store, "pickup_authorizations", body.authorization_id, lock=True)
        self.authorize_actor(auth, actor, order)
        expected = "RETIRO_EN_CURSO" if auth["purpose"] == "RETIRO" else "DEVOLUCION_EN_CURSO"
        if auth["state"] != "VALIDADA" or order["state"] != expected:
            raise conflict("La preparación ya no se puede anular.")
        disputed = conn.execute(select(self.recoveries.c.id).where(
            self.recoveries.c.custody_id == order["id"], self.recoveries.c.purpose == "RECONCILIAR_ENTREGA",
            self.recoveries.c.state == "PENDIENTE",
        ).limit(1)).scalar_one_or_none()
        if disputed is not None:
            raise conflict("Resuelve la conciliación pendiente antes de anular la preparación.")
        conn.execute(self.authorizations.update().where(self.authorizations.c.id == auth["id"]).values(state="ANULADA"))
        self.workflow.revoke_credentials(conn, order["id"])
        updated = conn.execute(self.orders.update().where(self.orders.c.id == order["id"]).values(
            state="EN_CUSTODIA", version=order["version"] + 1,
        ).returning(*self.orders.c)).mappings().one()
        reason = re.sub(r"\b(?:[0-9]{6}|[A-Za-z0-9_-]{43})\b", "[dato omitido]", body.reason)
        self.workflow.audit(conn, actor, order, "PREPARACION_ANULADA", correlation, new_state="EN_CUSTODIA", payload={
            "authorization_id": str(auth["id"]), "reason": reason,
        })
        return custody_view(updated)
