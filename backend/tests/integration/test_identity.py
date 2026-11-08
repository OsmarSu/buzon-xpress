from datetime import UTC, datetime, timedelta
from os import environ
from pathlib import Path
from secrets import token_hex
from uuid import uuid4

import pytest
import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.adapters.storage.identity import IdentityStore
from app.application.identity import IdentityService
from app.config import Settings
from app.domain.identity import IdentityError, Role
from app.main import create_app
from app.ports.mail import MailUnavailable


API = "/api/v1/auth"
ORIGIN = "https://buzon.example.com"
CONTRACT = Path(__file__).resolve().parents[3] / "docs/ingenieria/anexos/openapi.yaml"


class TestMailbox:
    __test__ = False

    def __init__(self):
        self.deliveries = {}
        self.unavailable = False

    def verify_contact(self, recipient, token):
        if self.unavailable:
            raise MailUnavailable
        self.deliveries[recipient] = token


@pytest.fixture(scope="module")
def database_url():
    value = environ.get("BUZON_TEST_DATABASE_URL")
    if not value:
        pytest.fail("Ejecuta infra/probar-identidad.sh para crear PostgreSQL desechable.")
    url = make_url(value)
    if url.host != "127.0.0.1" or not url.database or not url.database.startswith("buzon_test_"):
        pytest.fail("La integración exige una base desechable buzon_test_ en loopback.")
    return value


@pytest.fixture
def environment(database_url):
    settings = Settings(
        database_url=database_url,
        session_secret=token_hex(32).encode(),
        allowed_origins=(ORIGIN,),
        public_origin=ORIGIN,
    )
    mailbox = TestMailbox()
    engine = create_engine(database_url, hide_parameters=True)
    with TestClient(create_app(settings, mail=mailbox), base_url=ORIGIN) as client:
        yield client, mailbox, engine
    engine.dispose()


@pytest.fixture(scope="module")
def assert_contract():
    spec = yaml.safe_load(CONTRACT.read_text())

    def assert_response(response, method, path, status):
        assert response.status_code == status
        schema = spec["paths"][path][method]["responses"][str(status)]["content"]["application/json"]["schema"]
        validator = Draft202012Validator({**schema, "components": spec["components"]}, format_checker=FormatChecker())
        validator.validate(response.json())
        assert response.headers["cache-control"] == "no-store"
        if status >= 400:
            assert response.json()["correlation_id"] == response.headers["x-correlation-id"]

    return assert_response


def account():
    return {
        "email": f"user-{uuid4().hex}@example.com",
        "full_name": "Participante de ensayo",
        "password": token_hex(18),
    }


def csrf(client):
    return client.get(API + "/csrf").json()["csrf_token"]


def mutate(client, route, body=None, *, csrf_token=None, origin=ORIGIN):
    if csrf_token is None:
        csrf_token = csrf(client)
    return client.post(API + route, json=body, headers={"Origin": origin, "X-CSRF-Token": csrf_token})


def test_t01_registration_verification_login_and_revocation(environment, assert_contract):
    client, mailbox, engine = environment
    data = account()
    denied = mutate(client, "/register", {**data, "role": "ADMIN"})
    assert_contract(denied, "post", "/auth/register", 422)
    registration = mutate(client, "/register", data)
    assert_contract(registration, "post", "/auth/register", 201)
    user = registration.json()
    assert user["role"] == "USUARIO"
    assert user["contact_verified"] is False

    token = mailbox.deliveries[data["email"]]
    with engine.connect() as connection:
        stored = connection.execute(
            text("SELECT password_hash, contact_verification_hash FROM users WHERE email = :email"),
            {"email": data["email"]},
        ).one()
        assert stored.password_hash.startswith("$argon2id$")
        assert stored.contact_verification_hash != token

    verification = mutate(client, "/verify-contact", {"token": token})
    assert_contract(verification, "post", "/auth/verify-contact", 200)
    assert mutate(client, "/verify-contact", {"token": token}).status_code == 400

    prelogin = csrf(client)
    credentials = {key: data[key] for key in ("email", "password")}
    wrong = mutate(client, "/login", {**credentials, "password": "incorrecta"})
    assert_contract(wrong, "post", "/auth/login", 401)
    login = mutate(client, "/login", credentials, csrf_token=prelogin)
    assert_contract(login, "post", "/auth/login", 200)
    flags = next(header for header in login.headers.get_list("set-cookie") if header.startswith("buzon_session="))
    assert all(flag in flags for flag in ("HttpOnly", "Secure", "SameSite=lax", "Path=/api/v1"))
    assert login.json()["user"]["contact_verified"] is True
    assert login.json()["user"]["id"] == user["id"]
    bearer = client.cookies.get("buzon_session")
    assert_contract(client.get(API + "/me"), "get", "/auth/me", 200)
    assert mutate(client, "/logout", csrf_token=prelogin).status_code == 403
    assert_contract(mutate(client, "/logout"), "post", "/auth/logout", 200)

    client.cookies.set("buzon_session", bearer, path="/api/v1")
    assert_contract(client.get(API + "/me"), "get", "/auth/me", 401)


