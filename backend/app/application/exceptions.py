from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import Connection, select
from sqlalchemy.engine import RowMapping

from app.adapters.storage.operations import OperationsStore
from app.application.operations_access import find, projected, require_scope
from app.domain.identity import IdentityError, Role

MANAGERS = frozenset({Role.ADMIN})
OPERATORS = frozenset({Role.OPERADOR})
PERSONNEL = frozenset({Role.OPERADOR, Role.ADMIN})
IN_FLIGHT = ("RETIRO_EN_CURSO", "DEVOLUCION_EN_CURSO")
INCIDENT_FIELDS = ("id", "custody_id", "state", "is_blocking")
RECOVERY_FIELDS = ("id", "custody_id", "state")
HANDOVER_FIELDS = ("id", "custody_id", "kind", "confirmed_at", "operator_id")
ADVISORY_INCIDENTS = {"CONSULTA", "OBSERVACION"}
PURPOSE_STATES = {
    "REEMITIR_CREDENCIAL": ("EN_CUSTODIA",),
    "CAMBIAR_DESTINATARIO": ("REGISTRADA", "EN_CUSTODIA"),
    "AUTORIZAR_DEVOLUCION": ("EN_CUSTODIA",),
    "RECONCILIAR_ENTREGA": IN_FLIGHT,
}


def conflict(message: str) -> IdentityError:
    return IdentityError(409, "ESTADO_EN_CONFLICTO", message)


