from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from os import environ
from secrets import token_hex, token_urlsafe
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url

from app.adapters.api.custody import custody_router
from app.adapters.api.security import ApiSecurity
from app.adapters.storage.identity import IdentityStore
from app.adapters.storage.operations import OperationsStore
from app.application.identity import IdentityService, token_hash
from app.config import Settings
from app.main import create_app


ORIGIN = "https://buzon.example.com"
API = "/api/v1"
RULES = {
    "currency": "BOB",
    "sizes": {
        size: {
            "base_hours": 24, "block_hours": 12, "base_amount": "10.00", "block_amount": "2.50",
        }
        for size in ("PEQUENO", "MEDIANO", "GRANDE")
    },
}


@dataclass
class Account:
    id: UUID
    contact: str
    token: str


@dataclass
class Case:
    app: object
    store: OperationsStore
    point: UUID
    another_point: UUID
    location: UUID
    outside_location: UUID
    tariff: UUID
    sender: Account
    recipient: Account
    outsider: Account
    operator: Account
    other_operator: Account


@pytest.fixture
def sample():
    url = environ.get("BUZON_TEST_DATABASE_URL")
    if not url:
        pytest.fail("Ejecuta las pruebas contra PostgreSQL desechable con infra/probar-identidad.sh.")
    target = make_url(url)
    if target.host != "127.0.0.1" or not target.database or not target.database.startswith("buzon_test_"):
        pytest.fail("Solo se permiten pruebas con PostgreSQL de ensayo en loopback.")
    settings = Settings(
        database_url=url,
        session_secret=token_hex(32).encode(),
        allowed_origins=(ORIGIN,),
        public_origin=ORIGIN,
    )
    identity_store = IdentityStore(url)
    identity = IdentityService(identity_store, None)
    store = OperationsStore(identity_store.engine)
    app = create_app(settings)
    if "/api/v1/custodies" not in app.openapi()["paths"]:
        app.include_router(custody_router(store, ApiSecurity(identity, settings)), prefix=API)
        app.openapi_schema = None
    now = datetime.now(UTC)

    def add_account(conn, role):
        account_id = uuid4()
        contact = f"{account_id.hex}@example.com"
        token = token_urlsafe(32)
        conn.execute(store.table("users").insert().values(
            id=account_id, email=contact, full_name="Cuenta sintética",
            password_hash="inutilizable-en-pruebas-de-sesion", role=role, contact_verified_at=now,
        ))
        conn.execute(store.table("sessions").insert().values(
            id=uuid4(), user_id=account_id, token_hash=token_hash(token), expires_at=now + timedelta(hours=1),
        ))
        return Account(account_id, contact, token)

    try:
        with store.engine.begin() as conn:
            sender, recipient, outsider = [add_account(conn, "USUARIO") for _ in range(3)]
            operator, other_operator = [add_account(conn, "OPERADOR") for _ in range(2)]
            point, another_point, location, outside_location, tariff = [uuid4() for _ in range(5)]
            for point_id, location_id, staff in ((point, location, operator), (another_point, outside_location, other_operator)):
                conn.execute(store.table("service_points").insert().values(
                    id=point_id, code=point_id.hex[:20], name="Punto de prueba",
                    address="Dirección sintética", opening_hours={"lun": "09:00–17:00"},
                ))
                conn.execute(store.table("storage_locations").insert().values(
                    id=location_id, point_id=point_id, code="A-01", size_category="MEDIANO", state="DISPONIBLE",
                ))
                conn.execute(store.table("staff_assignments").insert().values(
                    id=uuid4(), user_id=staff.id, point_id=point_id,
                ))
            conn.execute(store.table("tariff_versions").insert().values(
                id=tariff, point_id=point, version=1, rules=RULES, valid_from=now - timedelta(days=1),
                created_by=operator.id,
            ))
        yield Case(app, store, point, another_point, location, outside_location, tariff, sender, recipient, outsider, operator, other_operator)
    finally:
        identity_store.engine.dispose()


def client(case: Case, account: Account | None = None) -> TestClient:
    result = TestClient(case.app, base_url=ORIGIN, raise_server_exceptions=False)
    if account:
        result.cookies.set("buzon_session", account.token, path=API)
    return result


def mutate(api, path, body=None, *, key=None):
    token = api.get(f"{API}/auth/csrf").json()["csrf_token"]
    return api.post(API + path, json=body, headers={
        "Origin": ORIGIN, "X-CSRF-Token": token, "Idempotency-Key": key or uuid4().hex,
    })


