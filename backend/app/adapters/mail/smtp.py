import smtplib
import ssl
from email.message import EmailMessage

from app.config import Settings
from app.ports.mail import MailUnavailable


class SmtpIdentityMail:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def verify_contact(self, recipient: str, token: str) -> None:
        message = EmailMessage()
        message["From"] = self.settings.smtp_sender
        message["To"] = recipient
        message["Subject"] = "Comprueba tu correo · BUZON Xpress"
        link = f"{self.settings.public_origin}/#verificar={token}"
        message.set_content(f"Abre este enlace para comprobar tu correo:\n\n{link}\n\nVence en 30 minutos.")
        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=5) as server:
                server.starttls(context=ssl.create_default_context())
                if self.settings.smtp_user:
                    server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise MailUnavailable from error
