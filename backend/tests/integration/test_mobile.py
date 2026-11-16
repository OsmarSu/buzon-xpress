from datetime import UTC, datetime, timedelta
from os import environ
from secrets import token_hex
from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.config import Settings
from app.domain.mfa import totp
from app.main import create_app

ORIGIN = "https://buzon.example.com"
AUTH = "/api/v1/auth"
NATIVE = "/api/v1/mobile/auth"


class Mailbox:
    def __init__(self):
        self.verify = {}
        self.reset = {}

    def verify_contact(self, recipient, token):
        self.verify[recipient] = token

    def password_reset(self, recipient, token):
        self.reset[recipient] = token


@pytest.fixture
def environment():
    url = environ.get("BUZON_TEST_DATABASE_URL", "")
    parsed = make_url(url)
    if parsed.host != "127.0.0.1" or not parsed.database or not parsed.database.startswith("buzon_test_"):
        pytest.fail("Mobile integration requires disposable loopback buzon_test_ database.")
    settings = Settings(url, token_hex(32).encode(), (ORIGIN,), ORIGIN, mfa_encryption_key=Fernet.generate_key())
    mail = Mailbox()
    app = create_app(settings, mail=mail)
    engine = create_engine(url, hide_parameters=True)
    with TestClient(app, base_url=ORIGIN) as web, TestClient(app, base_url=ORIGIN) as mobile:
        yield web, mobile, mail, engine
    engine.dispose()


def web_post(client, path, body=None):
    csrf = client.get(AUTH + "/csrf").json()["csrf_token"]
    return client.post(AUTH + path, json=body, headers={"Origin": ORIGIN, "X-CSRF-Token": csrf})


def profile(web, mail):
    data = {"email": f"android-{uuid4().hex}@example.com", "full_name": "Android test", "password": token_hex(18)}
    registered = web_post(web, "/register", data)
    assert registered.status_code == 201
    assert web_post(web, "/verify-contact", {"token": mail.verify[data["email"]]}).status_code == 200
    return data, registered.json()["id"]


def credentials(data):
    return {key: data[key] for key in ("email", "password")}


def test_mobile_session_is_hashed_revocable_and_distinct_from_browser_cookies(environment):
    web, mobile, mail, engine = environment
    data, uid = profile(web, mail)
    assert web_post(web, "/login", credentials(data)).status_code == 200
    web_token = web.cookies.get("buzon_session")
    result = mobile.post(NATIVE + "/login", json=credentials(data))
    assert result.status_code == 200
    assert "set-cookie" not in result.headers
    token = result.json()["access_token"]
    assert token.startswith("mob_") and len(token) == 47
    headers = {"Authorization": "Bearer " + token}
    assert mobile.get(AUTH + "/me", headers=headers).json()["id"] == uid
    assert mobile.get(AUTH + "/me", headers={"Authorization": "Bearer " + web_token}).status_code == 401
    mobile.cookies.set("buzon_session", token, path="/api/v1")
    assert mobile.get(AUTH + "/me").status_code == 401
    mobile.cookies.clear()
    with engine.connect() as conn:
        hashes = conn.execute(text("SELECT token_hash FROM sessions WHERE user_id=:id"), {"id": uid}).scalars().all()
        assert all(len(value) == 64 and value != token for value in hashes)
    assert mobile.post(NATIVE + "/logout", json={}, headers=headers).status_code == 200
    assert mobile.get(AUTH + "/me", headers=headers).status_code == 401
    assert web.get(AUTH + "/me").status_code == 200
    assert web.post(AUTH + "/logout", json={}).status_code == 403


