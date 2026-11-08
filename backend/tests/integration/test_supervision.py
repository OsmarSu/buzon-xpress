from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from os import environ
from secrets import token_hex, token_urlsafe
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from app.adapters.storage.operations import OperationsStore
from app.config import Settings
from app.jobs.maintenance import deliver_one, notify_expired
from app.main import create_app
from app.ports.mail import MailUnavailable

ORIGIN = "https://buzon.example.com"
API = "/api/v1"


class Scenario:
    def __init__(self, url):
        self.now = datetime.now(UTC)
        self.engine = create_engine(url, hide_parameters=True)
        self.store = OperationsStore(self.engine)
        settings = Settings(url, token_hex(32).encode(), (ORIGIN,), ORIGIN)
        self.app = create_app(settings)
        self.point, self.other_point, self.order, self.location = (uuid4() for _ in range(4))
        self.accounts = {}
        with self.engine.begin() as conn:
            points = self.store.table("service_points")
            for point in (self.point, self.other_point):
                conn.execute(points.insert().values(
                    id=point, code=point.hex[:20], name="Punto sintético", address="Dirección de ensayo", opening_hours={},
                ))
            for label, role, point in (
                ("sender", "USUARIO", None), ("recipient", "USUARIO", None), ("new", "USUARIO", None),
                ("admin1", "ADMIN", self.point), ("admin2", "ADMIN", self.point),
                ("operator", "OPERADOR", self.point), ("operator2", "OPERADOR", self.point),
                ("outsider", "ADMIN", self.other_point),
            ):
                self._account(conn, label, role, point)
            conn.execute(self.store.table("storage_locations").insert().values(
                id=self.location, point_id=self.point, code="A-01", size_category="PEQUENO", state="OCUPADA",
            ))
            conn.execute(self.store.table("custody_orders").insert().values(
                id=self.order, tracking_number=self.order.hex, public_reference_hash=sha256(self.order.bytes).hexdigest(),
                sender_id=self.accounts["sender"][0], recipient_id=self.accounts["recipient"][0], point_id=self.point,
                description="Bulto sintético", size_category="PEQUENO", state="EN_CUSTODIA",
                received_at=self.now - timedelta(hours=1), due_at=self.now + timedelta(hours=2),
            ))
            conn.execute(self.store.table("storage_assignments").insert().values(
                id=uuid4(), custody_id=self.order, point_id=self.point, location_id=self.location, assigned_at=self.now,
            ))

    def _account(self, conn, label, role, point):
        user_id, token = uuid4(), token_urlsafe(32)
        self.accounts[label] = user_id, token
        conn.execute(self.store.table("users").insert().values(
            id=user_id, email=f"qa-{user_id.hex}@example.com", full_name="Cuenta sintética", role=role,
            contact_verified_at=self.now, password_hash="ensayo-sesion-preparada",
        ))
        conn.execute(self.store.table("sessions").insert().values(
            id=uuid4(), user_id=user_id, token_hash=sha256(token.encode()).hexdigest(),
            expires_at=self.now + timedelta(hours=1),
        ))
        if point is not None:
            conn.execute(self.store.table("staff_assignments").insert().values(
                id=uuid4(), user_id=user_id, point_id=point,
            ))

    @contextmanager
    def client(self, label):
        with TestClient(self.app, base_url=ORIGIN) as client:
            client.cookies.set("buzon_session", self.accounts[label][1], path=API)
            yield client

    def change(self, label, path, body=None, *, method="POST", key=None):
        with self.client(label) as client:
            token = client.get(API + "/auth/csrf").raise_for_status().json()["csrf_token"]
            return client.request(method, API + path, json=body, headers={
                "Origin": ORIGIN, "X-CSRF-Token": token, "Idempotency-Key": key or uuid4().hex,
            })

    def get(self, label, path, **params):
        with self.client(label) as client:
            return client.get(API + path, params=params)

    def row(self, name, record_id):
        table = self.store.table(name)
        with self.engine.connect() as conn:
            return conn.execute(select(table).where(table.c.id == record_id)).mappings().one()


@pytest.fixture
def scenario():
    url = environ.get("BUZON_TEST_DATABASE_URL")
    if not url:
        pytest.fail("Ejecuta infra/probar-identidad.sh con PostgreSQL desechable.")
    parsed = make_url(url)
    if parsed.host != "127.0.0.1" or not parsed.database or not parsed.database.startswith("buzon_test_"):
        pytest.fail("Se requiere una base desechable buzon_test_ en loopback.")
    case = Scenario(url)
    try:
        yield case
    finally:
        case.engine.dispose()


