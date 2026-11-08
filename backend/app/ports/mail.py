from typing import Protocol


class MailUnavailable(Exception):
    """The configured transport could not accept a message."""


class IdentityMail(Protocol):
    def verify_contact(self, recipient: str, token: str) -> None: ...
