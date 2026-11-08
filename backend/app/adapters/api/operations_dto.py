from typing import Annotated, Literal
from uuid import UUID

from fastapi import Header
from pydantic import AwareDatetime, Field, StringConstraints

from app.adapters.api.dto import Payload

IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=120)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Note = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=1200)]
Version = Annotated[int, Field(ge=1)]
Size = Literal["PEQUENO", "MEDIANO", "GRANDE"]


class PointWrite(Payload):
    name: Name
    address: Note
    opening_hours: dict
    is_active: bool


class LocationWrite(Payload):
    point_id: UUID
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=24)]
    size_category: Size


class LocationState(Payload):
    state: Literal["DISPONIBLE", "BLOQUEADA", "FUERA_SERVICIO"]
    expected_version: Version
    reason: Note


class StaffWrite(Payload):
    point_id: UUID
    user_id: UUID
    role: Literal["OPERADOR", "ADMIN", "AUDITOR"]
    is_active: bool


class TariffWrite(Payload):
    point_id: UUID
    valid_from: AwareDatetime
    rules: dict


class Reason(Payload):
    reason: Note


class IncidentCreate(Payload):
    kind: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
    description: Note
    is_blocking: bool = True


class RecoveryCreate(Payload):
    custody_id: UUID
    purpose: Literal["REEMITIR_CREDENCIAL", "CAMBIAR_DESTINATARIO", "AUTORIZAR_DEVOLUCION", "RECONCILIAR_ENTREGA"]
    evidence: Note
    target_recipient_id: UUID | None = None


class Decision(Payload):
    decision: Literal["APROBAR", "RECHAZAR"]
    note: Note


class ReturnAuthorization(Payload):
    recovery_request_id: UUID
    expected_version: Version
    sender_check: Literal["COMPROBACION_VISUAL_COMPLETADA"]


class HandoverConfirm(Payload):
    authorization_id: UUID
    expected_version: Version
    physically_delivered: Literal[True]
