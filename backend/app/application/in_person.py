from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.engine import RowMapping

from app.adapters.storage.operations import OperationsStore
from app.domain.identity import IdentityError, Role


def verify_contact_in_person(
    store: OperationsStore, *, actor_id: UUID, user_id: UUID, reason: str, key: str, secret: bytes,
    correlation_id: UUID,
) -> RowMapping:
    if actor_id == user_id:
        raise IdentityError(403, "AUTOCOMPROBACION", "Otra persona autorizada debe comprobar el contacto.")
    users, assignments, points = (store.table(name) for name in ("users", "staff_assignments", "service_points"))
    with store.engine.begin() as conn:
        scope = set(conn.scalars(
            select(points.c.id).join(assignments, assignments.c.point_id == points.c.id)
            .join(users, users.c.id == assignments.c.user_id)
            .where(
                users.c.id == actor_id,
                users.c.role == Role.ADMIN,
                users.c.is_active.is_(True),
                assignments.c.is_active.is_(True),
                points.c.is_active.is_(True),
            ).order_by(points.c.id).with_for_update(of=points, read=True)
        ))
        if not scope:
            raise IdentityError(403, "PUNTO_NO_AUTORIZADO", "Se requiere administración de un punto activo.")

        target = conn.execute(
            select(users).where(users.c.id == user_id, users.c.is_active.is_(True)).with_for_update()
        ).mappings().one_or_none()
        if target is None:
            raise IdentityError(404, "RECURSO_NO_VISIBLE", "El recurso no está disponible.")
        if target["role"] != Role.USUARIO:
            scope.intersection_update(conn.scalars(
                select(assignments.c.point_id).where(
                    assignments.c.user_id == user_id,
                    assignments.c.is_active.is_(True),
                    assignments.c.point_id.in_(scope),
                )
            ))
            if not scope:
                raise IdentityError(404, "RECURSO_NO_VISIBLE", "El recurso no está disponible.")
        if len(scope) != 1:
            raise IdentityError(409, "PUNTO_AMBIGUO", "Se requiere un punto activo inequívoco para comprobar el contacto.")

        record_id, prior = store.claim(
            conn, actor_id=actor_id, operation="users:verify-contact", key=key,
            payload={"user_id": str(user_id), "reason": reason}, secret=secret,
        )
        if prior is not None:
            return target
        if target["contact_verified_at"] is not None:
            raise IdentityError(409, "CONTACTO_YA_COMPROBADO", "El contacto ya fue comprobado.")

        checked = conn.execute(
            users.update().where(users.c.id == user_id).values(
                contact_verified_at=datetime.now(UTC),
                contact_verification_hash=None,
                verification_expires_at=None,
            ).returning(*users.c)
        ).mappings().one()
        store.event(
            conn, actor_id=actor_id, point_id=next(iter(scope)), event_type="CONTACTO_COMPROBADO_PRESENCIAL",
            correlation_id=correlation_id, payload={"user_id": str(user_id), "reason": reason},
        )
        store.complete(conn, record_id, user_id)
        return checked
