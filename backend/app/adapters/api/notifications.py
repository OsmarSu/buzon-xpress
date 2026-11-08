from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select

from app.adapters.api.security import ApiSecurity
from app.adapters.storage.operations import OperationsStore
from app.application.operations_access import projected
from app.domain.identity import IdentityError

NOTICE_FIELDS = ("id", "subject", "body", "created_at", "read_at")


def notifications_router(store: OperationsStore, security: ApiSecurity) -> APIRouter:
    router = APIRouter(tags=["Avisos"])
    notices = store.table("notifications")

    @router.get("/notifications")
    def list_notifications(request: Request) -> list[dict]:
        actor = security.actor(request)
        with store.engine.connect() as conn:
            rows = conn.execute(select(notices).where(
                notices.c.user_id == actor["id"], notices.c.channel == "BANDEJA",
            ).order_by(notices.c.created_at.desc(), notices.c.id.desc())).mappings()
            return [projected(row, NOTICE_FIELDS) for row in rows]

    @router.post("/notifications/{notification_id}/read", dependencies=[Depends(security.csrf)])
    def mark_read(notification_id: UUID, request: Request) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            found = conn.execute(notices.update().where(
                notices.c.id == notification_id, notices.c.user_id == actor["id"], notices.c.channel == "BANDEJA",
            ).values(
                state="LEIDA", read_at=func.coalesce(notices.c.read_at, datetime.now(UTC)),
            ).returning(notices.c.id)).scalar_one_or_none()
            if found is None:
                raise IdentityError(404, "AVISO_NO_VISIBLE", "El aviso no está disponible.")
        return {"id": found, "state": "LEIDA"}

    return router