def test_t21_origin_csrf_and_expiration(environment, assert_contract):
    client, mailbox, engine = environment
    data = account()
    bootstrap = client.get(API + "/csrf")
    assert_contract(bootstrap, "get", "/auth/csrf", 200)
    signed = bootstrap.json()["csrf_token"]
    assert client.post(API + "/register", json=data).status_code == 403
    assert mutate(client, "/register", data, csrf_token=signed, origin="https://outside.example.com").status_code == 403
    assert mutate(client, "/register", data, csrf_token="0" * 64).status_code == 403

    assert mutate(client, "/register", data, csrf_token=signed).status_code == 201
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE users SET verification_expires_at = :past WHERE email = :email"),
            {"past": datetime.now(UTC) - timedelta(minutes=1), "email": data["email"]},
        )
    assert mutate(client, "/verify-contact", {"token": mailbox.deliveries[data["email"]]}).status_code == 400

    credentials = {key: data[key] for key in ("email", "password")}
    assert mutate(client, "/login", credentials).status_code == 200
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE sessions SET expires_at = :past WHERE user_id = (SELECT id FROM users WHERE email = :email)"),
            {"past": datetime.now(UTC) - timedelta(minutes=1), "email": data["email"]},
        )
    assert_contract(client.get(API + "/me"), "get", "/auth/me", 401)
    assert_contract(client.get("/api/v1/health"), "get", "/health", 200)


def test_unavailable_mail_rolls_back_registration(environment, assert_contract):
    client, mailbox, _engine = environment
    data = account()
    mailbox.unavailable = True
    response = mutate(client, "/register", data)
    assert_contract(response, "post", "/auth/register", 503)
    assert response.json()["code"] == "CORREO_NO_DISPONIBLE"
    mailbox.unavailable = False
    assert mutate(client, "/register", data).status_code == 201
    assert mutate(client, "/register", data).status_code == 409


def test_t02_operator_is_limited_to_assigned_active_point(environment, database_url):
    _client, _mailbox, engine = environment
    store = IdentityStore(database_url)
    service = IdentityService(store, None)
    actor_id, point_id, another_point = uuid4(), uuid4(), uuid4()
    try:
        with engine.begin() as connection:
            connection.execute(store.users.insert().values(
                id=actor_id, email=account()["email"], full_name="Operador de ensayo",
                password_hash=service.dummy_hash, role=Role.OPERADOR,
            ))
            for point in (point_id, another_point):
                connection.execute(store.points.insert().values(
                    id=point, code=point.hex[:20], name="Punto de ensayo", address="Dirección sintética",
                    opening_hours={},
                ))
            connection.execute(store.assignments.insert().values(id=uuid4(), user_id=actor_id, point_id=point_id))
        actor = {"id": actor_id, "role": Role.OPERADOR.value}
        permitted = frozenset({Role.OPERADOR})
        service.require_point_access(actor, point_id, permitted)
        with pytest.raises(IdentityError) as outside:
            service.require_point_access(actor, another_point, permitted)
        assert outside.value.status == 403
        with engine.begin() as connection:
            connection.execute(store.assignments.update().where(
                store.assignments.c.user_id == actor_id
            ).values(is_active=False))
        with pytest.raises(IdentityError):
            service.require_point_access(actor, point_id, permitted)
    finally:
        store.engine.dispose()


def test_login_limits_attempts_before_password_work(environment, assert_contract):
    client, _mailbox, _engine = environment
    data = account()
    credentials = {key: data[key] for key in ("email", "password")}
    signed = csrf(client)
    for _ in range(10):
        assert mutate(client, "/login", credentials, csrf_token=signed).status_code == 401
    response = mutate(client, "/login", credentials, csrf_token=signed)
    assert_contract(response, "post", "/auth/login", 429)
    assert response.json()["code"] == "LIMITE_DE_INTENTOS"
