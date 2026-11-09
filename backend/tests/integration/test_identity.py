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
        self.resets = {}
        self.unavailable = False

    def verify_contact(self, recipient, token):
        if self.unavailable:
            raise MailUnavailable
        self.deliveries[recipient] = token

    def password_reset(self, recipient, token):
        if self.unavailable:
            raise MailUnavailable
        self.resets[recipient] = token


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


def test_approved_frontend_uses_partitioned_cookies(database_url):
    api_origin = "https://api.example.net"
    other = "https://other.example.org"
    settings = Settings(
        database_url=database_url,
        session_secret=token_hex(32).encode(),
        allowed_origins=(ORIGIN, api_origin),
        public_origin=ORIGIN,
        cors_origins=(ORIGIN,),
    )
    with TestClient(create_app(settings), base_url=api_origin) as client:
        preflight = {
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token,idempotency-key",
        }
        denied = client.options(API + "/login", headers={**preflight, "Origin": other})
        assert denied.status_code == 400
        assert "access-control-allow-origin" not in denied.headers
        allowed = client.options(API + "/login", headers={**preflight, "Origin": ORIGIN})
        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == ORIGIN
        assert allowed.headers["access-control-allow-credentials"] == "true"

        def send(route, body=None):
            issued = client.get(API + "/csrf", headers={"Origin": ORIGIN})
            return client.post(API + route, json=body, headers={
                "Origin": ORIGIN, "X-CSRF-Token": issued.json()["csrf_token"],
            })

        data = account()
        assert send("/register", data).status_code == 201
        login = send("/login", {key: data[key] for key in ("email", "password")})
        assert login.status_code == 200
        session = next(cookie for cookie in login.headers.get_list("set-cookie") if cookie.startswith("__Host-buzon_session_web="))
        assert all(flag in session for flag in ("Secure", "HttpOnly", "SameSite=none", "Partitioned", "Path=/"))
        assert client.get(API + "/me", headers={"Origin": ORIGIN}).status_code == 200
        assert client.get(API + "/me").status_code == 401
        logout = send("/logout")
        assert logout.status_code == 200
        assert any("Max-Age=0" in cookie and "Partitioned" in cookie for cookie in logout.headers.get_list("set-cookie"))
        assert client.get(API + "/me", headers={"Origin": ORIGIN}).status_code == 401


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


def test_t21_password_reset_consumes_token_and_revokes_all_sessions(environment, assert_contract):
    client, mailbox, engine = environment
    user = account()
    registration = mutate(client, "/register", user)
    assert registration.status_code == 201
    user_id = registration.json()["id"]
    old_credentials = {key: user[key] for key in ("email", "password")}
    sessions = []
    for _ in range(2):
        client.cookies.clear()
        assert mutate(client, "/login", old_credentials).status_code == 200
        sessions.append(client.cookies.get("buzon_session"))
    assert sessions[0] != sessions[1]

    requested = mutate(client, "/password-reset/request", {"email": user["email"]})
    unknown = mutate(client, "/password-reset/request", {"email": account()["email"]})
    for response in (requested, unknown):
        assert_contract(response, "post", "/auth/password-reset/request", 200)
        assert response.json()["state"] == "SOLICITADA"
        assert response.json()["id"] != user_id

    token = mailbox.resets[user["email"]]
    with engine.connect() as connection:
        digest = connection.execute(
            text("SELECT password_reset_hash FROM users WHERE id = :id"), {"id": user_id}
        ).scalar_one()
    assert len(digest) == 64 and digest != token

    new_password = token_hex(18)
    body = {"token": token, "password": new_password}
    completed = mutate(client, "/password-reset/complete", body)
    assert_contract(completed, "post", "/auth/password-reset/complete", 200)
    assert completed.json() == {"id": user_id, "state": "RESTABLECIDA"}
    assert not client.cookies.get("buzon_session")
    assert mutate(client, "/password-reset/complete", body).status_code == 400
    for session in sessions:
        client.cookies.clear()
        client.cookies.set("buzon_session", session, path="/api/v1")
        assert client.get(API + "/me").status_code == 401

    assert mutate(client, "/login", old_credentials).status_code == 401
    assert mutate(client, "/login", {**old_credentials, "password": new_password}).status_code == 200


def test_t21_password_reset_mail_failure_is_generic_and_preserves_token(environment, assert_contract):
    client, mailbox, engine = environment
    user = account()
    assert mutate(client, "/register", user).status_code == 201
    endpoint = "/password-reset/request"
    body = {"email": user["email"]}
    assert mutate(client, endpoint, body).status_code == 200
    token = mailbox.resets[user["email"]]
    mailbox.unavailable = True
    failed = mutate(client, endpoint, body)
    for response in (failed, mutate(client, endpoint, {"email": account()["email"]})):
        assert_contract(response, "post", "/auth" + endpoint, 200)
        assert response.json()["state"] == "SOLICITADA"
    assert mailbox.resets[user["email"]] == token
    with engine.begin() as connection:
        assert connection.execute(
            text("SELECT password_reset_hash FROM users WHERE email = :email"), body
        ).scalar_one() is not None
        connection.execute(
            text("UPDATE users SET password_reset_expires_at = CURRENT_TIMESTAMP - INTERVAL '1 second' WHERE email = :email"),
            body,
        )
    assert mutate(
        client, "/password-reset/complete", {"token": token, "password": token_hex(18)}
    ).status_code == 400


