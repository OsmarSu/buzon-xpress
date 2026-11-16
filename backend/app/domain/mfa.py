"""TOTP interoperable con RFC 6238; ninguna dependencia de red o framework."""
import base64
from hashlib import sha1
import hmac
import re
from secrets import token_bytes
import struct
from urllib.parse import quote, urlencode

STEP_SECONDS = 30


def new_secret() -> str:
    return base64.b32encode(token_bytes(20)).decode("ascii").rstrip("=")


def totp(secret: str, counter: int, *, digits: int = 6) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.digest(key, struct.pack(">Q", counter), sha1)
    offset = digest[-1] & 15
    number = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7fffffff
    return str(number % (10 ** digits)).zfill(digits)


def accepted_counter(secret: str, code: str, timestamp: float, last_counter: int = -1) -> int | None:
    if not re.fullmatch(r"[0-9]{6}", code):
        return None
    counter = int(timestamp // STEP_SECONDS)
    for candidate in (counter, counter - 1, counter + 1):
        if candidate >= 0 and candidate > last_counter and hmac.compare_digest(totp(secret, candidate), code):
            return candidate
    return None


def enrollment_uri(secret: str, email: str) -> str:
    return "otpauth://totp/" + quote("BUZON Xpress:" + email, safe="") + "?" + urlencode({
        "secret": secret, "issuer": "BUZON Xpress", "algorithm": "SHA1", "digits": "6", "period": "30",
    })


def normalize_recovery_code(code: str) -> str | None:
    normalized = code.replace("-", "").replace(" ", "").upper()
    return normalized if re.fullmatch(r"[0-9A-F]{32}", normalized) else None
