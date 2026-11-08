import smtplib
import ssl
from email.message import EmailMessage

from app.config import Settings
from app.ports.mail import MailUnavailable


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
        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=5) as server:
                server.starttls(context=ssl.create_default_context())
                if self.settings.smtp_user:
                    server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise MailUnavailable from error
