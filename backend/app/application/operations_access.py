from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import Connection, select
from sqlalchemy.engine import RowMapping

from app.adapters.storage.operations import OperationsStore
from app.domain.identity import IdentityError, Role


def projected(row: RowMapping, fields: Iterable[str]) -> dict:
    return {field: row[field] for field in fields}


def find(conn: Connection, store: OperationsStore, name: str, record_id: UUID, *, lock: bool = False) -> RowMapping:
    table = store.table(name)
    query = select(table).where(table.c.id == record_id)
    if lock:
        query = query.with_for_update()
    result = conn.execute(query).mappings().one_or_none()
    if result is None:
        raise IdentityError(404, "RECURSO_NO_VISIBLE", "El recurso no está disponible.")
    return result


def require_scope(
    conn: Connection, store: OperationsStore, actor: RowMapping, point_id: UUID,
    roles: frozenset[Role], *, active_point: bool = True,
) -> None:
    assignments, points, users = (store.table(name) for name in ("staff_assignments", "service_points", "users"))
    query = select(assignments.c.id).join(points, assignments.c.point_id == points.c.id).join(
        users, assignments.c.user_id == users.c.id
    ).where(
        assignments.c.user_id == actor["id"],
        assignments.c.point_id == point_id,
        assignments.c.is_active.is_(True),
        users.c.is_active.is_(True),
        users.c.role.in_(roles),
    )
    if active_point:
        query = query.where(points.c.is_active.is_(True))
    if conn.execute(query).scalar_one_or_none() is None:
        raise IdentityError(403, "PUNTO_NO_AUTORIZADO", "La cuenta no tiene acceso a ese punto.")
