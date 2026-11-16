import smtplib
import ssl
from email.message import EmailMessage

from app.config import Settings
from app.ports.mail import MailUnavailable


def send_message(settings: Settings, message: EmailMessage) -> None:
    """TLS validado tanto para Gmail como para el transporte SMTP configurable."""
    try:
        if settings.smtp_port == 465:
            channel = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=8, context=ssl.create_default_context())
        else:
            channel = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=8)
        with channel as server:
            if settings.smtp_port != 465:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise MailUnavailable from error


class SmtpIdentityMail:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def verify_contact(self, recipient: str, token: str) -> None:
        link = f"{self.settings.public_origin}/#verificar={token}"
        self.send(
            recipient,
            "Comprueba tu correo · BUZON Xpress",
            f"Abre este enlace para comprobar tu correo:\n\n{link}\n\nVence en 30 minutos.",
        )

    def password_reset(self, recipient: str, token: str) -> None:
        link = f"{self.settings.public_origin}/#recuperar={token}"
        self.send(
            recipient,
            "Restablece tu contraseña · BUZON Xpress",
            f"Abre este enlace para restablecer tu contraseña:\n\n{link}\n\nVence en 30 minutos.",
        )

    def send(self, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.settings.smtp_sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        send_message(self.settings, message)
