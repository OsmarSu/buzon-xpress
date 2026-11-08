import argparse
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
import smtplib
import ssl
from time import sleep
from uuid import uuid4

from sqlalchemy import Text, cast, create_engine, exists, func, or_, select

from app.adapters.storage.operations import OperationsStore
from app.config import Settings
from app.ports.mail import MailUnavailable


def notify_expired(store: OperationsStore, *, now: datetime, batch: int = 50) -> int:
    orders = store.table("custody_orders")
    events = store.table("custody_events")
    deadline = cast(func.timezone("UTC", orders.c.due_at), Text)
    already_notified = exists(select(events.c.id).where(
        events.c.custody_id == orders.c.id, events.c.event_type == "PLAZO_VENCIDO",
        events.c.payload["deadline_utc"].astext == deadline,
    ))
    query = select(orders.c.id, orders.c.point_id, deadline.label("deadline_utc")).where(
        orders.c.state == "EN_CUSTODIA", orders.c.due_at <= now, ~already_notified,
    ).order_by(orders.c.due_at, orders.c.id).limit(batch).with_for_update(skip_locked=True, of=orders)
    with store.engine.begin() as conn:
        rows = list(conn.execute(query).mappings())
        for row in rows:
            event_id = store.event(
                conn, actor_id=None, point_id=row["point_id"], custody_id=row["id"], event_type="PLAZO_VENCIDO",
                correlation_id=uuid4(), payload={"job": "vencimientos", "deadline_utc": row["deadline_utc"]},
            )
            store.notify(conn, custody_id=row["id"], event_id=event_id, subject="Plazo de custodia vencido")
        return len(rows)


def deliver_one(
    store: OperationsStore, send: Callable[[str, str, str, str], None], *, now: datetime,
) -> bool:
    notices, users, orders = (store.table(name) for name in ("notifications", "users", "custody_orders"))
    query = select(notices, users.c.email, users.c.is_active).join(
        users, users.c.id == notices.c.user_id,
    ).where(
        notices.c.channel == "CORREO", notices.c.state == "PENDIENTE",
        or_(notices.c.next_attempt_at.is_(None), notices.c.next_attempt_at <= now),
    ).order_by(notices.c.created_at, notices.c.id).limit(1).with_for_update(skip_locked=True, of=notices)
    with store.engine.begin() as conn:
        notice = conn.execute(query).mappings().one_or_none()
        if notice is None:
            return False
        attempts = notice["attempts"] + 1
        try:
            if not notice["is_active"]:
                raise MailUnavailable
            send(notice["email"], notice["subject"], notice["body"], str(notice["id"]))
        except MailUnavailable:
            finished = attempts >= 3 or not notice["is_active"]
            updates = {
                "state": "FALLIDA" if finished else "PENDIENTE", "attempts": attempts,
                "next_attempt_at": None if finished else now + timedelta(minutes=2 ** (attempts - 1)),
            }
            if finished and notice["custody_id"] is not None:
                point = conn.execute(select(orders.c.point_id).where(
                    orders.c.id == notice["custody_id"]
                )).scalar_one()
                store.event(
                    conn, actor_id=None, point_id=point, custody_id=notice["custody_id"],
                    event_type="AVISO_CORREO_FALLIDO", correlation_id=uuid4(), payload={"job": "correo"},
                )
        else:
            updates = {"state": "ENVIADA", "attempts": attempts, "next_attempt_at": None, "sent_at": now}
        conn.execute(notices.update().where(notices.c.id == notice["id"]).values(**updates))
        return True


def smtp_sender(settings: Settings):
    def send(recipient: str, subject: str, body: str, notice_id: str) -> None:
        message = EmailMessage()
        message["From"] = settings.smtp_sender
        message["To"] = recipient
        message["Subject"] = subject
        sender_host = settings.smtp_sender.rsplit("@", 1)[-1]
        message["Message-ID"] = f"<buzon-{notice_id}@{sender_host}>"
        message.set_content(body.replace("/#custodia=", f"{settings.public_origin}/#custodia="))
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as server:
                server.starttls(context=ssl.create_default_context())
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise MailUnavailable from error

    return send


def main() -> None:
    parser = argparse.ArgumentParser(description="Procesar vencimientos y avisos de BUZON Xpress.")
    parser.add_argument("--loop", action="store_true", help="Repetir el procesamiento cada 30 segundos.")
    args = parser.parse_args()
    settings = Settings.from_env()
    engine = create_engine(settings.database_url, pool_pre_ping=True, hide_parameters=True)
    try:
        store = OperationsStore(engine, smtp_enabled=bool(settings.smtp_host))
        send = smtp_sender(settings)
        while True:
            notify_expired(store, now=datetime.now(UTC))
            if store.smtp_enabled:
                for _ in range(20):
                    if not deliver_one(store, send, now=datetime.now(UTC)):
                        break
            if not args.loop:
                break
            sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
