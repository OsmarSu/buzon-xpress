from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from pydantic import StringConstraints

from app.adapters.api.auth import serialize_user
from app.adapters.api.dto import Payload, User
from app.adapters.api.security import ApiSecurity
from app.adapters.storage.operations import OperationsStore
from app.application.in_person import verify_contact_in_person


class ContactEvidence(Payload):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


def in_person_router(store: OperationsStore, security: ApiSecurity) -> APIRouter:
    router = APIRouter(tags=["Identidad"])

    @router.post("/admin/users/{user_id}/verify-contact", response_model=User, dependencies=[Depends(security.csrf)])
    def verify(
        user_id: UUID,
        body: ContactEvidence,
        request: Request,
        key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=120)],
    ) -> User:
        actor = security.actor(request)
        checked = verify_contact_in_person(
            store, actor_id=actor["id"], user_id=user_id, reason=body.reason, key=key,
            secret=security.request_key, correlation_id=request.state.correlation_id,
        )
        return serialize_user(checked)

    return router
