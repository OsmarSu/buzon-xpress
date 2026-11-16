from datetime import UTC, datetime
from secrets import token_hex
from unittest.mock import MagicMock

from cryptography.fernet import Fernet
import pytest

from app.domain.mfa import accepted_counter, enrollment_uri, normalize_recovery_code, totp
from app.config import Settings
from app.adapters.mail.smtp import SmtpIdentityMail


def test_rfc6238_sha1_vectors_and_replay_window():
    # RFC 6238 appendix B, ASCII secret 12345678901234567890.
    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    for timestamp, expected in [(59, "94287082"), (1111111109, "07081804"), (1111111111, "14050471"),
                                (1234567890, "89005924"), (2000000000, "69279037"), (20000000000, "65353130")]:
        assert totp(secret, timestamp // 30, digits=8) == expected
    code = totp(secret, 100)
    assert accepted_counter(secret, code, 3000) == 100
    assert accepted_counter(secret, code, 3030) == 100
    assert accepted_counter(secret, code, 3060) is None
    assert accepted_counter(secret, code, 3000, last_counter=100) is None
    assert accepted_counter(secret, "12x456", 3000) is None
    assert "issuer=BUZON+Xpress" in enrollment_uri(secret, "name+test@example.com")
    assert normalize_recovery_code("ABCD1234-" * 3 + "ABCD1234") == "ABCD1234" * 4


def local_config(monkeypatch):
    for name in ("BUZON_SMTP_HOST", "BUZON_SMTP_FROM", "BUZON_SMTP_USER", "BUZON_SMTP_PASSWORD",
                 "BUZON_SMTP_PORT", "BUZON_MAIL_PROVIDER", "BUZON_MFA_ENCRYPTION_KEY", "BUZON_CORS_ORIGINS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("BUZON_ENV", "pruebas")
    monkeypatch.setenv("BUZON_DATABASE_URL", "postgresql+psycopg://test:test@127.0.0.1:5432/buzon_test_config")
    monkeypatch.setenv("BUZON_ALLOWED_ORIGINS", "https://buzon.example.com")
    monkeypatch.setenv("BUZON_SESSION_SECRET", token_hex(32))


def test_gmail_configuration_uses_app_password_and_tls_ports(monkeypatch):
    local_config(monkeypatch)
    monkeypatch.setenv("BUZON_MAIL_PROVIDER", "gmail")
    monkeypatch.setenv("BUZON_SMTP_USER", "buzon.test@gmail.com")
    monkeypatch.setenv("BUZON_SMTP_PASSWORD", "abcd efgh ijkl mnop")
    settings = Settings.from_env()
    assert settings.smtp_host == "smtp.gmail.com"
    assert settings.smtp_port == 587
    assert settings.smtp_sender == settings.smtp_user
    assert len(settings.smtp_password) == 16 and " " not in settings.smtp_password
    monkeypatch.setenv("BUZON_SMTP_PORT", "465")
    assert Settings.from_env().smtp_port == 465
    monkeypatch.setenv("BUZON_SMTP_FROM", "another@example.com")
    with pytest.raises(RuntimeError, match="coincidir"):
        Settings.from_env()
    monkeypatch.delenv("BUZON_SMTP_FROM")
    monkeypatch.setenv("BUZON_SMTP_PORT", "25")
    with pytest.raises(RuntimeError, match="587"):
        Settings.from_env()
    monkeypatch.setenv("BUZON_SMTP_PORT", "587")
    monkeypatch.delenv("BUZON_SMTP_PASSWORD")
    with pytest.raises(RuntimeError, match="aplicación"):
        Settings.from_env()


def test_pilot_requires_valid_distinct_mfa_encryption_key(monkeypatch):
    local_config(monkeypatch)
    monkeypatch.setenv("BUZON_ENV", "piloto")
    monkeypatch.setenv("BUZON_CREDENTIAL_HMAC_KEY", token_hex(32))
    monkeypatch.setenv("BUZON_REQUEST_HMAC_KEY", token_hex(32))
    with pytest.raises(RuntimeError, match="MFA_ENCRYPTION_KEY"):
        Settings.from_env()
    monkeypatch.setenv("BUZON_MFA_ENCRYPTION_KEY", "invalid")
    with pytest.raises(RuntimeError, match="Fernet"):
        Settings.from_env()
    monkeypatch.setenv("BUZON_MFA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    assert len(Settings.from_env().mfa_encryption_key) == 44


@pytest.mark.parametrize("port", [465, 587])
def test_gmail_transport_authenticates_only_after_tls(monkeypatch, port):
    import app.adapters.mail.smtp as transport
    smtp, implicit = MagicMock(), MagicMock()
    monkeypatch.setattr(transport.smtplib, "SMTP", smtp)
    monkeypatch.setattr(transport.smtplib, "SMTP_SSL", implicit)
    settings = Settings("", b"", ("https://buzon.example.com",), "https://buzon.example.com",
                        smtp_host="smtp.gmail.com", smtp_port=port, smtp_sender="buzon.test@gmail.com",
                        smtp_user="buzon.test@gmail.com", smtp_password="synthetic-password")
    SmtpIdentityMail(settings).verify_contact("recipient@example.com", "synthetic-token")
    selected = implicit if port == 465 else smtp
    other = smtp if port == 465 else implicit
    other.assert_not_called()
    server = selected.return_value.__enter__.return_value
    server.login.assert_called_once_with(settings.smtp_user, settings.smtp_password)
    server.send_message.assert_called_once()
    if port == 465:
        assert selected.call_args.kwargs["context"].verify_mode
        server.starttls.assert_not_called()
    else:
        server.starttls.assert_called_once()
        calls = [x[0] for x in server.method_calls]
        assert calls.index("starttls") < calls.index("login") < calls.index("send_message")
