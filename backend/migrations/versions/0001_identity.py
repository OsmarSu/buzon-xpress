"""Create the identity and point access schema for BZ-001."""

from alembic import op

revision = "0001_identity"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            email VARCHAR(254) NOT NULL UNIQUE,
            full_name VARCHAR(160) NOT NULL,
            phone VARCHAR(24),
            password_hash TEXT NOT NULL,
            role VARCHAR(16) NOT NULL CHECK (role IN ('USUARIO','OPERADOR','ADMIN','AUDITOR')),
            contact_verified_at TIMESTAMPTZ,
            contact_verification_hash CHAR(64),
            verification_expires_at TIMESTAMPTZ,
            password_reset_hash CHAR(64),
            password_reset_expires_at TIMESTAMPTZ,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    op.execute("""
        CREATE TABLE sessions (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            token_hash CHAR(64) NOT NULL UNIQUE,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    op.execute("""
        CREATE TABLE service_points (
            id UUID PRIMARY KEY,
            code VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(120) NOT NULL,
            address TEXT NOT NULL,
            opening_hours JSONB NOT NULL,
            timezone VARCHAR(64) NOT NULL DEFAULT 'America/La_Paz',
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        );
    """)
    op.execute("""
        CREATE TABLE staff_assignments (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            point_id UUID NOT NULL REFERENCES service_points(id),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, point_id)
        );
    """)


def downgrade() -> None:
    op.drop_table("staff_assignments")
    op.drop_table("service_points")
    op.drop_table("sessions")
    op.drop_table("users")
