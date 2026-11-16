from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, MetaData, Table, create_engine, delete, func, select, update
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
        self.mfa_challenges = Table("mfa_login_challenges", metadata, autoload_with=self.engine)
        self.mfa_recovery = Table("mfa_recovery_codes", metadata, autoload_with=self.engine)

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
                    users.c.mfa_enabled.is_(False),
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

    def set_password_reset(
        self, connection: Connection, email: str, digest: str, expires_at: datetime
    ) -> bool:
        users = self.users
        result = connection.execute(
            update(users)
            .where(users.c.email == email, users.c.is_active.is_(True))
            .values(password_reset_hash=digest, password_reset_expires_at=expires_at)
            .returning(users.c.id)
        )
        return result.scalar_one_or_none() is not None

    def lock_reset_user(self, connection: Connection, digest: str, now: datetime) -> UUID | None:
        users = self.users
        return connection.execute(
            select(users.c.id).where(
                users.c.password_reset_hash == digest,
                users.c.password_reset_expires_at > now,
                users.c.is_active.is_(True),
            ).with_for_update()
        ).scalar_one_or_none()

    def replace_password(
        self, connection: Connection, user_id: UUID, password_hash: str, now: datetime
    ) -> None:
        users, sessions = self.users, self.sessions
        connection.execute(
            update(users).where(users.c.id == user_id).values(
                password_hash=password_hash,
                password_reset_hash=None,
                password_reset_expires_at=None,
            )
        )
        connection.execute(
            update(sessions)
            .where(sessions.c.user_id == user_id, sessions.c.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        self.delete_mfa_challenges(connection, user_id)

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


    def lock_user(self, connection: Connection, user_id: UUID) -> RowMapping | None:
        return connection.execute(select(self.users).where(
            self.users.c.id == user_id, self.users.c.is_active.is_(True),
        ).with_for_update()).mappings().one_or_none()

    def update_user(self, connection: Connection, user_id: UUID, values: dict[str, Any]) -> None:
        connection.execute(update(self.users).where(self.users.c.id == user_id).values(**values))

    def delete_mfa_challenges(self, connection: Connection, user_id: UUID) -> None:
        connection.execute(delete(self.mfa_challenges).where(self.mfa_challenges.c.user_id == user_id))

    def add_mfa_challenge(self, connection: Connection, values: dict[str, Any]) -> None:
        self.delete_mfa_challenges(connection, values["user_id"])
        connection.execute(self.mfa_challenges.insert().values(**values))

    def lock_challenge_user(self, connection: Connection, digest: str) -> RowMapping | None:
        identifier = select(self.mfa_challenges.c.user_id).where(
            self.mfa_challenges.c.token_hash == digest
        ).scalar_subquery()
        return connection.execute(select(self.users).where(
            self.users.c.id == identifier, self.users.c.is_active.is_(True),
        ).with_for_update()).mappings().one_or_none()

    def mfa_challenge(self, connection: Connection, digest: str) -> RowMapping | None:
        return connection.execute(select(self.mfa_challenges).where(
            self.mfa_challenges.c.token_hash == digest,
        ).with_for_update()).mappings().one_or_none()

    def update_mfa_challenge(self, connection: Connection, identifier: UUID, values: dict[str, Any]) -> None:
        connection.execute(update(self.mfa_challenges).where(
            self.mfa_challenges.c.id == identifier,
        ).values(**values))

    def replace_recovery_codes(self, connection: Connection, user_id: UUID, digests: list[str]) -> None:
        connection.execute(delete(self.mfa_recovery).where(self.mfa_recovery.c.user_id == user_id))
        if digests:
            from uuid import uuid4
            connection.execute(self.mfa_recovery.insert(), [
                {"id": uuid4(), "user_id": user_id, "code_hash": digest} for digest in digests
            ])

    def consume_recovery_code(self, connection: Connection, user_id: UUID, digest: str) -> bool:
        return connection.execute(delete(self.mfa_recovery).where(
            self.mfa_recovery.c.user_id == user_id, self.mfa_recovery.c.code_hash == digest,
        ).returning(self.mfa_recovery.c.id)).scalar_one_or_none() is not None

    def recovery_count(self, user_id: UUID) -> int:
        with self.engine.connect() as connection:
            return connection.execute(select(func.count()).select_from(self.mfa_recovery).where(
                self.mfa_recovery.c.user_id == user_id,
            )).scalar_one()

    def revoke_other_sessions(
        self, connection: Connection, user_id: UUID, current_hash: str, now: datetime,
    ) -> None:
        connection.execute(update(self.sessions).where(
            self.sessions.c.user_id == user_id, self.sessions.c.token_hash != current_hash,
            self.sessions.c.revoked_at.is_(None),
        ).values(revoked_at=now))

    def insert_session(self, connection: Connection, values: dict[str, Any], previous_hash: str | None, now: datetime) -> None:
        if previous_hash:
            connection.execute(update(self.sessions).where(
                self.sessions.c.token_hash == previous_hash, self.sessions.c.revoked_at.is_(None),
            ).values(revoked_at=now))
        connection.execute(self.sessions.insert().values(**values))