def test_t21_password_reset_rate_limit_is_independent_of_account_existence(environment, assert_contract):
    client, _mailbox, _engine = environment
    addresses = [account()["email"], account()["email"]]
    for address in addresses:
        for _ in range(3):
            assert mutate(client, "/password-reset/request", {"email": address}).status_code == 200
        assert_contract(
            mutate(client, "/password-reset/request", {"email": address}),
            "post", "/auth/password-reset/request", 429,
        )


def test_t01_in_person_verification_is_scoped_idempotent_and_auditable(environment, assert_contract):
    client, mailbox, engine = environment
    admin, participant, staff = (account() for _ in range(3))
    admin_id, user_id, staff_id = (
        mutate(client, "/register", profile).json()["id"] for profile in (admin, participant, staff)
    )
    first_point, second_point = uuid4(), uuid4()
    with engine.begin() as connection:
        for role, uid in (("ADMIN", admin_id), ("OPERADOR", staff_id)):
            connection.execute(text("UPDATE users SET role = :role WHERE id = :id"), {"role": role, "id": uid})
        for point in (first_point, second_point):
            connection.execute(text(
                "INSERT INTO service_points (id, code, name, address, opening_hours)"
                " VALUES (:id, :code, 'Punto de ensayo', 'Dirección sintética', '{}')"
            ), {"id": point, "code": point.hex[:20]})
        connection.execute(text(
            "INSERT INTO staff_assignments (id, user_id, point_id) VALUES (:id, :user, :point)"
        ), {"id": uuid4(), "user": staff_id, "point": second_point})

    reason = "Identidad del participante comprobada en el punto."
    path = f"/admin/users/{user_id}/verify-contact"
    template = "/admin/users/{user_id}/verify-contact"
    key = uuid4().hex

    def verify(*, route=path, idempotency_key=key, evidence=reason):
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf(client)}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return client.post("/api/v1" + route, json={"reason": evidence}, headers=headers)

    def login(profile):
        client.cookies.clear()
        assert mutate(client, "/login", {k: profile[k] for k in ("email", "password")}).status_code == 200

    assert_contract(verify(), "post", template, 401)
    login(participant)
    assert_contract(verify(), "post", template, 403)
    login(admin)
    assert_contract(verify(idempotency_key=None), "post", template, 422)
    assert_contract(verify(), "post", template, 403)
    with engine.begin() as connection:
        for point in (first_point, second_point):
            connection.execute(text(
                "INSERT INTO staff_assignments (id, user_id, point_id) VALUES (:id, :user, :point)"
            ), {"id": uuid4(), "user": admin_id, "point": point})
    assert_contract(verify(), "post", template, 409)
    assert_contract(verify(route=f"/admin/users/{admin_id}/verify-contact"), "post", template, 403)

    # A staff member with one shared point is unambiguous even for a multi-point administrator.
    assert_contract(
        verify(route=f"/admin/users/{staff_id}/verify-contact", idempotency_key=uuid4().hex),
        "post", template, 200,
    )
    with engine.begin() as connection:
        connection.execute(text(
            "UPDATE staff_assignments SET is_active = false WHERE user_id = :user AND point_id = :point"
        ), {"user": admin_id, "point": second_point})
    assert_contract(
        verify(route=f"/admin/users/{staff_id}/verify-contact", idempotency_key=uuid4().hex),
        "post", template, 404,
    )

    completed = verify()
    assert_contract(completed, "post", template, 200)
    assert completed.json()["contact_verified"] is True
    replay = verify()
    assert_contract(replay, "post", template, 200)
    assert replay.json() == completed.json()
    assert_contract(verify(evidence="Otra evidencia"), "post", template, 409)

    with engine.connect() as connection:
        event = connection.execute(text(
            "SELECT actor_id, point_id, correlation_id, payload FROM custody_events"
            " WHERE event_type = 'CONTACTO_COMPROBADO_PRESENCIAL' AND payload->>'user_id' = :user"
        ), {"user": user_id}).mappings().one()
        assert str(event["actor_id"]) == admin_id
        assert event["point_id"] == first_point
        assert str(event["correlation_id"]) == completed.headers["x-correlation-id"]
        assert event["payload"] == {"user_id": user_id, "reason": reason}
    token = mailbox.deliveries[participant["email"]]
    assert mutate(client, "/verify-contact", {"token": token}).status_code == 400