def create_body(case):
    return {
        "recipient_contact": case.recipient.contact, "point_id": str(case.point),
        "description": "Caja de ensayo", "size_category": "PEQUENO",
    }


def register(case):
    with client(case, case.sender) as api:
        response = mutate(api, "/custodies", create_body(case))
    assert response.status_code == 201, response.text
    return response.json()


def receipt(case, **changes):
    return {
        "location_id": str(case.location), "expected_version": 1, "duration_hours": 26,
        "tariff_id": str(case.tariff), "accepted_amount": "12.50", "payment_method": "EFECTIVO",
        "external_condition": "Embalaje íntegro", **changes,
    }


def entries(case, name, custody_id):
    table = case.store.table(name)
    with case.store.engine.connect() as conn:
        return conn.scalar(select(func.count()).select_from(table).where(table.c.custody_id == UUID(custody_id)))


def test_t02_t03_t06_registration_scope_and_public_privacy(sample):
    case = sample
    key = uuid4().hex
    with client(case, case.sender) as sender, client(case) as public, client(case, case.outsider) as outsider:
        created = mutate(sender, "/custodies", create_body(case), key=key)
        assert created.status_code == 201, created.text
        order = created.json()
        replay = mutate(sender, "/custodies", create_body(case), key=key)
        assert replay.status_code == 201
        assert replay.json()["id"] == order["id"]
        assert "public_reference" not in replay.json()
        assert entries(case, "storage_assignments", order["id"]) == 0

        path = f"/custodies/{order['id']}"
        assert outsider.get(API + path).status_code == 404
        assert outsider.get(f"{API}/custodies?tracking_number={order['tracking_number']}").json() == []
        tracking = public.get(f"{API}/public-tracking/{order['public_reference']}")
        assert tracking.status_code == 200
        assert tracking.json() == {
            "state": "PENDIENTE", "point_name": "Punto de prueba", "opening_hours": {"lun": "09:00–17:00"},
        }
        assert public.get(f"{API}/public-tracking/{order['tracking_number']}").status_code == 404
        with client(case, case.recipient) as recipient:
            renewed = mutate(recipient, path + "/public-reference")
        assert renewed.status_code == 200
        assert public.get(f"{API}/public-tracking/{order['public_reference']}").status_code == 404
        sample_pin = "819204"
        sample_opaque = token_urlsafe(32)
        cancelled = mutate(sender, path + "/cancel", {
            "expected_version": 1, "reason": f"Cambio de plan {sample_pin} {sample_opaque}",
        })
        assert cancelled.json()["state"] == "CANCELADA"
        assert public.get(f"{API}/public-tracking/{renewed.json()['public_reference']}").json()["state"] == "FINALIZADA"

    events = case.store.table("custody_events")
    with case.store.engine.connect() as conn:
        audit = conn.execute(select(events.c.payload).where(
            events.c.custody_id == UUID(order["id"]), events.c.event_type == "CUSTODIA_CANCELADA",
        )).scalar_one()
    assert audit == {"reason": "Cambio de plan [redactado] [redactado]"}

    with client(case, case.other_operator) as outside:
        assert outside.get(f"{API}/inventory", params={"point_id": str(case.point)}).status_code == 403
        assert outside.get(API + path).status_code == 404


