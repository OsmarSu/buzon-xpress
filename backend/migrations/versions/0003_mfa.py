"""MFA TOTP cifrado, desafíos de acceso y códigos de recuperación de un uso."""
from alembic import op

revision = "0003_mfa"
down_revision = "0002_operations"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE users
    ADD COLUMN mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN mfa_secret_ciphertext TEXT,
    ADD COLUMN mfa_pending_secret_ciphertext TEXT,
    ADD COLUMN mfa_pending_expires_at TIMESTAMPTZ,
    ADD COLUMN mfa_last_counter BIGINT,
    ADD COLUMN mfa_failed_attempts INTEGER NOT NULL DEFAULT 0 CHECK (mfa_failed_attempts BETWEEN 0 AND 5),
    ADD COLUMN mfa_locked_until TIMESTAMPTZ,
    ADD COLUMN mfa_version INTEGER NOT NULL DEFAULT 0 CHECK (mfa_version >= 0),
    ADD CONSTRAINT users_mfa_enabled_secret CHECK (NOT mfa_enabled OR mfa_secret_ciphertext IS NOT NULL);
CREATE TABLE mfa_login_challenges (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 5),
    mfa_version INTEGER NOT NULL,
    previous_session_hash CHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE mfa_recovery_codes (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, code_hash)
);
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.drop_table("mfa_recovery_codes")
    op.drop_table("mfa_login_challenges")
    op.execute("ALTER TABLE users DROP CONSTRAINT users_mfa_enabled_secret")
    for column in ("mfa_version", "mfa_locked_until", "mfa_failed_attempts", "mfa_last_counter",
                   "mfa_pending_expires_at", "mfa_pending_secret_ciphertext", "mfa_secret_ciphertext", "mfa_enabled"):
        op.drop_column("users", column)
