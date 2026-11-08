from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, MetaData, Table, create_engine, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import RowMapping


class IdentityStore:
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url, pool_pre_ping=True, hide_parameters=True, connect_args={"connect_timeout": 4})
        metadata = MetaData()
        self.users = Table("users", metadata, autoload_with=self.engine)
        self.sessions = Table("sessions", metadata, autoload_with=self.engine)
        self.points = Table("service_points", metadata, autoload_with=self.engine)
        self.assignments = Table("staff_assignments", metadata, autoload_with=self.engine)

    def transaction(self):
        return self.engine.begin()

    def add_user(self, connection: Connection, values: dict[str, Any]) -> RowMapping | None:
        statement = insert(self.users).values(values).on_conflict_do_nothing(index_elements=["email"])
        return connection.execute(statement.returning(*self.users.c)).mappings().one_or_none()

    def find_active_user(self, email: str) -> RowMapping | None:
        users = self.users
        with self.engine.connect() as connection:
            return connection.execute(
                select(users).where(users.c.email == email, users.c.is_active.is_(True))
            ).mappings().one_or_none()

    def add_session(self, user: RowMapping, values: dict[str, Any], previous_hash: str | None, now: datetime) -> bool:
        users, sessions = self.users, self.sessions
        with self.engine.begin() as connection:
            locked = connection.execute(
                select(users.c.id).where(
                    users.c.id == user["id"],
                    users.c.password_hash == user["password_hash"],
                    users.c.is_active.is_(True),
                ).with_for_update()
            ).scalar_one_or_none()
            if locked is None:
                return False
            if previous_hash:
                connection.execute(
                    update(sessions).where(
                        sessions.c.token_hash == previous_hash, sessions.c.revoked_at.is_(None)
                    ).values(revoked_at=now)
                )
            connection.execute(sessions.insert().values(values))
            return True

    def current_user(self, token_hash: str, now: datetime) -> RowMapping | None:
        sessions, users = self.sessions, self.users
        query = select(users).join(sessions, sessions.c.user_id == users.c.id).where(
            sessions.c.token_hash == token_hash,
            sessions.c.expires_at > now,
            sessions.c.revoked_at.is_(None),
            users.c.is_active.is_(True),
        )
        with self.engine.connect() as connection:
            return connection.execute(query).mappings().one_or_none()

    def revoke_session(self, token_hash: str, now: datetime) -> UUID | None:
        sessions = self.sessions
        active_users = select(self.users.c.id).where(self.users.c.is_active.is_(True))
        with self.engine.begin() as connection:
            return connection.execute(
                update(sessions).where(
                    sessions.c.token_hash == token_hash,
                    sessions.c.expires_at > now,
                    sessions.c.revoked_at.is_(None),
                    sessions.c.user_id.in_(active_users),
                ).values(revoked_at=now).returning(sessions.c.id)
            ).scalar_one_or_none()

    def verify_contact(self, token_hash: str, now: datetime) -> UUID | None:
        users = self.users
        with self.engine.begin() as connection:
            return connection.execute(
                update(users).where(
                    users.c.contact_verification_hash == token_hash,
                    users.c.verification_expires_at > now,
                    users.c.is_active.is_(True),
                    users.c.contact_verified_at.is_(None),
                ).values(
                    contact_verified_at=now, contact_verification_hash=None, verification_expires_at=None
                ).returning(users.c.id)
            ).scalar_one_or_none()

    def has_active_assignment(self, user_id: UUID, point_id: UUID) -> bool:
        assignments, points = self.assignments, self.points
        query = select(assignments.c.id).join(points, points.c.id == assignments.c.point_id).where(
            assignments.c.user_id == user_id,
            assignments.c.point_id == point_id,
            assignments.c.is_active.is_(True),
            points.c.is_active.is_(True),
        )
        with self.engine.connect() as connection:
            return connection.execute(query).scalar_one_or_none() is not None
