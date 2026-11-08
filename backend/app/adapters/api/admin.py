from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request
from pydantic import AwareDatetime, ValidationError
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.adapters.api.operations_dto import (
    IdempotencyKey, LocationState, LocationWrite, PointWrite, StaffWrite, TariffWrite,
)
from app.adapters.api.security import ApiSecurity
from app.adapters.storage.operations import OperationsStore
from app.application.custody_tariffs import TariffRules
from app.application.operations_access import find, projected, require_scope
from app.domain.identity import IdentityError, Role


ADMIN = frozenset({Role.ADMIN})
SUPERVISORS = frozenset({Role.ADMIN, Role.AUDITOR})
POINT = ("id", "name", "address", "opening_hours", "is_active")
LOCATION = ("id", "point_id", "code", "state", "size_category", "version")
EVENT = ("id", "event_type", "created_at", "correlation_id", "actor_id", "custody_id")
ACTIVE_CUSTODIES = ("REGISTRADA", "EN_CUSTODIA", "RETIRO_EN_CURSO", "DEVOLUCION_EN_CURSO")


def admin_router(store: OperationsStore, security: ApiSecurity) -> APIRouter:
    router = APIRouter(tags=["Supervisión"])
    points = store.table("service_points")
    staff = store.table("staff_assignments")
    orders = store.table("custody_orders")
    locations = store.table("storage_locations")
    occupancy = store.table("storage_assignments")
    tariffs = store.table("tariff_versions")
    users = store.table("users")
    events = store.table("custody_events")
    incidents = store.table("incidents")
    write = [Depends(security.csrf)]

    def claim(conn, actor, operation, key, payload):
        return store.claim(
            conn, actor_id=actor["id"], operation=operation, key=key, payload=payload, secret=security.request_key,
        )

    def record(conn, request, actor, point_id, event_type, payload=None):
        store.event(
            conn, actor_id=actor["id"], point_id=point_id, event_type=event_type,
            correlation_id=request.state.correlation_id, payload=payload,
        )

    def locked_point(conn, actor, point_id, *, active=True):
        point = find(conn, store, "service_points", point_id, lock=True)
        require_scope(conn, store, actor, point_id, ADMIN, active_point=active)
        return point

    @router.post("/admin/points", status_code=201, dependencies=write)
    def create_point(body: PointWrite, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        if actor["role"] != Role.ADMIN or actor["contact_verified_at"] is None:
            raise IdentityError(403, "ADMIN_REQUERIDO", "Se requiere un administrador comprobado.")
        with store.engine.begin() as conn:
            any_point = conn.execute(select(points.c.id).limit(1)).scalar_one_or_none()
            assigned = conn.execute(select(staff.c.id).where(
                staff.c.user_id == actor["id"], staff.c.is_active.is_(True),
            ).limit(1)).scalar_one_or_none()
            if any_point is not None and assigned is None:
                raise IdentityError(403, "PUNTO_NO_AUTORIZADO", "El administrador carece de asignación.")
            record_id, prior = claim(conn, actor, "point:create", key, body.model_dump(mode="json"))
            if prior is not None:
                require_scope(conn, store, actor, prior, ADMIN, active_point=False)
                return projected(find(conn, store, "service_points", prior), POINT)
            point_id = uuid4()
            row = conn.execute(points.insert().values(
                id=point_id, code=point_id.hex[:20], **body.model_dump()
            ).returning(*points.c)).mappings().one()
            conn.execute(staff.insert().values(id=uuid4(), user_id=actor["id"], point_id=point_id, is_active=True))
            record(conn, request, actor, point_id, "PUNTO_CREADO")
            store.complete(conn, record_id, point_id)
            return projected(row, POINT)

    @router.put("/admin/points/{point_id}", dependencies=write)
    def update_point(point_id: UUID, body: PointWrite, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            point = locked_point(conn, actor, point_id, active=False)
            record_id, prior = claim(conn, actor, f"point:update:{point_id}", key, body.model_dump(mode="json"))
            if prior is not None:
                return projected(point, POINT)
            if not body.is_active and conn.execute(select(orders.c.id).where(
                orders.c.point_id == point_id, orders.c.state.in_(ACTIVE_CUSTODIES),
            ).limit(1)).scalar_one_or_none() is not None:
                raise IdentityError(409, "PUNTO_CON_CUSTODIAS", "Resuelve las custodias activas antes de cerrar el punto.")
            row = conn.execute(points.update().where(points.c.id == point_id).values(
                **body.model_dump()
            ).returning(*points.c)).mappings().one()
            record(conn, request, actor, point_id, "PUNTO_ACTUALIZADO")
            store.complete(conn, record_id, point_id)
            return projected(row, POINT)

    @router.post("/admin/locations", status_code=201, dependencies=write)
    def create_location(body: LocationWrite, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            locked_point(conn, actor, body.point_id)
            record_id, prior = claim(conn, actor, "location:create", key, body.model_dump(mode="json"))
            if prior is not None:
                row = find(conn, store, "storage_locations", prior)
                return projected(row, LOCATION)
            row = conn.execute(insert(locations).values(
                id=uuid4(), state="DISPONIBLE", **body.model_dump()
            ).on_conflict_do_nothing(index_elements=["point_id", "code"]).returning(
                *locations.c
            )).mappings().one_or_none()
            if row is None:
                raise IdentityError(409, "UBICACION_DUPLICADA", "El código de ubicación ya existe en el punto.")
            record(conn, request, actor, body.point_id, "UBICACION_CREADA", {"location_id": str(row["id"])})
            store.complete(conn, record_id, row["id"])
            return projected(row, LOCATION)

    @router.patch("/admin/locations/{location_id}", dependencies=write)
    def change_location(location_id: UUID, body: LocationState, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            location = find(conn, store, "storage_locations", location_id)
            point_id = location["point_id"]
            locked_point(conn, actor, point_id)
            record_id, prior = claim(conn, actor, f"location:state:{location_id}", key, body.model_dump(mode="json"))
            location = find(conn, store, "storage_locations", location_id, lock=True)
            if prior is not None:
                return projected(location, LOCATION)
            occupied = conn.execute(select(occupancy.c.id).where(
                occupancy.c.location_id == location_id, occupancy.c.released_at.is_(None),
            )).scalar_one_or_none() is not None
            if occupied or location["state"] == "OCUPADA" or location["version"] != body.expected_version:
                raise IdentityError(409, "UBICACION_EN_CONFLICTO", "La ubicación está ocupada o cambió de versión.")
            row = conn.execute(locations.update().where(locations.c.id == location_id).values(
                state=body.state, version=location["version"] + 1,
            ).returning(*locations.c)).mappings().one()
            record(conn, request, actor, point_id, "UBICACION_ESTADO", {
                "location_id": str(location_id), "previous": location["state"], "state": body.state,
            })
            store.complete(conn, record_id, location_id)
            return projected(row, LOCATION)

    @router.post("/admin/staff-assignments", dependencies=write)
    def assign_staff(body: StaffWrite, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        with store.engine.begin() as conn:
            locked_point(conn, actor, body.point_id)
            record_id, prior = claim(conn, actor, "staff:assign", key, body.model_dump(mode="json"))
            if prior is not None:
                return {"id": prior, "state": "ACTIVA" if body.is_active else "INACTIVA"}
            member = find(conn, store, "users", body.user_id, lock=True)
            if body.is_active and (not member["is_active"] or member["contact_verified_at"] is None):
                raise IdentityError(409, "PERSONAL_NO_COMPROBADO", "La cuenta de personal debe estar activa y comprobada.")
            assignment = conn.execute(select(staff).where(
                staff.c.point_id == body.point_id, staff.c.user_id == body.user_id,
            )).mappings().one_or_none()
            if not body.is_active and (assignment is None or member["role"] != body.role):
                raise IdentityError(404, "ASIGNACION_NO_VISIBLE", "No se encontró esa asignación.")
            if member["role"] == Role.ADMIN and (not body.is_active or body.role != Role.ADMIN):
                another = conn.execute(select(staff.c.id).join(users, staff.c.user_id == users.c.id).where(
                    staff.c.point_id == body.point_id, staff.c.user_id != body.user_id,
                    staff.c.is_active.is_(True), users.c.role == Role.ADMIN, users.c.is_active.is_(True),
                ).limit(1)).scalar_one_or_none()
                if another is None:
                    raise IdentityError(409, "ULTIMO_ADMIN", "Asigna a otro administrador antes de quitar este acceso.")
            if body.is_active and member["role"] != body.role:
                other_points = conn.execute(select(staff.c.id).where(
                    staff.c.user_id == body.user_id, staff.c.point_id != body.point_id, staff.c.is_active.is_(True),
                ).limit(1)).scalar_one_or_none()
                if other_points is not None:
                    raise IdentityError(409, "ROL_EN_OTRO_PUNTO", "El cambio de rol afecta otros puntos activos.")
                conn.execute(users.update().where(users.c.id == body.user_id).values(role=body.role))
            assignment_id = assignment["id"] if assignment is not None else uuid4()
            if assignment is None:
                conn.execute(staff.insert().values(
                    id=assignment_id, point_id=body.point_id, user_id=body.user_id, is_active=body.is_active,
                ))
            else:
                conn.execute(staff.update().where(staff.c.id == assignment_id).values(is_active=body.is_active))
            record(conn, request, actor, body.point_id, "PERSONAL_ASIGNADO", {
                "assignment_id": str(assignment_id), "role": body.role, "is_active": body.is_active,
            })
            store.complete(conn, record_id, assignment_id)
            return {"id": assignment_id, "state": "ACTIVA" if body.is_active else "INACTIVA"}

    @router.post("/admin/tariffs", status_code=201, dependencies=write)
    def create_tariff(body: TariffWrite, request: Request, key: IdempotencyKey) -> dict:
        actor = security.actor(request)
        try:
            rules = TariffRules.model_validate(body.rules).model_dump(mode="json")
        except ValidationError:
            raise IdentityError(422, "TARIFA_INVALIDA", "Revisa moneda, tamaños, bloques e importes de la tarifa.") from None
        with store.engine.begin() as conn:
            locked_point(conn, actor, body.point_id)
            record_id, prior = claim(conn, actor, "tariff:create", key, body.model_dump(mode="json"))
            if prior is not None:
                return {"id": prior}
            latest = conn.execute(select(func.coalesce(func.max(tariffs.c.version), 0)).where(
                tariffs.c.point_id == body.point_id
            )).scalar_one()
            tariff_id = uuid4()
            conn.execute(tariffs.insert().values(
                id=tariff_id, point_id=body.point_id, version=latest + 1, valid_from=body.valid_from,
                rules=rules, created_by=actor["id"],
            ))
            record(conn, request, actor, body.point_id, "TARIFA_PUBLICADA", {"tariff_id": str(tariff_id)})
            store.complete(conn, record_id, tariff_id)
            return {"id": tariff_id}

    @router.get("/audit/events")
    def audit(point_id: UUID, request: Request) -> list[dict]:
        actor = security.actor(request)
        with store.engine.connect() as conn:
            require_scope(conn, store, actor, point_id, SUPERVISORS, active_point=False)
            rows = conn.execute(select(events).where(events.c.point_id == point_id).order_by(
                events.c.created_at.desc(), events.c.id.desc()
            ).limit(500)).mappings()
            return [projected(row, EVENT) for row in rows]

    @router.get("/reports")
    def report(
        point_id: UUID, request: Request, date_from: Annotated[AwareDatetime, Query(alias="from")],
        date_to: Annotated[AwareDatetime, Query(alias="to")],
    ) -> dict:
        actor = security.actor(request)
        if date_to <= date_from or date_to - date_from > timedelta(days=366):
            raise IdentityError(422, "PERIODO_INVALIDO", "Indica un periodo ordenado de hasta 366 días.")
        with store.engine.connect() as conn:
            require_scope(conn, store, actor, point_id, SUPERVISORS, active_point=False)
            available, occupied = conn.execute(select(
                func.count().filter(locations.c.state == "DISPONIBLE"),
                func.count().filter(locations.c.state == "OCUPADA"),
            ).where(locations.c.point_id == point_id)).one()
            completed, measured, mean_hours = conn.execute(select(
                func.count(),
                func.count(orders.c.received_at),
                func.avg(func.extract("epoch", orders.c.completed_at - orders.c.received_at) / 3600),
            ).where(
                orders.c.point_id == point_id, orders.c.state.in_(("RETIRADA", "DEVUELTA")),
                orders.c.completed_at >= date_from, orders.c.completed_at < date_to,
            )).one()
            issue_count = conn.execute(select(func.count()).select_from(incidents).join(
                orders, orders.c.id == incidents.c.custody_id,
            ).where(
                orders.c.point_id == point_id, incidents.c.created_at >= date_from, incidents.c.created_at < date_to,
            )).scalar_one()
        duration = f"Permanencia media {mean_hours:.2f} h en {measured} de {completed} salidas." if measured else (
            f"Permanencia sin mediciones en {completed} salidas."
        )
        stamp = datetime.now(UTC).isoformat(timespec="minutes")
        return {
            "point_id": point_id, "from": date_from, "to": date_to,
            "available_locations": available, "occupied_locations": occupied, "completed_custodies": completed,
            "data_quality_note": (
                f"Ocupación actual a {stamp} sobre {available + occupied} ubicaciones utilizables. "
                f"{duration} Incidencias abiertas en el periodo {issue_count}. "
                "El sistema registra fechas de custodia. Los tiempos de atención presencial requieren observación."
            ),
        }

    return router
