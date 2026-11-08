from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from secrets import token_hex, token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy import Connection, exists, or_, select
from sqlalchemy.engine import RowMapping

from app.adapters.storage.operations import OperationsStore
from app.application.custody_tariffs import MAX_AMOUNT, TariffRules
from app.domain.identity import IdentityError, Role


CUSTODY_FIELDS = (
    "id", "tracking_number", "state", "point_id", "description", "size_category",
    "version", "due_at", "received_at",
)
POINT_FIELDS = ("id", "name", "address", "opening_hours", "is_active")
LOCATION_FIELDS = ("id", "point_id", "code", "state", "size_category", "version")
SIZE_ORDER = {"PEQUENO": 0, "MEDIANO": 1, "GRANDE": 2}
STAFF_ROLES = (Role.OPERADOR, Role.ADMIN, Role.AUDITOR)
OPERATOR_ROLES = (Role.OPERADOR,)


def public_reference_hash(reference: str) -> str:
    return sha256(reference.encode()).hexdigest()


def custody_view(order: RowMapping) -> dict:
    return {**{key: order[key] for key in CUSTODY_FIELDS}, "service_total": f"{order['service_total']:.2f}"}


def conflict(code: str, message: str) -> IdentityError:
    return IdentityError(409, code, message)


class CustodyOperations:
    def __init__(self, store: OperationsStore, *, request_key: bytes) -> None:
        self.store = store
        self.request_key = request_key
        self.orders = store.table("custody_orders")
        self.users = store.table("users")
        self.points = store.table("service_points")
        self.assignments = store.table("staff_assignments")
        self.locations = store.table("storage_locations")
        self.storage = store.table("storage_assignments")
        self.tariffs = store.table("tariff_versions")
        self.payments = store.table("service_payments")

    def points_list(self) -> list[dict]:
        with self.store.engine.connect() as conn:
            rows = conn.execute(
                select(self.points).where(self.points.c.is_active).order_by(self.points.c.name, self.points.c.id)
            ).mappings()
            return [{key: row[key] for key in POINT_FIELDS} for row in rows]

    def quote(self, point_id: UUID, category: str, hours: int) -> dict:
        with self.store.engine.connect() as conn:
            self.active_point(conn, point_id)
            tariff, _rules, price = self.current_price(conn, point_id, category, hours)
            return {"tariff_id": tariff["id"], "amount": f"{price:.2f}", "currency": "BOB", "duration_hours": hours}

    def historical_quote(
        self, actor: RowMapping, point_id: UUID, custody_id: UUID, category: str, hours: int
    ) -> dict:
        with self.store.engine.connect() as conn:
            self.require_staff(conn, actor, point_id)
            order = self.get_order(conn, custody_id)
            if order["point_id"] != point_id:
                raise IdentityError(404, "CUSTODIA_NO_ENCONTRADA", "No se encontró la custodia.")
            if order["state"] != "EN_CUSTODIA":
                raise conflict("ESTADO_NO_PERMITE", "El estado de la custodia no permite una prórroga.")
            if order["size_category"] != category:
                raise conflict("TAMANO_NO_COINCIDE", "Cotiza con el tamaño registrado en la custodia.")
            amount = self.extension_amount(order, hours)
            return {
                "tariff_id": order["tariff_id"], "amount": f"{amount:.2f}",
                "currency": "BOB", "duration_hours": hours,
            }

    def create(self, actor: RowMapping, key: str, body: dict, correlation_id: UUID) -> dict:
        with self.store.engine.begin() as conn:
            self.require_verified(conn, actor["id"])
            record, prior = self.claim(conn, actor, "custodies:create", key, body)
            if prior is not None:
                return custody_view(self.locked_order(conn, prior))
            point_id = body["point_id"]
            self.active_point(conn, point_id)
            recipient_id = self.find_recipient(conn, body["recipient_contact"])
            reference = token_urlsafe(32)
            order = conn.execute(
                self.orders.insert().values(
                    id=uuid4(), tracking_number=f"BZX-{token_hex(12).upper()}",
                    public_reference_hash=public_reference_hash(reference), sender_id=actor["id"],
                    recipient_id=recipient_id, point_id=point_id, description=body["description"],
                    size_category=body["size_category"], state="REGISTRADA",
                ).returning(self.orders)
            ).mappings().one()
            self.event(conn, actor, order, "CUSTODIA_REGISTRADA", correlation_id, previous_state=None)
            self.store.complete(conn, record, order["id"])
            return {**custody_view(order), "public_reference": reference}

    def list_custodies(self, actor: RowMapping, point_id: UUID | None, tracking_number: str | None) -> list[dict]:
        order = self.orders
        visible = or_(order.c.sender_id == actor["id"], order.c.recipient_id == actor["id"])
        if actor["role"] in STAFF_ROLES:
            assigned = exists(select(self.assignments.c.id).where(
                self.assignments.c.point_id == order.c.point_id,
                self.assignments.c.user_id == actor["id"],
                self.assignments.c.is_active,
            ))
            visible = or_(visible, assigned)
        query = select(order).where(visible)
        if point_id is not None:
            query = query.where(order.c.point_id == point_id)
        if tracking_number is not None:
            query = query.where(order.c.tracking_number == tracking_number.strip().upper())
        with self.store.engine.connect() as conn:
            return [custody_view(row) for row in conn.execute(query.order_by(order.c.created_at.desc(), order.c.id)).mappings()]

    def detail(self, actor: RowMapping, custody_id: UUID) -> dict:
        with self.store.engine.connect() as conn:
            order = self.get_order(conn, custody_id)
            if actor["id"] not in (order["sender_id"], order["recipient_id"]):
                self.require_staff(conn, actor, order["point_id"], roles=STAFF_ROLES, concealed=True)
            return custody_view(order)

    def rotate_reference(self, actor: RowMapping, custody_id: UUID, correlation_id: UUID) -> dict:
        with self.store.engine.begin() as conn:
            order = self.locked_order(conn, custody_id)
            if actor["id"] not in (order["sender_id"], order["recipient_id"]):
                raise IdentityError(404, "CUSTODIA_NO_ENCONTRADA", "No se encontró la custodia.")
            reference = token_urlsafe(32)
            conn.execute(
                self.orders.update().where(self.orders.c.id == custody_id)
                .values(public_reference_hash=public_reference_hash(reference))
            )
            self.event(conn, actor, order, "REFERENCIA_PUBLICA_RENOVADA", correlation_id, previous_state=order["state"])
            return {"public_reference": reference}

    def tracking(self, reference: str) -> dict:
        orders, points = self.orders, self.points
        with self.store.engine.connect() as conn:
            row = conn.execute(
                select(orders.c.state, points.c.name, points.c.opening_hours)
                .select_from(orders.join(points, orders.c.point_id == points.c.id))
                .where(orders.c.public_reference_hash == public_reference_hash(reference))
            ).mappings().one_or_none()
        if row is None:
            raise IdentityError(404, "REFERENCIA_NO_ENCONTRADA", "No se encontró la referencia pública.")
        state = row["state"]
        if state == "REGISTRADA":
            public = "PENDIENTE"
        elif state in ("RETIRADA", "DEVUELTA", "CANCELADA"):
            public = "FINALIZADA"
        else:
            public = "RECIBIDA"
        return {"state": public, "point_name": row["name"], "opening_hours": row["opening_hours"]}

    def cancel(self, actor: RowMapping, custody_id: UUID, key: str, body: dict, correlation_id: UUID) -> dict:
        with self.store.engine.begin() as conn:
            order = self.locked_order(conn, custody_id)
            self.require_sender(order, actor)
            record, prior = self.claim(conn, actor, f"custodies:{custody_id}:cancel", key, body)
            if prior is not None:
                return custody_view(order)
            self.require_state(order, "REGISTRADA", body["expected_version"])
            updated = self.update_order(conn, order, state="CANCELADA", completed_at=datetime.now(UTC))
            self.event(
                conn, actor, updated, "CUSTODIA_CANCELADA", correlation_id,
                previous_state=order["state"], payload={"reason": body["reason"]},
            )
            self.store.complete(conn, record, custody_id)
            return custody_view(updated)

    def receive(self, actor: RowMapping, custody_id: UUID, key: str, body: dict, correlation_id: UUID) -> dict:
        with self.store.engine.begin() as conn:
            order = self.locked_order(conn, custody_id)
            self.require_staff(conn, actor, order["point_id"], lock=True)
            record, prior = self.claim(conn, actor, f"custodies:{custody_id}:receive", key, body)
            if prior is not None:
                return custody_view(order)
            self.require_state(order, "REGISTRADA", body["expected_version"])
            self.active_point(conn, order["point_id"], lock=True)
            for user_id in sorted({order["sender_id"], order["recipient_id"]}):
                self.require_verified(conn, user_id, lock=True)
            tariff, rules, amount = self.current_price(
                conn, order["point_id"], order["size_category"], body["duration_hours"]
            )
            if tariff["id"] != body["tariff_id"] or amount != Decimal(body["accepted_amount"]):
                raise conflict("TARIFA_CAMBIO", "Solicita una cotización y confirma el importe vigente.")
            location = self.available_location(conn, order, body["location_id"])
            now = datetime.now(UTC)
            updated = self.update_order(
                conn, order, state="EN_CUSTODIA", tariff_id=tariff["id"], tariff_snapshot=rules.model_dump(mode="json"),
                service_total=amount, received_at=now, due_at=self.advance_hours(now, body["duration_hours"]),
            )
            conn.execute(self.storage.insert().values(
                id=uuid4(), custody_id=custody_id, point_id=order["point_id"],
                location_id=location["id"], assigned_at=now,
            ))
            conn.execute(self.locations.update().where(self.locations.c.id == location["id"]).values(
                state="OCUPADA", version=location["version"] + 1,
            ))
            self.register_payment(conn, actor, custody_id, "INICIAL", amount, body)
            self.event(
                conn, actor, updated, "CUSTODIA_RECIBIDA", correlation_id, previous_state=order["state"],
                payload={
                    "location_id": str(location["id"]), "tariff_id": str(tariff["id"]),
                    "amount": f"{amount:.2f}", "external_condition": body["external_condition"],
                },
            )
            self.store.complete(conn, record, custody_id)
            return custody_view(updated)

    def extend(self, actor: RowMapping, custody_id: UUID, key: str, body: dict, correlation_id: UUID) -> dict:
        with self.store.engine.begin() as conn:
            order = self.locked_order(conn, custody_id)
            self.require_staff(conn, actor, order["point_id"], lock=True)
            record, prior = self.claim(conn, actor, f"custodies:{custody_id}:extend", key, body)
            if prior is not None:
                return custody_view(order)
            self.require_state(order, "EN_CUSTODIA", body["expected_version"])
            amount = self.extension_amount(order, body["additional_hours"])
            if amount != Decimal(body["accepted_amount"]):
                raise conflict("IMPORTE_NO_COINCIDE", "Confirma el importe calculado con la tarifa histórica.")
            total = order["service_total"] + amount
            due = self.advance_hours(order["due_at"], body["additional_hours"])
            updated = self.update_order(conn, order, service_total=total, due_at=due)
            self.register_payment(conn, actor, custody_id, "PRORROGA", amount, body)
            self.event(
                conn, actor, updated, "PLAZO_PRORROGADO", correlation_id, previous_state=order["state"],
                payload={"amount": f"{amount:.2f}", "additional_hours": body["additional_hours"]},
            )
            self.store.complete(conn, record, custody_id)
            return custody_view(updated)

    def inventory(self, actor: RowMapping, point_id: UUID) -> list[dict]:
        with self.store.engine.connect() as conn:
            self.require_staff(conn, actor, point_id, roles=STAFF_ROLES)
            rows = conn.execute(
                select(self.locations).where(self.locations.c.point_id == point_id).order_by(self.locations.c.code)
            ).mappings()
            return [{key: row[key] for key in LOCATION_FIELDS} for row in rows]

    def get_order(self, conn: Connection, custody_id: UUID, *, lock: bool = False) -> RowMapping:
        query = select(self.orders).where(self.orders.c.id == custody_id)
        if lock:
            query = query.with_for_update()
        row = conn.execute(query).mappings().one_or_none()
        if row is None:
            raise IdentityError(404, "CUSTODIA_NO_ENCONTRADA", "No se encontró la custodia.")
        return row

    def locked_order(self, conn: Connection, custody_id: UUID) -> RowMapping:
        return self.get_order(conn, custody_id, lock=True)

    def require_staff(
        self, conn: Connection, actor: RowMapping, point_id: UUID, *,
        roles=OPERATOR_ROLES, concealed: bool = False, lock: bool = False,
    ) -> None:
        staff, users = self.assignments, self.users
        query = select(staff.c.id).select_from(staff.join(users, staff.c.user_id == users.c.id)).where(
            staff.c.point_id == point_id, staff.c.user_id == actor["id"],
            staff.c.is_active, users.c.is_active, users.c.role.in_(roles),
        )
        if lock:
            query = query.with_for_update(read=True, of=(staff, users))
        if actor["role"] not in roles or conn.execute(query).scalar_one_or_none() is None:
            if concealed:
                raise IdentityError(404, "CUSTODIA_NO_ENCONTRADA", "No se encontró la custodia.")
            raise IdentityError(403, "PUNTO_NO_AUTORIZADO", "La cuenta no tiene permiso en el punto indicado.")

    def require_sender(self, order: RowMapping, actor: RowMapping) -> None:
        if order["sender_id"] != actor["id"]:
            raise IdentityError(404, "CUSTODIA_NO_ENCONTRADA", "No se encontró la custodia.")

    def require_verified(self, conn: Connection, user_id: UUID, *, lock: bool = False) -> None:
        users = self.users
        query = select(users.c.id).where(users.c.id == user_id, users.c.is_active, users.c.contact_verified_at.is_not(None))
        if lock:
            query = query.with_for_update(read=True)
        if conn.execute(query).scalar_one_or_none() is None:
            raise IdentityError(403, "CONTACTO_NO_COMPROBADO", "Los participantes necesitan cuentas activas y comprobadas.")

    def find_recipient(self, conn: Connection, contact: str) -> UUID:
        users = self.users
        exact = users.c.email == contact.casefold() if "@" in contact else users.c.phone == contact
        rows = conn.execute(select(users.c.id).where(
            exact, users.c.is_active, users.c.contact_verified_at.is_not(None),
        ).limit(2)).scalars().all()
        if len(rows) != 1:
            raise IdentityError(400, "DESTINATARIO_NO_DISPONIBLE", "No se pudo seleccionar un destinatario comprobado.")
        return rows[0]

    def active_point(self, conn: Connection, point_id: UUID, *, lock: bool = False) -> None:
        query = select(self.points.c.id).where(self.points.c.id == point_id, self.points.c.is_active)
        if lock:
            query = query.with_for_update(read=True)
        if conn.execute(query).scalar_one_or_none() is None:
            raise IdentityError(404, "PUNTO_NO_DISPONIBLE", "No se encontró un punto activo.")

    def current_price(self, conn: Connection, point_id: UUID, category: str, hours: int) -> tuple:
        tariffs = self.tariffs
        row = conn.execute(
            select(tariffs).where(tariffs.c.point_id == point_id, tariffs.c.valid_from <= datetime.now(UTC))
            .order_by(tariffs.c.valid_from.desc(), tariffs.c.version.desc()).limit(1)
        ).mappings().one_or_none()
        if row is None:
            raise IdentityError(404, "TARIFA_NO_DISPONIBLE", "No hay una tarifa publicada para el punto.")
        rules = TariffRules.model_validate(row["rules"])
        price = rules.sizes[category].initial_price(hours)
        if price > MAX_AMOUNT:
            raise IdentityError(400, "IMPORTE_FUERA_DE_RANGO", "La cotización supera el importe admitido.")
        return row, rules, price

    @staticmethod
    def extension_amount(order: RowMapping, hours: int) -> Decimal:
        rules = TariffRules.model_validate(order["tariff_snapshot"])
        amount = rules.sizes[order["size_category"]].extension_price(hours)
        if order["service_total"] + amount > MAX_AMOUNT:
            raise IdentityError(400, "IMPORTE_FUERA_DE_RANGO", "El total supera el importe admitido.")
        return amount

    def available_location(self, conn: Connection, order: RowMapping, location_id: UUID) -> RowMapping:
        loc, allocations = self.locations, self.storage
        row = conn.execute(
            select(loc).where(loc.c.id == location_id, loc.c.point_id == order["point_id"]).with_for_update()
        ).mappings().one_or_none()
        occupied = exists(select(allocations.c.id).where(
            allocations.c.location_id == location_id, allocations.c.released_at.is_(None),
        ))
        if (
            row is None or row["state"] != "DISPONIBLE"
            or SIZE_ORDER[row["size_category"]] < SIZE_ORDER[order["size_category"]]
            or conn.scalar(select(occupied))
        ):
            raise conflict("UBICACION_NO_DISPONIBLE", "Selecciona una ubicación disponible y compatible del punto.")
        return row

    def require_state(self, order: RowMapping, state: str, version: int) -> None:
        if order["version"] != version:
            raise conflict("VERSION_CAMBIO", "Actualiza la custodia antes de repetir la operación.")
        if order["state"] != state:
            raise conflict("ESTADO_NO_PERMITE", "El estado de la custodia no permite esta operación.")

    def update_order(self, conn: Connection, order: RowMapping, **values) -> RowMapping:
        return conn.execute(
            self.orders.update().where(self.orders.c.id == order["id"])
            .values(version=order["version"] + 1, **values).returning(self.orders)
        ).mappings().one()

    def register_payment(self, conn: Connection, actor: RowMapping, custody_id: UUID, kind: str, amount: Decimal, body: dict) -> None:
        method = body["payment_method"]
        reference = body.get("payment_reference") if method == "REFERENCIA_MANUAL" else None
        if method == "REFERENCIA_MANUAL" and not reference:
            raise IdentityError(422, "REFERENCIA_REQUERIDA", "Indica la referencia del pago comprobado.")
        conn.execute(self.payments.insert().values(
            id=uuid4(), custody_id=custody_id, received_by=actor["id"], kind=kind,
            amount=amount, method=method, reference=reference, state="REGISTRADO",
        ))

    def claim(self, conn: Connection, actor: RowMapping, operation: str, key: str, body: dict) -> tuple:
        return self.store.claim(conn, actor_id=actor["id"], operation=operation, key=key, payload=body, secret=self.request_key)

    def event(
        self, conn: Connection, actor: RowMapping, order: RowMapping, name: str, correlation_id: UUID,
        *, previous_state: str | None, payload: dict | None = None,
    ) -> None:
        self.store.event(
            conn, actor_id=actor["id"], point_id=order["point_id"], custody_id=order["id"], event_type=name,
            correlation_id=correlation_id, previous_state=previous_state, new_state=order["state"], payload=payload,
        )

    @staticmethod
    def advance_hours(date: datetime, hours: int) -> datetime:
        try:
            return date + timedelta(hours=hours)
        except OverflowError:
            raise IdentityError(400, "PLAZO_FUERA_DE_RANGO", "El plazo supera el rango admitido.") from None
