from datetime import UTC, datetime, timedelta
import hmac
import json
from uuid import UUID, uuid4

from sqlalchemy import Connection, Engine, MetaData, Table, select
from sqlalchemy.dialects.postgresql import insert

from app.domain.identity import IdentityError


NOTICE = {
    "EN_CUSTODIA": "Custodia disponible en el punto",
    "RETIRADA": "Retiro confirmado",
    "DEVUELTA": "Devolución confirmada",
    "CANCELADA": "Custodia cancelada",
}


class OperationsStore:
    def __init__(self, engine: Engine, *, smtp_enabled: bool = False) -> None:
        self.engine = engine
        self.smtp_enabled = smtp_enabled
        self.metadata = MetaData()
        self.metadata.reflect(bind=engine, only=(
            "users", "sessions", "service_points", "staff_assignments", "storage_locations", "tariff_versions",
            "custody_orders", "storage_assignments", "pickup_credentials", "recovery_requests",
            "pickup_authorizations", "handovers", "custody_events", "notifications", "incidents",
            "service_payments", "idempotency_keys",
        ))

    def table(self, name: str) -> Table:
        return self.metadata.tables[name]

    def claim(self, conn: Connection, *, actor_id: UUID, operation: str, key: str, payload: dict, secret: bytes):
        keys = self.table("idempotency_keys")
        key_id, now = uuid4(), datetime.now(UTC)
        fingerprint = hmac.digest(
            secret, json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(), "sha256"
        ).hex()
        inserted = conn.execute(
            insert(keys).values(
                id=key_id, actor_id=actor_id, operation=operation, request_key=key,
                request_hash=fingerprint, state="EN_CURSO", expires_at=now + timedelta(days=1),
            ).on_conflict_do_nothing(index_elements=["actor_id", "operation", "request_key"]).returning(keys.c.id)
        ).scalar_one_or_none()
        if inserted:
            return inserted, None
        prior = conn.execute(select(keys).where(
            keys.c.actor_id == actor_id, keys.c.operation == operation, keys.c.request_key == key,
        ).with_for_update()).mappings().one()
        if not hmac.compare_digest(prior["request_hash"], fingerprint):
            raise IdentityError(409, "CLAVE_REUTILIZADA", "La clave ya se usó con una solicitud distinta.")
        if prior["expires_at"] <= now or prior["state"] != "COMPLETADA" or prior["result_resource_id"] is None:
            raise IdentityError(409, "CLAVE_NO_DISPONIBLE", "La clave está vencida o la operación sigue en curso.")
        return prior["id"], prior["result_resource_id"]

    def complete(self, conn: Connection, record_id: UUID, resource_id: UUID) -> None:
        keys = self.table("idempotency_keys")
        conn.execute(keys.update().where(keys.c.id == record_id).values(
            state="COMPLETADA", result_resource_id=resource_id,
        ))

    def event(
        self, conn: Connection, *, actor_id: UUID | None, point_id: UUID | None,
        custody_id: UUID | None = None, event_type: str, correlation_id: UUID,
        previous_state: str | None = None, new_state: str | None = None, payload: dict | None = None,
    ) -> UUID:
        event_id = uuid4()
        conn.execute(self.table("custody_events").insert().values(
            id=event_id, custody_id=custody_id, point_id=point_id, actor_id=actor_id,
            event_type=event_type, previous_state=previous_state, new_state=new_state,
            correlation_id=correlation_id, payload=payload or {},
        ))
        subject = NOTICE.get(new_state)
        if custody_id and subject and new_state != previous_state:
            self.notify(conn, custody_id=custody_id, event_id=event_id, subject=subject)
        return event_id

    def notify(self, conn: Connection, *, custody_id: UUID, event_id: UUID, subject: str) -> None:
        orders = self.table("custody_orders")
        sender, recipient = conn.execute(
            select(orders.c.sender_id, orders.c.recipient_id).where(orders.c.id == custody_id)
        ).one()
        notices = self.table("notifications")
        body = f"Consulta el detalle privado de la custodia en /#custodia={custody_id}."
        channels = ("BANDEJA", "CORREO") if self.smtp_enabled else ("BANDEJA",)
        rows = [
            {
                "id": uuid4(), "user_id": user_id, "custody_id": custody_id, "event_key": event_id,
                "channel": channel, "state": "PENDIENTE", "subject": subject, "body": body,
            }
            for user_id in {sender, recipient}
            for channel in channels
        ]
        conn.execute(insert(notices).values(rows).on_conflict_do_nothing(
            index_elements=["user_id", "event_key", "channel"]
        ))
