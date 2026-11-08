from email import policy
from email.parser import BytesParser
from pathlib import Path
from secrets import token_urlsafe
from shutil import which
from socketserver import BaseRequestHandler, ThreadingTCPServer
from ssl import PROTOCOL_TLS_SERVER, SSLContext, SSLError
from subprocess import DEVNULL, run
from tempfile import TemporaryDirectory
from threading import Thread

import pytest

from app.adapters.mail.smtp import SmtpIdentityMail
from app.config import Settings
from app.ports.mail import MailUnavailable


class LoopbackSmtpHandler(BaseRequestHandler):
    def handle(self):
        channel = self.request
        channel.settimeout(5)
        stream = channel.makefile("rb")
        secured = False
        try:
            channel.sendall(b"220 localhost ESMTP test\r\n")
            while line := stream.readline():
                command = line.split(None, 1)[0].upper()
                if command == b"EHLO":
                    reply = b"250 localhost\r\n" if secured else b"250-localhost\r\n250 STARTTLS\r\n"
                    channel.sendall(reply)
                elif command == b"STARTTLS" and not secured:
                    channel.sendall(b"220 Start TLS\r\n")
                    stream.close()
                    channel = self.server.context.wrap_socket(channel, server_side=True)
                    stream = channel.makefile("rb")
                    secured = True
                elif not secured:
                    channel.sendall(b"530 TLS required\r\n")
                elif command in {b"MAIL", b"RCPT"}:
                    channel.sendall(b"250 accepted\r\n")
                elif command == b"DATA":
                    channel.sendall(b"354 send body\r\n")
                    content = bytearray()
                    while (body_line := stream.readline()) != b".\r\n":
                        if not body_line:
                            return
                        content.extend(body_line)
                    self.server.received.append(BytesParser(policy=policy.default).parsebytes(content))
                    channel.sendall(b"250 accepted\r\n")
                elif command == b"QUIT":
                    channel.sendall(b"221 goodbye\r\n")
                    return
                else:
                    channel.sendall(b"500 unsupported\r\n")
        except SSLError:
            # The test also connects with a client that rejects the peer certificate.
            return
        finally:
            stream.close()
            channel.close()


class LoopbackSmtpServer(ThreadingTCPServer):
    daemon_threads = True

    def __init__(self, cert: Path, key: Path):
        self.context = SSLContext(PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(cert, key)
        self.received = []
        super().__init__(("127.0.0.1", 0), LoopbackSmtpHandler)


@pytest.mark.skipif(which("openssl") is None, reason="La prueba STARTTLS requiere openssl.")
def test_t01_t21_smtp_starttls_verifies_peer_and_delivers_identity_links(monkeypatch):
    with TemporaryDirectory(prefix="buzon-smtp-test-") as tmp:
        cert, key = Path(tmp, "cert.pem"), Path(tmp, "key.pem")
        run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                "-subj", "/CN=127.0.0.1", "-addext", "subjectAltName=IP:127.0.0.1",
                "-keyout", str(key), "-out", str(cert),
            ],
            stdout=DEVNULL, stderr=DEVNULL, check=True,
        )
        with LoopbackSmtpServer(cert, key) as server:
            thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
            thread.start()
            try:
                origin = "https://buzon.example.com"
                recipient = "participant@example.com"
                mail = SmtpIdentityMail(Settings(
                    database_url="", session_secret=b"", allowed_origins=(origin,), public_origin=origin,
                    smtp_host="127.0.0.1", smtp_port=server.server_address[1], smtp_sender="buzon@example.com",
                ))
                verify_token, reset_token = token_urlsafe(32), token_urlsafe(32)
                with pytest.raises(MailUnavailable):
                    mail.verify_contact(recipient, verify_token)
                assert len(server.received) == 0

                monkeypatch.setenv("SSL_CERT_FILE", str(cert))
                mail.verify_contact(recipient, verify_token)
                mail.password_reset(recipient, reset_token)
                assert len(server.received) == 2
                expected = (("verificar", verify_token), ("recuperar", reset_token))
                for message, (fragment, token) in zip(server.received, expected, strict=True):
                    assert str(message["To"]) == recipient
                    if f"{origin}/#{fragment}={token}" not in message.get_content():
                        pytest.fail("El enlace no llegó en el fragmento esperado.")
            finally:
                server.shutdown()
                thread.join()
