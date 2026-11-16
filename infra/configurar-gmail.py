#!/usr/bin/env python3
"""Configura Gmail en un archivo de entorno externo sin exponer la credencial."""
import argparse
import getpass
import os
from pathlib import Path
import smtplib
import ssl
import subprocess
import tempfile


def save_environment(path: Path, changes: dict[str, str]) -> None:
    if path.is_symlink():
        raise ValueError("El archivo de entorno no puede ser un enlace simbólico.")
    if path.exists() and path.stat().st_uid != os.getuid():
        raise ValueError("El archivo de entorno debe pertenecer a tu usuario.")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen = set()
    updated = []
    for line in lines:
        name = line.partition("=")[0]
        if name in changes:
            if name not in seen:
                updated.append(name + "=" + changes[name])
                seen.add(name)
        else:
            updated.append(line)
    updated.extend(name + "=" + value for name, value in changes.items() if name not in seen)
    fd, filename = tempfile.mkstemp(prefix=".gmail-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write("\n".join(updated) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(filename, path)
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


def normalize_app_password(value: str) -> str | None:
    candidate = "".join(value.split())
    if len(candidate) == 16 and candidate.isascii() and candidate.isalnum():
        return candidate
    return None


def request_app_password() -> str:
    while True:
        candidate = normalize_app_password(getpass.getpass("Contraseña de aplicación (16 caracteres): "))
        if candidate:
            return candidate
        print("La entrada no tiene el formato de una contraseña de aplicación de Google.")
        print("Pega la clave de 16 caracteres generada en Contraseñas de aplicaciones; los espacios se aceptan.")
        print("El código de Authenticator de 6 dígitos y tu contraseña habitual no corresponden a este paso.")
        print("Puedes volver a pegarla o cancelar con Ctrl+C. No se ha guardado la entrada.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", help="Cuenta Gmail o Google Workspace remitente")
    parser.add_argument("--env-file", type=Path,
                        default=Path.home() / ".local/share/buzon-xpress/publica/app.env")
    parser.add_argument("--port", type=int, choices=(465, 587), default=587)
    parser.add_argument("--restart", action="store_true", help="Reiniciar API y avisos tras guardar")
    args = parser.parse_args()
    if not os.isatty(0):
        parser.error("Usa una terminal interactiva para introducir la contraseña de aplicación.")
    email = (args.email or input("Dirección Gmail remitente: ")).strip()
    if email.count("@") != 1 or any(c.isspace() or ord(c) < 33 for c in email):
        parser.error("Introduce solo una dirección de correo válida.")
    print("Activa la verificación en dos pasos de Google y crea una contraseña de aplicación.")
    print("No uses tu contraseña habitual de Google. La entrada siguiente permanece oculta.")
    password = request_app_password()
    try:
        context = ssl.create_default_context()
        if args.port == 465:
            smtp = smtplib.SMTP_SSL("smtp.gmail.com", args.port, timeout=20, context=context)
        else:
            smtp = smtplib.SMTP("smtp.gmail.com", args.port, timeout=20)
        with smtp:
            smtp.ehlo()
            if args.port == 587:
                smtp.starttls(context=context)
                smtp.ehlo()
            smtp.login(email, password)
        save_environment(args.env_file, {
            "BUZON_MAIL_PROVIDER": "gmail",
            "BUZON_SMTP_HOST": "smtp.gmail.com",
            "BUZON_SMTP_PORT": str(args.port),
            "BUZON_SMTP_FROM": email,
            "BUZON_SMTP_USER": email,
            "BUZON_SMTP_PASSWORD": password,
        })
    except smtplib.SMTPAuthenticationError:
        print("Google rechazó la autenticación. Usa una contraseña de aplicación generada para esta cuenta.")
        print("No uses la contraseña habitual de Google ni un código de Authenticator.")
        return 1
    except (OSError, smtplib.SMTPException, ValueError):
        print("No se pudo validar o guardar Gmail. La configuración anterior se conserva.")
        return 1
    print("Gmail autenticado. Configuración guardada con permisos 600; no se ha enviado ningún mensaje.")
    if args.restart:
        result = subprocess.run(["systemctl", "--user", "restart",
                                 "buzon-publica-api.service", "buzon-publica-avisos.service"], check=False)
        if result.returncode:
            print("La configuración se guardó; revisa el estado de los servicios.")
            return result.returncode
    else:
        print("Reinicia los servicios de API y avisos para usar la nueva configuración.")
    return 0


if __name__ == "__main__":
    try:
        result = main()
    except (KeyboardInterrupt, EOFError):
        print("\nConfiguración interrumpida.")
        result = 130
    except SystemExit as error:
        result = error.code if isinstance(error.code, int) else 1
    if result and os.isatty(0):
        try:
            input("Pulsa Enter para cerrar esta ventana y revisar la configuración de Google.")
        except (KeyboardInterrupt, EOFError):
            pass
    raise SystemExit(result)
