from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from os import environ
from secrets import token_hex
from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.adapters.storage.identity import IdentityStore
from app.application.identity import IdentityService
from app.application.mfa import MfaService
from app.config import Settings
from app.domain.identity import IdentityError
from app.domain.mfa import totp
from app.main import create_app

API = "/api/v1/auth"
ORIGIN = "https://buzon.example.com"


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
        pytest.fail("MFA integration requires disposable loopback buzon_test_ database.")
    settings = Settings(url, token_hex(32).encode(), (ORIGIN,), ORIGIN,
                        mfa_encryption_key=Fernet.generate_key())
    mailbox = Mailbox()
    engine = create_engine(url, hide_parameters=True)
    with TestClient(create_app(settings, mail=mailbox), base_url=ORIGIN) as client:
        yield client, mailbox, engine, settings
    engine.dispose()


def post(client, path, body=None):
    token = client.get(API + "/csrf").json()["csrf_token"]
    return client.post(API + path, json=body, headers={"Origin": ORIGIN, "X-CSRF-Token": token})


def register(client, mailbox, *, verify=True):
    profile = {"email": f"mfa-{uuid4().hex}@example.com", "full_name": "MFA test", "password": token_hex(18)}
    response = post(client, "/register", profile)
    assert response.status_code == 201
    if verify:
        assert post(client, "/verify-contact", {"token": mailbox.verify[profile["email"]]}).status_code == 200
    assert post(client, "/login", {k: profile[k] for k in ("email", "password")}).status_code == 200
    return profile, response.json()["id"]


def login(client, profile):
    client.cookies.clear()
    return post(client, "/login", {k: profile[k] for k in ("email", "password")})