class ExceptionsService:
    def __init__(self, store: OperationsStore) -> None:
        self.store = store
        self.orders = store.table("custody_orders")
        self.issues = store.table("incidents")
        self.recovery = store.table("recovery_requests")
        self.credentials = store.table("pickup_credentials")
        self.authorizations = store.table("pickup_authorizations")
        self.handovers = store.table("handovers")
        self.assignments = store.table("storage_assignments")
        self.locations = store.table("storage_locations")

    def scope(self, conn: Connection, actor: RowMapping, order: RowMapping, *, participants: bool = False) -> None:
        if participants and actor["id"] in (order["sender_id"], order["recipient_id"]):
            return
        require_scope(conn, self.store, actor, order["point_id"], PERSONNEL)

    def audit(self, conn, actor, order, event, correlation, *, new_state=None, payload=None):
        return self.store.event(
            conn, actor_id=actor["id"], point_id=order["point_id"], custody_id=order["id"],
            event_type=event, correlation_id=correlation, previous_state=order["state"],
            new_state=new_state, payload=payload,
        )

    def record_incident(self, conn, actor, order, body, correlation):
        blocking = body["is_blocking"] or body["kind"] not in ADVISORY_INCIDENTS
        issue = conn.execute(self.issues.insert().values(
            id=uuid4(), custody_id=order["id"], opened_by=actor["id"], kind=body["kind"],
            description=body["description"], is_blocking=blocking, state="ABIERTA",
        ).returning(*self.issues.c)).mappings().one()
        event = self.audit(conn, actor, order, "INCIDENCIA_ABIERTA", correlation, payload={
            "incident_id": str(issue["id"]), "blocking": blocking,
        })
        self.store.notify(conn, custody_id=order["id"], event_id=event, subject="Incidencia registrada")
        return issue

    def resolve_incident(self, conn, actor, order, issue, reason, correlation):
        if issue["state"] == "RESUELTA":
            raise conflict("La incidencia ya fue resuelta.")
        if issue["is_blocking"] and issue["opened_by"] == actor["id"]:
            raise IdentityError(403, "DOBLE_CONTROL_REQUERIDO", "Otro administrador debe resolver esta incidencia.")
        row = conn.execute(self.issues.update().where(self.issues.c.id == issue["id"]).values(
            state="RESUELTA", resolved_by=actor["id"], resolved_at=datetime.now(UTC), resolution_note=reason,
        ).returning(*self.issues.c)).mappings().one()
        self.audit(conn, actor, order, "INCIDENCIA_RESUELTA", correlation, payload={"incident_id": str(issue["id"])})
        return row

    def validate_recipient(self, conn, order, target_id):
        if target_id is None or target_id in (order["sender_id"], order["recipient_id"]):
            raise IdentityError(422, "DESTINATARIO_INVALIDO", "Indica otro destinatario distinto del emisor.")
        target = find(conn, self.store, "users", target_id)
        if not target["is_active"] or target["contact_verified_at"] is None:
            raise conflict("El nuevo destinatario debe estar activo y comprobado.")

    def active_authorization(self, conn, order_id):
        query = select(self.authorizations).where(
            self.authorizations.c.custody_id == order_id, self.authorizations.c.state == "VALIDADA",
        ).with_for_update()
        authorization = conn.execute(query).mappings().one_or_none()
        if authorization is None:
            raise conflict("La custodia carece de autorización pendiente para conciliar.")
        return authorization

    def create_recovery(self, conn, actor, order, body, correlation):
        purpose = body["purpose"]
        if order["state"] not in PURPOSE_STATES[purpose]:
            raise conflict("El estado de la custodia no admite la excepción solicitada.")
        exists = conn.execute(select(self.recovery.c.id).where(
            self.recovery.c.custody_id == order["id"], self.recovery.c.purpose == purpose,
            self.recovery.c.state.in_(("PENDIENTE", "APROBADA")),
        ).limit(1)).scalar_one_or_none()
        if exists:
            raise conflict("Ya existe un expediente abierto para ese propósito.")
        target_id = body["target_recipient_id"]
        changes = {}
        if purpose == "CAMBIAR_DESTINATARIO":
            self.validate_recipient(conn, order, target_id)
            changes["target_recipient_id"] = str(target_id)
        elif target_id is not None:
            raise IdentityError(422, "DESTINATARIO_INESPERADO", "Este propósito no admite un nuevo destinatario.")
        if purpose == "RECONCILIAR_ENTREGA":
            authorization = self.active_authorization(conn, order["id"])
            changes["authorization_id"] = str(authorization["id"])
        row = conn.execute(self.recovery.insert().values(
            id=uuid4(), custody_id=order["id"], purpose=purpose, evidence=body["evidence"],
            requested_changes=changes, requested_by=actor["id"], state="PENDIENTE",
        ).returning(*self.recovery.c)).mappings().one()
        self.audit(conn, actor, order, "RECUPERACION_SOLICITADA", correlation, payload={
            "recovery_id": str(row["id"]), "purpose": purpose,
        })
        return row

    def revoke_credentials(self, conn, order_id):
        conn.execute(self.credentials.update().where(
            self.credentials.c.custody_id == order_id, self.credentials.c.state.in_(("ACTIVA", "RETENIDA")),
        ).values(state="REVOCADA"))

    def decide(self, conn, actor, order, recovery, body, correlation):
        if recovery["requested_by"] == actor["id"]:
            raise IdentityError(403, "DOBLE_CONTROL_REQUERIDO", "Otra persona debe decidir sobre la excepción.")
        if recovery["state"] != "PENDIENTE":
            raise conflict("El expediente ya fue decidido.")
        decision = "RECHAZADA"
        purpose = recovery["purpose"]
        if body["decision"] == "APROBAR":
            if order["state"] not in PURPOSE_STATES[purpose]:
                raise conflict("El estado de la custodia cambió desde la solicitud.")
            decision = "APROBADA"
            if purpose == "RECONCILIAR_ENTREGA":
                authorization = self.active_authorization(conn, order["id"])
                if str(authorization["id"]) != recovery["requested_changes"].get("authorization_id"):
                    raise conflict("La autorización original ya no está pendiente.")
                self.complete_handover(conn, actor, order, authorization, correlation, reconciliation=recovery["id"])
                decision = "EJECUTADA"
            elif purpose in ("REEMITIR_CREDENCIAL", "CAMBIAR_DESTINATARIO"):
                fields = {"version": order["version"] + 1}
                if purpose == "CAMBIAR_DESTINATARIO":
                    target_id = UUID(recovery["requested_changes"]["target_recipient_id"])
                    self.validate_recipient(conn, order, target_id)
                    fields["recipient_id"] = target_id
                self.revoke_credentials(conn, order["id"])
                conn.execute(self.orders.update().where(self.orders.c.id == order["id"]).values(**fields))
                decision = "EJECUTADA"
        updated = conn.execute(self.recovery.update().where(self.recovery.c.id == recovery["id"]).values(
            state=decision, decision_note=body["note"], decided_by=actor["id"], decided_at=datetime.now(UTC),
        ).returning(*self.recovery.c)).mappings().one()
        self.audit(conn, actor, order, "RECUPERACION_DECIDIDA", correlation, payload={
            "recovery_id": str(recovery["id"]), "purpose": purpose, "decision": decision,
        })
        return updated

    def ensure_no_blocking_issue(self, conn, order_id):
        if conn.execute(select(self.issues.c.id).where(
            self.issues.c.custody_id == order_id, self.issues.c.is_blocking.is_(True),
            self.issues.c.state != "RESUELTA",
        ).limit(1)).scalar_one_or_none():
            raise conflict("Existe una incidencia bloqueante.")

    def location_for(self, conn, order_id, *, lock=False):
        query = select(
            self.assignments.c.id, self.assignments.c.location_id, self.locations.c.code, self.locations.c.state,
        ).join(self.locations, self.assignments.c.location_id == self.locations.c.id).where(
            self.assignments.c.custody_id == order_id, self.assignments.c.released_at.is_(None),
        )
        if lock:
            query = query.with_for_update(of=[self.assignments, self.locations])
        row = conn.execute(query).mappings().one_or_none()
        if row is None or row["state"] != "OCUPADA":
            raise conflict("La ubicación de la custodia requiere conciliación.")
        return row

    def issue_return(self, conn, actor, order, body, correlation):
        if order["state"] != "EN_CUSTODIA" or order["version"] != body["expected_version"]:
            raise conflict("Actualiza la custodia antes de preparar la devolución.")
        recovery = find(conn, self.store, "recovery_requests", body["recovery_request_id"], lock=True)
        if recovery["custody_id"] != order["id"] or recovery["purpose"] != "AUTORIZAR_DEVOLUCION" or recovery["state"] != "APROBADA":
            raise conflict("Se requiere un expediente de devolución aprobado para esta custodia.")
        sender = find(conn, self.store, "users", order["sender_id"])
        if not sender["is_active"] or sender["contact_verified_at"] is None:
            raise conflict("El emisor debe estar activo y comprobado.")
        self.ensure_no_blocking_issue(conn, order["id"])
        self.location_for(conn, order["id"])
        self.revoke_credentials(conn, order["id"])
        authorization = conn.execute(self.authorizations.insert().values(
            id=uuid4(), custody_id=order["id"], operator_id=actor["id"], purpose="DEVOLUCION",
            recovery_request_id=recovery["id"], person_check=body["sender_check"], state="VALIDADA",
            expires_at=datetime.now(UTC) + timedelta(minutes=2),
        ).returning(*self.authorizations.c)).mappings().one()
        conn.execute(self.orders.update().where(self.orders.c.id == order["id"]).values(
            state="DEVOLUCION_EN_CURSO", version=order["version"] + 1,
        ))
        self.audit(conn, actor, order, "DEVOLUCION_PREPARADA", correlation, new_state="DEVOLUCION_EN_CURSO", payload={
            "authorization_id": str(authorization["id"]), "recovery_id": str(recovery["id"]),
        })
        return authorization

    def return_view(self, conn, order, authorization):
        if authorization["state"] != "VALIDADA" or authorization["expires_at"] <= datetime.now(UTC):
            raise conflict("La autorización ya no se encuentra vigente.")
        location = self.location_for(conn, order["id"])
        return {
            "authorization_id": authorization["id"], "custody_id": order["id"],
            "expires_at": authorization["expires_at"], "state": "VALIDADA",
            "location_code": location["code"], "description": order["description"], "version": order["version"],
        }

    def confirm_return(self, conn, actor, order, body, correlation):
        if order["state"] != "DEVOLUCION_EN_CURSO" or order["version"] != body["expected_version"]:
            raise conflict("La devolución cambió o ya se confirmó.")
        authorization = find(conn, self.store, "pickup_authorizations", body["authorization_id"], lock=True)
        if authorization["operator_id"] != actor["id"] or authorization["custody_id"] != order["id"]:
            raise IdentityError(403, "AUTORIZACION_NO_VISIBLE", "El operador debe confirmar su propia autorización.")
        if authorization["state"] != "VALIDADA" or authorization["purpose"] != "DEVOLUCION" or authorization["expires_at"] <= datetime.now(UTC):
            raise conflict("La autorización de devolución no está vigente.")
        self.ensure_no_blocking_issue(conn, order["id"])
        return self.complete_handover(conn, actor, order, authorization, correlation)

    def complete_handover(self, conn, actor, order, authorization, correlation, *, reconciliation=None):
        now = datetime.now(UTC)
        location = self.location_for(conn, order["id"], lock=True)
        result = "DEVUELTA" if authorization["purpose"] == "DEVOLUCION" else "RETIRADA"
        row = conn.execute(self.handovers.insert().values(
            id=uuid4(), custody_id=order["id"], authorization_id=authorization["id"],
            kind=authorization["purpose"], operator_id=authorization["operator_id"],
            recipient_check=authorization["person_check"], confirmed_at=now, reconciliation_request_id=reconciliation,
        ).returning(*self.handovers.c)).mappings().one()
        conn.execute(self.authorizations.update().where(
            self.authorizations.c.id == authorization["id"],
        ).values(state="CONSUMIDA"))
        if authorization["credential_id"] is not None:
            conn.execute(self.credentials.update().where(
                self.credentials.c.id == authorization["credential_id"],
            ).values(state="CONSUMIDA"))
        if authorization["recovery_request_id"] is not None:
            conn.execute(self.recovery.update().where(
                self.recovery.c.id == authorization["recovery_request_id"],
            ).values(state="EJECUTADA"))
        conn.execute(self.assignments.update().where(
            self.assignments.c.id == location["id"],
        ).values(released_at=now))
        conn.execute(self.locations.update().where(self.locations.c.id == location["location_id"]).values(
            state="DISPONIBLE", version=self.locations.c.version + 1,
        ))
        conn.execute(self.orders.update().where(self.orders.c.id == order["id"]).values(
            state=result, version=order["version"] + 1, completed_at=now,
        ))
        event = "ENTREGA_CONCILIADA" if reconciliation else "DEVOLUCION_CONFIRMADA"
        payload = {"handover_id": str(row["id"]), "authorization_id": str(authorization["id"])}
        if reconciliation:
            payload["recovery_id"] = str(reconciliation)
            payload["authorization_created_at"] = authorization["created_at"].isoformat()
        self.audit(conn, actor, order, event, correlation, new_state=result, payload=payload)
        return projected(row, HANDOVER_FIELDS)