def test_t10_return_requires_two_people_and_releases_location_once(scenario):
    s = scenario
    requested = s.change("admin1", "/recovery-requests", {
        "custody_id": str(s.order), "purpose": "AUTORIZAR_DEVOLUCION", "evidence": "Emisor y bulto cotejados.",
    })
    assert requested.status_code == 201
    request_id = requested.json()["id"]
    decision = {"decision": "APROBAR", "note": "Evidencia y emisor verificados por separado."}
    assert s.change("admin1", f"/recovery-requests/{request_id}/decision", decision).status_code == 403
    assert s.change("outsider", f"/recovery-requests/{request_id}/decision", decision).status_code == 403
    assert s.change("admin2", f"/recovery-requests/{request_id}/decision", decision).json()["state"] == "APROBADA"
    prepared = s.change("operator", f"/custodies/{s.order}/return-authorization", {
        "recovery_request_id": request_id, "expected_version": 1, "sender_check": "COMPROBACION_VISUAL_COMPLETADA",
    }).raise_for_status().json()
    assert prepared["location_code"] == "A-01"
    assert s.row("storage_locations", s.location)["state"] == "OCUPADA"
    confirmation = {
        "authorization_id": prepared["authorization_id"], "expected_version": prepared["version"],
        "physically_delivered": True,
    }
    route = f"/custodies/{s.order}/return-handover"
    assert s.change("operator2", route, confirmation).status_code == 403
    key = uuid4().hex
    result = s.change("operator", route, confirmation, key=key).raise_for_status().json()
    assert result["kind"] == "DEVOLUCION"
    assert s.change("operator", route, confirmation, key=key).raise_for_status().json() == result
    changed = {**confirmation, "expected_version": prepared["version"] + 1}
    assert s.change("operator", route, changed, key=key).status_code == 409
    assert s.row("storage_locations", s.location)["state"] == "DISPONIBLE"
    assert s.row("custody_orders", s.order)["state"] == "DEVUELTA"


def test_t14_change_recipient_revokes_credentials_only_after_approval(scenario):
    s = scenario
    credential = uuid4()
    with s.engine.begin() as conn:
        conn.execute(s.store.table("pickup_credentials").insert().values(
            id=credential, custody_id=s.order, verifier=token_hex(32), state="ACTIVA",
            expires_at=s.now + timedelta(minutes=10),
        ))
    path = "/recovery-requests"
    body = {"custody_id": str(s.order), "purpose": "CAMBIAR_DESTINATARIO", "evidence": "Cambio comprobado en punto."}
    assert s.change("operator", path, body).status_code == 422
    body["target_recipient_id"] = str(s.accounts["new"][0])
    created = s.change("operator", path, body).raise_for_status().json()
    assert s.row("pickup_credentials", credential)["state"] == "ACTIVA"
    response = s.change("admin1", f"{path}/{created['id']}/decision", {
        "decision": "APROBAR", "note": "Se verificó la nueva cuenta y la evidencia.",
    }).raise_for_status()
    assert response.json()["state"] == "EJECUTADA"
    assert s.row("pickup_credentials", credential)["state"] == "REVOCADA"
    assert s.row("custody_orders", s.order)["recipient_id"] == s.accounts["new"][0]
    assert s.row("storage_locations", s.location)["state"] == "OCUPADA"


def test_t18_late_handover_reconciliation_keeps_original_authorization(scenario):
    s = scenario
    credential, authorization = uuid4(), uuid4()
    orders = s.store.table("custody_orders")
    with s.engine.begin() as conn:
        conn.execute(s.store.table("pickup_credentials").insert().values(
            id=credential, custody_id=s.order, verifier=token_hex(32), state="RETENIDA",
            expires_at=s.now - timedelta(minutes=2),
        ))
        conn.execute(s.store.table("pickup_authorizations").insert().values(
            id=authorization, custody_id=s.order, operator_id=s.accounts["operator"][0],
            credential_id=credential, purpose="RETIRO", person_check="COMPROBACION_VISUAL_COMPLETADA",
            state="VALIDADA", expires_at=s.now - timedelta(minutes=1),
        ))
        conn.execute(orders.update().where(orders.c.id == s.order).values(state="RETIRO_EN_CURSO", version=2))
    incident = s.change("operator", f"/custodies/{s.order}/incidents", {
        "kind": "RESPUESTA_PERDIDA", "description": "Operador entregó antes del corte y cotejó el comprobante.",
        "is_blocking": False,
    }).raise_for_status().json()
    assert incident["is_blocking"] is True
    recovery = s.change("operator", "/recovery-requests", {
        "custody_id": str(s.order), "purpose": "RECONCILIAR_ENTREGA",
        "evidence": "La constancia presencial y el cotejo acreditan una entrega previa al corte.",
    }).raise_for_status().json()
    decided = s.change("admin2", f"/recovery-requests/{recovery['id']}/decision", {
        "decision": "APROBAR", "note": "Confirmación documental cotejada por segundo responsable.",
    }).raise_for_status().json()
    assert decided["state"] == "EJECUTADA"
    handovers = s.store.table("handovers")
    with s.engine.connect() as conn:
        handover = conn.execute(select(handovers).where(handovers.c.custody_id == s.order)).mappings().one()
    assert handover["authorization_id"] == authorization
    assert handover["operator_id"] == s.accounts["operator"][0]
    assert str(handover["reconciliation_request_id"]) == recovery["id"]
    assert s.row("storage_locations", s.location)["state"] == "DISPONIBLE"
    assert s.change("admin2", f"/incidents/{incident['id']}/resolve", {
        "reason": "Se reconcilió la entrega y se comprobó el espacio liberado.",
    }).raise_for_status().json()["state"] == "RESUELTA"


