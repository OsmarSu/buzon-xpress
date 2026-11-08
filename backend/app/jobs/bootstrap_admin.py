import argparse
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import create_engine, select, text

from app.adapters.storage.operations import OperationsStore
from app.config import database_url
from app.domain.identity import Role


def main() -> None:
    parser = argparse.ArgumentParser(description="Habilitar la primera cuenta administradora de una base nueva.")
    parser.add_argument("user_id", type=UUID)
    parser.add_argument(
        "--comprobacion-presencial", action="store_true",
        help="Declara que el contacto de la primera cuenta se comprobó presencialmente.",
    )
    args = parser.parse_args()
    engine = create_engine(database_url(), hide_parameters=True)
    try:
        store = OperationsStore(engine)
        users = store.table("users")
        with engine.begin() as conn:
            conn.execute(text("SELECT pg_advisory_xact_lock(74182942)"))
            existing = conn.execute(select(users.c.id).where(
                users.c.role == Role.ADMIN, users.c.is_active.is_(True),
            ).limit(1)).scalar_one_or_none()
            if existing is not None:
                raise SystemExit("Ya existe una cuenta administradora activa.")
            account = conn.execute(select(users).where(
                users.c.id == args.user_id, users.c.role == Role.USUARIO, users.c.is_active.is_(True),
            ).with_for_update()).mappings().one_or_none()
            if account is None or (account["contact_verified_at"] is None and not args.comprobacion_presencial):
                raise SystemExit("Indica una cuenta general activa y comprobada o registra la comprobación presencial.")
            now = datetime.now(UTC)
            manual = account["contact_verified_at"] is None
            conn.execute(users.update().where(users.c.id == args.user_id).values(
                role=Role.ADMIN.value, contact_verified_at=account["contact_verified_at"] or now,
                contact_verification_hash=None, verification_expires_at=None,
            ))
            sessions = store.table("sessions")
            conn.execute(sessions.update().where(
                sessions.c.user_id == args.user_id, sessions.c.revoked_at.is_(None),
            ).values(revoked_at=now))
            store.event(
                conn, actor_id=None, point_id=None, event_type="ADMIN_INICIAL_HABILITADO",
                correlation_id=uuid4(), payload={"job": "bootstrap_admin", "user_id": str(args.user_id), "comprobacion_presencial": manual},
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
