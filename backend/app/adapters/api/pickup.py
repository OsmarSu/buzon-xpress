from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import Field, SecretStr, field_validator

from app.adapters.api.dto import Payload
from app.adapters.api.limits import IdentityRateLimit
from app.adapters.api.operations_dto import HandoverConfirm, IdempotencyKey, Note, Version
from app.adapters.api.security import ApiSecurity
from app.adapters.storage.operations import OperationsStore
from app.application.exceptions import HANDOVER_FIELDS, OPERATORS
from app.application.operations_access import find, projected, require_scope
from app.application.pickup import PickupService, custody_view
from app.domain.identity import IdentityError


class CredentialIssue(Payload):
    reissue: bool = False


class Verify(Payload):
    code: Annotated[SecretStr, Field(min_length=6, max_length=6)]
    expected_version: Version
    recipient_check: Literal["COMPROBACION_VISUAL_COMPLETADA"]

    @field_validator("code")
    @classmethod
    def six_ascii_digits(cls, value: SecretStr) -> SecretStr:
        code = value.get_secret_value()
        if not code.isascii() or not code.isdecimal():
            raise ValueError("Usa seis dígitos.")
        return value


class Abort(Payload):
    authorization_id: UUID
    physically_delivered: Literal[False]
    reason: Note

    @field_validator("physically_delivered", mode="before")
    @classmethod
    def must_be_false(cls, value):
        if value is not False:
            raise ValueError("La anulación exige declarar que no se entregó.")
        return value


def pickup_router(store: OperationsStore, security: ApiSecurity) -> APIRouter:
    router = APIRouter(prefix="/custodies", tags=["Retiro"])
    service = PickupService(store, security.credential_key)
    rates = IdentityRateLimit(window_seconds=900)
    write = [Depends(security.csrf)]

    def claim(conn, actor, operation, key, payload):
        return store.claim(
            conn, actor_id=actor["id"], operation=operation, key=key, payload=payload, secret=security.request_key,
        )

    def locked_order(conn, actor, custody_id):
        order = find(conn, store, "custody_orders", custody_id, lock=True)
        require_scope(conn, store, actor, order["point_id"], OPERATORS)
        return order

    @router.post("/{custody_id}/credentials", status_code=201, dependencies=write)
    def issue(custody_id: UUID, body: CredentialIssue, request: Request) -> dict:
        actor = security.actor(request)
        rates.check("emitir", str(actor["id"]), 20)
        with store.engine.begin() as conn:
            order = find(conn, store, "custody_orders", custody_id, lock=True)
            return service.issue(conn, actor, order, body.reissue, request.state.correlation_id)

    @router.post("/{custody_id}/verify", dependencies=write)
    def verify(custody_id: UUID, body: Verify, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        ip = request.client.host if request.client else "unknown"
        rates.check("verificar-origen", ip, 120)
        rates.check("verificar-cuenta", str(actor["id"]), 40)
        with store.engine.begin() as conn:
            order = locked_order(conn, actor, custody_id)
            payload = {**body.model_dump(mode="json"), "code": body.code.get_secret_value()}
            record, prior = claim(conn, actor, f"pickup:verify:{custody_id}", key, payload)
            if prior is not None:
                outcome = service.retry_verification(conn, actor, order, prior)
            else:
                outcome = service.verify(conn, actor, order, body, request.state.correlation_id, record)
        # Rejected attempts and their idempotency result must commit before the HTTP error.
        if isinstance(outcome, IdentityError):
            raise outcome
        return outcome

    @router.post("/{custody_id}/handover", dependencies=write)
    def handover(custody_id: UUID, body: HandoverConfirm, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            order = locked_order(conn, actor, custody_id)
            record, prior = claim(conn, actor, f"pickup:handover:{custody_id}", key, body.model_dump(mode="json"))
            if prior is not None:
                return projected(find(conn, store, "handovers", prior), HANDOVER_FIELDS)
            result = service.confirm(conn, actor, order, body, request.state.correlation_id)
            store.complete(conn, record, result["id"])
            return result

    @router.post("/{custody_id}/abort-handover", dependencies=write)
    def abort(custody_id: UUID, body: Abort, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            order = locked_order(conn, actor, custody_id)
            record, prior = claim(conn, actor, f"pickup:abort:{custody_id}", key, body.model_dump(mode="json"))
            if prior is not None:
                return custody_view(order)
            result = service.abort(conn, actor, order, body, request.state.correlation_id)
            store.complete(conn, record, order["id"])
            return result

    return router