def enroll(client, profile):
    setup = post(client, "/mfa/setup", {"password": profile["password"]})
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    code = totp(secret, int(datetime.now(UTC).timestamp() // 30))
    confirmed = post(client, "/mfa/confirm", {"code": code})
    assert confirmed.status_code == 200, confirmed.text
    return secret, confirmed.json()["recovery_codes"]


def test_mfa_password_alone_has_no_session_recovery_is_single_use_and_secret_is_encrypted(environment):
    client, mailbox, engine, _settings = environment
    profile, uid = register(client, mailbox)
    previous_session = client.cookies.get("buzon_session")
    # Keep a second, older session to prove activation revokes it.
    client.cookies.clear()
    assert login(client, profile).status_code == 200
    secret, codes = enroll(client, profile)
    assert len(codes) == len(set(codes)) == 10
    assert client.get(API + "/me").json()["mfa_enabled"] is True
    assert client.get(API + "/mfa").json() == {"enabled": True, "recovery_codes_remaining": 10}
    with engine.connect() as conn:
        row = conn.execute(text("SELECT mfa_secret_ciphertext, mfa_pending_secret_ciphertext FROM users WHERE id=:id"),
                           {"id": uid}).one()
        assert row.mfa_secret_ciphertext != secret
        assert row.mfa_pending_secret_ciphertext is None
        stored = conn.execute(text("SELECT code_hash FROM mfa_recovery_codes WHERE user_id=:id"), {"id": uid}).scalars().all()
        assert all(value not in codes and len(value) == 64 for value in stored)
    current_session = client.cookies.get("buzon_session")
    client.cookies.clear()
    client.cookies.set("buzon_session", previous_session, path="/api/v1")
    assert client.get(API + "/me").status_code == 401
    client.cookies.clear()
    client.cookies.set("buzon_session", current_session, path="/api/v1")
    assert client.get(API + "/me").status_code == 200
    assert post(client, "/logout").status_code == 200

    password_only = login(client, profile)
    assert password_only.status_code == 200 and password_only.json()["mfa_required"] is True
    assert "user" not in password_only.json()
    assert client.cookies.get("buzon_session") is None
    assert client.get(API + "/me").status_code == 401
    challenge = password_only.json()["challenge_token"]
    assert post(client, "/mfa/verify", {"challenge_token": challenge, "code": codes[0]}).status_code == 200
    assert client.get(API + "/me").status_code == 200
    assert post(client, "/mfa/verify", {"challenge_token": challenge, "code": codes[1]}).status_code == 401
    second = login(client, profile).json()["challenge_token"]
    assert post(client, "/mfa/verify", {"challenge_token": second, "code": codes[0]}).status_code == 401
    assert post(client, "/mfa/verify", {"challenge_token": second, "code": codes[1]}).status_code == 200
    assert client.get(API + "/mfa").json()["recovery_codes_remaining"] == 8


def test_mfa_requires_verified_contact_password_and_current_factor_to_change(environment):
    client, mailbox, _engine, _settings = environment
    profile, _uid = register(client, mailbox, verify=False)
    assert post(client, "/mfa/setup", {"password": profile["password"]}).status_code == 403
    assert post(client, "/verify-contact", {"token": mailbox.verify[profile["email"]]}).status_code == 200
    assert post(client, "/mfa/setup", {"password": "wrong"}).status_code == 401
    _secret, codes = enroll(client, profile)
    assert post(client, "/mfa/disable", {"password": "wrong", "code": codes[0]}).status_code == 401
    rotated = post(client, "/mfa/recovery-codes", {"password": profile["password"], "code": codes[0]})
    assert rotated.status_code == 200
    new_codes = rotated.json()["recovery_codes"]
    assert set(new_codes).isdisjoint(codes)
    assert post(client, "/mfa/disable", {"password": profile["password"], "code": codes[1]}).status_code == 401
    assert post(client, "/mfa/disable", {"password": profile["password"], "code": new_codes[0]}).status_code == 200
    assert client.get(API + "/mfa").json() == {"enabled": False, "recovery_codes_remaining": 0}
    assert login(client, profile).json()["user"]["mfa_enabled"] is False


def test_mfa_failures_persist_across_new_challenges_and_app_restart(environment):
    client, mailbox, engine, settings = environment
    profile, uid = register(client, mailbox)
    secret, codes = enroll(client, profile)
    wrong = "000000" if totp(secret, int(datetime.now(UTC).timestamp() // 30)) != "000000" else "999999"
    for _ in range(5):
        challenge = login(client, profile).json()["challenge_token"]
        assert post(client, "/mfa/verify", {"challenge_token": challenge, "code": wrong}).status_code == 401
    with TestClient(create_app(settings, mail=mailbox), base_url=ORIGIN) as restarted:
        assert login(restarted, profile).status_code == 429
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET mfa_locked_until=CURRENT_TIMESTAMP-INTERVAL '1 second' WHERE id=:id"), {"id": uid})
    challenge = login(client, profile).json()["challenge_token"]
    assert post(client, "/mfa/verify", {"challenge_token": challenge, "code": codes[0]}).status_code == 200


def test_mfa_totp_is_not_replayed_and_expired_setup_and_challenge_are_rejected(environment, monkeypatch):
    import app.application.mfa as mfa_module
    client, mailbox, engine, _settings = environment
    fixed = datetime.now(UTC).replace(microsecond=0)

    class Clock:
        current = fixed
        @classmethod
        def now(cls, _timezone):
            return cls.current

    monkeypatch.setattr(mfa_module, "datetime", Clock)
    profile, uid = register(client, mailbox)
    setup = post(client, "/mfa/setup", {"password": profile["password"]}).json()
    secret = setup["secret"]
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET mfa_pending_expires_at=:past WHERE id=:id"), {"past": fixed-timedelta(seconds=1), "id": uid})
    assert post(client, "/mfa/confirm", {"code": totp(secret, int(fixed.timestamp()//30))}).status_code == 400
    secret, _codes = enroll(client, profile)
    code = totp(secret, int(fixed.timestamp() // 30))
    challenge = login(client, profile).json()["challenge_token"]
    assert post(client, "/mfa/verify", {"challenge_token": challenge, "code": code}).status_code == 401
    Clock.current += timedelta(seconds=30)
    fresh = totp(secret, int(Clock.current.timestamp() // 30))
    assert post(client, "/mfa/verify", {"challenge_token": challenge, "code": fresh}).status_code == 200
    next_challenge = login(client, profile).json()["challenge_token"]
    assert post(client, "/mfa/verify", {"challenge_token": next_challenge, "code": fresh}).status_code == 401
    Clock.current += timedelta(minutes=6)
    assert post(client, "/mfa/verify", {"challenge_token": next_challenge, "code": _codes[0]}).status_code == 401


def test_mfa_password_reset_preserves_factor_and_invalidates_pending_login(environment):
    client, mailbox, _engine, _settings = environment
    profile, _uid = register(client, mailbox)
    _secret, codes = enroll(client, profile)
    challenge = login(client, profile).json()["challenge_token"]
    assert post(client, "/password-reset/request", {"email": profile["email"]}).status_code == 200
    profile["password"] = token_hex(18)
    assert post(client, "/password-reset/complete", {"token": mailbox.reset[profile["email"]], "password": profile["password"]}).status_code == 200
    assert post(client, "/mfa/verify", {"challenge_token": challenge, "code": codes[0]}).status_code == 401
    new_challenge = login(client, profile).json()["challenge_token"]
    assert post(client, "/mfa/verify", {"challenge_token": new_challenge, "code": codes[0]}).status_code == 200


def test_mfa_challenge_consumption_is_atomic_under_concurrent_recovery(environment):
    client, mailbox, engine, settings = environment
    profile, uid = register(client, mailbox)
    _secret, codes = enroll(client, profile)
    challenge = login(client, profile).json()["challenge_token"]
    store = IdentityStore(settings.database_url)
    mfa = MfaService(IdentityService(store, None), settings)
    def attempt(_):
        try:
            mfa.verify_login(challenge, codes[0])
            return 200
        except IdentityError as error:
            return error.status
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(attempt, range(2))) == [200, 401]
        with engine.connect() as conn:
            assert conn.execute(text("SELECT count(*) FROM mfa_recovery_codes WHERE user_id=:id"), {"id": uid}).scalar_one() == 9
    finally:
        store.engine.dispose()
