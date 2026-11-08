from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.adapters.api.operations_dto import (
    Decision, HandoverConfirm, IdempotencyKey, IncidentCreate, Reason, RecoveryCreate, ReturnAuthorization,
)
from app.adapters.api.security import ApiSecurity
from app.adapters.storage.operations import OperationsStore
from app.application.exceptions import (
    HANDOVER_FIELDS, INCIDENT_FIELDS, MANAGERS, OPERATORS, RECOVERY_FIELDS, ExceptionsService,
)
from app.application.operations_access import find, projected, require_scope


def recovery_router(store: OperationsStore, security: ApiSecurity) -> APIRouter:
    router = APIRouter(tags=["Incidencias y recuperación"])
    service = ExceptionsService(store)
    write = [Depends(security.csrf)]

    def claim(conn, actor, operation, key, body):
        return store.claim(
            conn, actor_id=actor["id"], operation=operation, key=key,
            payload=body.model_dump(mode="json"), secret=security.request_key,
        )

    def order_for(conn, custody_id):
        return find(conn, store, "custody_orders", custody_id, lock=True)

    @router.post("/custodies/{custody_id}/incidents", status_code=201, dependencies=write)
    def incident(custody_id: UUID, body: IncidentCreate, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            order = order_for(conn, custody_id)
            service.scope(conn, actor, order, participants=True)
            record, prior = claim(conn, actor, f"incident:create:{custody_id}", key, body)
            if prior is not None:
                return projected(find(conn, store, "incidents", prior), INCIDENT_FIELDS)
            row = service.record_incident(conn, actor, order, body.model_dump(), request.state.correlation_id)
            store.complete(conn, record, row["id"])
            return projected(row, INCIDENT_FIELDS)

    @router.post("/incidents/{incident_id}/resolve", dependencies=write)
    def resolve(incident_id: UUID, body: Reason, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            issue = find(conn, store, "incidents", incident_id)
            order = order_for(conn, issue["custody_id"])
            require_scope(conn, store, actor, order["point_id"], MANAGERS)
            record, prior = claim(conn, actor, f"incident:resolve:{incident_id}", key, body)
            issue = find(conn, store, "incidents", incident_id, lock=True)
            if prior is not None:
                return projected(issue, INCIDENT_FIELDS)
            row = service.resolve_incident(conn, actor, order, issue, body.reason, request.state.correlation_id)
            store.complete(conn, record, row["id"])
            return projected(row, INCIDENT_FIELDS)

    @router.post("/recovery-requests", status_code=201, dependencies=write)
    def create_recovery(body: RecoveryCreate, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            order = order_for(conn, body.custody_id)
            service.scope(conn, actor, order, participants=body.purpose in ("REEMITIR_CREDENCIAL", "AUTORIZAR_DEVOLUCION"))
            record, prior = claim(conn, actor, "recovery:create", key, body)
            if prior is not None:
                return projected(find(conn, store, "recovery_requests", prior), RECOVERY_FIELDS)
            row = service.create_recovery(conn, actor, order, body.model_dump(), request.state.correlation_id)
            store.complete(conn, record, row["id"])
            return projected(row, RECOVERY_FIELDS)

    @router.post("/recovery-requests/{request_id}/decision", dependencies=write)
    def decide(request_id: UUID, body: Decision, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            recovery = find(conn, store, "recovery_requests", request_id)
            order = order_for(conn, recovery["custody_id"])
            require_scope(conn, store, actor, order["point_id"], MANAGERS)
            record, prior = claim(conn, actor, f"recovery:decide:{request_id}", key, body)
            recovery = find(conn, store, "recovery_requests", request_id, lock=True)
            if prior is not None:
                return projected(recovery, RECOVERY_FIELDS)
            row = service.decide(conn, actor, order, recovery, body.model_dump(), request.state.correlation_id)
            store.complete(conn, record, row["id"])
            return projected(row, RECOVERY_FIELDS)

    @router.post("/custodies/{custody_id}/return-authorization", dependencies=write)
    def authorize_return(custody_id: UUID, body: ReturnAuthorization, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            order = order_for(conn, custody_id)
            require_scope(conn, store, actor, order["point_id"], OPERATORS)
            record, prior = claim(conn, actor, f"return:authorize:{custody_id}", key, body)
            if prior is not None:
                return service.return_view(conn, order, find(conn, store, "pickup_authorizations", prior))
            row = service.issue_return(conn, actor, order, body.model_dump(), request.state.correlation_id)
            store.complete(conn, record, row["id"])
            return service.return_view(conn, order_for(conn, custody_id), row)

    @router.post("/custodies/{custody_id}/return-handover", dependencies=write)
    def return_handover(custody_id: UUID, body: HandoverConfirm, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            order = order_for(conn, custody_id)
            require_scope(conn, store, actor, order["point_id"], OPERATORS)
            record, prior = claim(conn, actor, f"return:handover:{custody_id}", key, body)
            if prior is not None:
                return projected(find(conn, store, "handovers", prior), HANDOVER_FIELDS)
            row = service.confirm_return(conn, actor, order, body.model_dump(), request.state.correlation_id)
            store.complete(conn, record, row["id"])
            return row

    return router
