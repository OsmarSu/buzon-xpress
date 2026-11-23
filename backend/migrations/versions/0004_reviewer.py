"""Permitir el rol de revisión de incidencias y solicitudes."""

from alembic import op

revision = "0004_reviewer"
down_revision = "0003_mfa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("users_role_check", "users", type_="check")
    op.create_check_constraint(
        "users_role_check", "users", "role IN ('USUARIO','OPERADOR','ADMIN','AUDITOR','REVISOR')",
    )


def downgrade() -> None:
    op.execute("""
        UPDATE sessions SET revoked_at = CURRENT_TIMESTAMP
        WHERE revoked_at IS NULL AND user_id IN (SELECT id FROM users WHERE role = 'REVISOR')
    """)
    op.execute("UPDATE users SET role = 'USUARIO' WHERE role = 'REVISOR'")
    op.drop_constraint("users_role_check", "users", type_="check")
    op.create_check_constraint(
        "users_role_check", "users", "role IN ('USUARIO','OPERADOR','ADMIN','AUDITOR')",
    )