def test_t15_t16_t17_admin_scope_occupied_space_and_audit(scenario):
    s = scenario
    change = {"state": "FUERA_SERVICIO", "expected_version": 1, "reason": "Mantenimiento programado."}
    route = f"/admin/locations/{s.location}"
    assert s.change("outsider", route, change, method="PATCH").status_code == 403
    assert s.change("admin1", route, change, method="PATCH").status_code == 409
    created = s.change("admin1", "/admin/locations", {
        "point_id": str(s.point), "code": "B-01", "size_category": "MEDIANO",
    }).raise_for_status().json()
    assert s.change("admin1", f"/admin/locations/{created['id']}", change, method="PATCH").status_code == 200
    assert s.get("outsider", "/audit/events", point_id=s.point).status_code == 403
    events = s.get("admin1", "/audit/events", point_id=s.point).raise_for_status().json()
    assert "UBICACION_ESTADO" in {event["event_type"] for event in events}
    assert all(set(event) == {"id", "event_type", "created_at", "correlation_id", "actor_id", "custody_id"} for event in events)
    audit_table = s.store.table("custody_events")
    with pytest.raises(DBAPIError) as violation, s.engine.begin() as conn:
        conn.execute(audit_table.update().where(audit_table.c.point_id == s.point).values(event_type="ALTERADO"))
    assert violation.value.orig.sqlstate == "55000"
    period = {"from": (s.now - timedelta(days=1)).isoformat(), "to": (s.now + timedelta(days=1)).isoformat()}
    report = s.get("admin1", "/reports", point_id=s.point, **period).raise_for_status().json()
    assert report["occupied_locations"] == 1
    assert report["available_locations"] == 0
    assert report["completed_custodies"] == 0
    assert "1 ubicaciones utilizables" in report["data_quality_note"]


def test_t11_t13_expiry_notices_and_smtp_retries_keep_inventory(scenario):
    s = scenario
    s.store.smtp_enabled = True
    orders, notices = s.store.table("custody_orders"), s.store.table("notifications")
    with s.engine.begin() as conn:
        conn.execute(orders.update().where(orders.c.id == s.order).values(due_at=s.now - timedelta(minutes=1)))
    assert notify_expired(s.store, now=s.now) == 1
    assert notify_expired(s.store, now=s.now) == 0
    assert s.row("storage_locations", s.location)["state"] == "OCUPADA"
    sender_mailbox = s.get("sender", "/notifications").raise_for_status().json()
    assert sender_mailbox[0]["subject"] == "Plazo de custodia vencido"
    notice_id = sender_mailbox[0]["id"]
    assert s.change("outsider", f"/notifications/{notice_id}/read").status_code == 404
    assert s.change("sender", f"/notifications/{notice_id}/read").json()["state"] == "LEIDA"
    assert s.get("sender", "/notifications").json()[0]["read_at"] is not None

    messages = []

    def fail(recipient, subject, body, message_id):
        messages.append((subject, body, message_id))
        raise MailUnavailable

    for minutes in (0, 1, 3):
        clock = s.now + timedelta(minutes=minutes)
        assert deliver_one(s.store, fail, now=clock)
        assert deliver_one(s.store, fail, now=clock)
        assert not deliver_one(s.store, fail, now=clock)
    assert len({message_id for _, _, message_id in messages}) == 2
    assert len(messages) == 6
    with s.engine.connect() as conn:
        statuses = conn.execute(select(notices.c.state, notices.c.attempts).where(
            notices.c.custody_id == s.order, notices.c.channel == "CORREO",
        )).all()
    assert statuses == [("FALLIDA", 3), ("FALLIDA", 3)]
    assert s.row("custody_orders", s.order)["state"] == "EN_CUSTODIA"