def test_mobile_endpoints_reject_browser_origins_cookies_and_privilege_injection(environment):
    web, mobile, mail, _engine = environment
    data, _uid = profile(web, mail)
    assert mobile.post(NATIVE + "/login", json=credentials(data), headers={"Origin": ORIGIN}).status_code == 403
    assert mobile.post(NATIVE + "/login", json=credentials(data), headers={"Cookie": "buzon_session=anything"}).status_code == 403
    assert mobile.post(NATIVE + "/register", json={**data, "role": "ADMIN"}).status_code == 422
    bad = mobile.post(NATIVE + "/login", json={**credentials(data), "password": "wrong"})
    assert bad.status_code == 401 and "access_token" not in bad.json()
    assert mobile.get("/api/v1/custodies", headers={"Authorization": "Bearer mob_" + "a"*43}).status_code == 401


def test_mobile_mfa_requires_the_second_factor_and_keeps_challenges_separate(environment):
    web, mobile, mail, _engine = environment
    data, _uid = profile(web, mail)
    assert web_post(web, "/login", credentials(data)).status_code == 200
    secret = web_post(web, "/mfa/setup", {"password": data["password"]}).json()["secret"]
    code = totp(secret, int(datetime.now(UTC).timestamp() // 30))
    confirmed = web_post(web, "/mfa/confirm", {"code": code})
    assert confirmed.status_code == 200
    recovery = confirmed.json()["recovery_codes"]
    response = mobile.post(NATIVE + "/login", json=credentials(data))
    assert response.status_code == 200 and response.json()["mfa_required"]
    assert "access_token" not in response.json() and "set-cookie" not in response.headers
    challenge = response.json()["challenge_token"]
    assert challenge.startswith("mfc_") and len(challenge) == 47
    verified = mobile.post(NATIVE + "/mfa/verify", json={"challenge_token": challenge, "code": recovery[0]})
    assert verified.status_code == 200 and verified.json()["access_token"].startswith("mob_")
    assert mobile.post(NATIVE + "/mfa/verify", json={"challenge_token": challenge, "code": recovery[1]}).status_code == 401
    assert web_post(web, "/mfa/verify", {"challenge_token": challenge, "code": recovery[1]}).status_code == 422
    web_challenge = web_post(web, "/login", credentials(data)).json()["challenge_token"]
    assert mobile.post(NATIVE + "/mfa/verify", json={"challenge_token": web_challenge, "code": recovery[1]}).status_code == 422


def test_mobile_expiration_reset_and_mutation_authorization(environment):
    web, mobile, mail, engine = environment
    data, uid = profile(web, mail)
    token = mobile.post(NATIVE + "/login", json=credentials(data)).json()["access_token"]
    headers = {"Authorization": "Bearer " + token, "Idempotency-Key": str(uuid4())}
    assert mobile.get("/api/v1/custodies", headers=headers).status_code == 200
    with engine.begin() as conn:
        conn.execute(text("UPDATE sessions SET expires_at=CURRENT_TIMESTAMP-INTERVAL '1 second' WHERE user_id=:id"), {"id": uid})
    assert mobile.get(AUTH + "/me", headers=headers).status_code == 401
    token = mobile.post(NATIVE + "/login", json=credentials(data)).json()["access_token"]
    headers["Authorization"] = "Bearer " + token
    # The explicit token passes CSRF transport, but authorization still applies.
    denied = mobile.post("/api/v1/admin/points", headers=headers, json={
        "name": "Forbidden", "address": "Not created", "opening_hours": {"Lunes": "09:00–17:00"}, "is_active": True,
    })
    assert denied.status_code == 403
    assert mobile.post(NATIVE + "/password-reset/request", json={"email": data["email"]}).status_code == 200
    reset = web_post(web, "/password-reset/complete", {"token": mail.reset[data["email"]], "password": token_hex(18)})
    assert reset.status_code == 200
    assert mobile.get(AUTH + "/me", headers=headers).status_code == 401


def test_login_limits_are_shared_between_web_and_mobile(environment):
    web, mobile, mail, _engine = environment
    data, _uid = profile(web, mail)
    wrong = {**credentials(data), "password": "wrong"}
    for _ in range(5):
        assert web_post(web, "/login", wrong).status_code == 401
        assert mobile.post(NATIVE + "/login", json=wrong).status_code == 401
    assert mobile.post(NATIVE + "/login", json=credentials(data)).status_code == 429