def test_t04_t05_t12_t13_receive_scope_price_and_historical_extension(sample):
    case = sample
    order = register(case)
    path = f"/custodies/{order['id']}"
    with client(case, case.operator) as operator, client(case, case.other_operator) as outside:
        quote = operator.get(f"{API}/points/{case.point}/quote", params={"size_category": "PEQUENO", "duration_hours": 26})
        assert quote.json() == {"tariff_id": str(case.tariff), "amount": "12.50", "currency": "BOB", "duration_hours": 26}
        assert mutate(outside, path + "/receive", receipt(case)).status_code == 403
        assert mutate(operator, path + "/receive", receipt(case, accepted_amount="1.00")).status_code == 409
        assert mutate(operator, path + "/receive", receipt(case, location_id=str(case.outside_location))).status_code == 409
        assert entries(case, "service_payments", order["id"]) == 0
        receipt_key = uuid4().hex
        received = mutate(operator, path + "/receive", receipt(case), key=receipt_key)
        assert received.status_code == 200, received.text
        assert received.json()["state"] == "EN_CUSTODIA"
        assert received.json()["service_total"] == "12.50"
        assert mutate(operator, path + "/receive", receipt(case), key=receipt_key).json() == received.json()
        assert mutate(operator, path + "/receive", receipt(case, accepted_amount="1.00"), key=receipt_key).status_code == 409
        inventory = operator.get(f"{API}/inventory", params={"point_id": str(case.point)}).json()
        assert inventory[0]["state"] == "OCUPADA"
        assert operator.get(f"{API}/custodies", params={"tracking_number": order["tracking_number"]}).json()[0]["id"] == order["id"]

        orders, tariffs = case.store.table("custody_orders"), case.store.table("tariff_versions")
        past = datetime.now(UTC) - timedelta(hours=1)
        with case.store.engine.begin() as conn:
            conn.execute(orders.update().where(orders.c.id == UUID(order["id"])).values(due_at=past))
            conn.execute(tariffs.insert().values(
                id=uuid4(), point_id=case.point, version=2, valid_from=past,
                rules={"currency": "BOB", "sizes": {
                    size: {**values, "block_amount": "99.00"} for size, values in RULES["sizes"].items()
                }},
                created_by=case.operator.id,
            ))
        params = {"size_category": "PEQUENO", "duration_hours": 13, "custody_id": order["id"]}
        historical = operator.get(f"{API}/points/{case.point}/quote", params=params)
        assert historical.json() == {"tariff_id": str(case.tariff), "amount": "5.00", "currency": "BOB", "duration_hours": 13}
        assert outside.get(f"{API}/points/{case.point}/quote", params=params).status_code == 403
        extended = mutate(operator, path + "/extend", {
            "expected_version": 2, "additional_hours": 13,
            "accepted_amount": "5.00", "payment_method": "EFECTIVO",
        })
        assert extended.status_code == 200, extended.text
        assert extended.json()["service_total"] == "17.50"
        assert datetime.fromisoformat(extended.json()["due_at"]) == past + timedelta(hours=13)
    assert entries(case, "storage_assignments", order["id"]) == 1
    assert entries(case, "service_payments", order["id"]) == 2
    with client(case, case.sender) as sender:
        assert mutate(sender, path + "/cancel", {"expected_version": 3, "reason": "Cambio de plan"}).status_code == 409


def test_t04_t22_payment_failure_rolls_back_receipt(sample):
    case = sample
    order = register(case)
    tag = uuid4().hex
    function, trigger = f"test_payment_{tag}", f"test_payment_trigger_{tag}"
    custody_id = UUID(order["id"])
    with case.store.engine.begin() as conn:
        conn.execute(text(
            f"CREATE FUNCTION {function}() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'Falla de ensayo' USING ERRCODE = '08006'; END $$"
        ))
        conn.execute(text(
            f"CREATE TRIGGER {trigger} BEFORE INSERT ON service_payments FOR EACH ROW "
            f"WHEN (NEW.custody_id = '{custody_id}'::uuid) EXECUTE FUNCTION {function}()"
        ))
    try:
        with client(case, case.operator) as operator:
            response = mutate(operator, f"/custodies/{custody_id}/receive", receipt(case))
            assert response.status_code == 503, response.text
            assert operator.get(f"{API}/custodies/{custody_id}").json()["state"] == "REGISTRADA"
            assert operator.get(f"{API}/inventory", params={"point_id": str(case.point)}).json()[0]["state"] == "DISPONIBLE"
        assert entries(case, "storage_assignments", order["id"]) == 0
        assert entries(case, "service_payments", order["id"]) == 0
        assert entries(case, "custody_events", order["id"]) == 1
    finally:
        with case.store.engine.begin() as conn:
            conn.execute(text(f"DROP TRIGGER {trigger} ON service_payments"))
            conn.execute(text(f"DROP FUNCTION {function}()"))


def test_t28_twenty_receipts_claim_single_location(sample):
    case = sample
    orders = [register(case)["id"] for _ in range(20)]

    def admit(order_id):
        with client(case, case.operator) as operator:
            return mutate(operator, f"/custodies/{order_id}/receive", receipt(case)).status_code

    with ThreadPoolExecutor(max_workers=20) as workers:
        results = list(workers.map(admit, orders))
    assert results.count(200) == 1, results
    assert results.count(409) == 19, results
    assert sum(entries(case, "service_payments", order_id) for order_id in orders) == 1
    assert sum(entries(case, "storage_assignments", order_id) for order_id in orders) == 1
