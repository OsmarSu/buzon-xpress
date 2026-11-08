from threading import Lock
from time import monotonic

from app.domain.identity import IdentityError


class IdentityRateLimit:
    """A bounded, process-local limit for the single-worker development server."""

    def __init__(self, *, window_seconds: int = 60, capacity: int = 4096) -> None:
        self.window_seconds = window_seconds
        self.capacity = capacity
        self.reset_at = monotonic() + window_seconds
        self.attempts: dict[tuple[str, str], int] = {}
        self.lock = Lock()

    def check(self, operation: str, origin: str, limit: int) -> None:
        key = operation, origin
        with self.lock:
            now = monotonic()
            if now >= self.reset_at:
                self.attempts.clear()
                self.reset_at = now + self.window_seconds
            if self.attempts.get(key, 0) >= limit or (key not in self.attempts and len(self.attempts) >= self.capacity):
                raise IdentityError(429, "LIMITE_DE_INTENTOS", "Espera un minuto antes de volver a intentarlo.")
            self.attempts[key] = self.attempts.get(key, 0) + 1
