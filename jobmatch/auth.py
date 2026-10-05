"""Password hashing with PBKDF2-HMAC-SHA256 (Python standard library)."""

import hashlib
import hmac
import secrets

ITERATIONS = 200_000


def hash_password(password: str, salt: str | None = None) -> str:
    """Return 'salt$hash' for storage. A random salt is generated if none is given."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time comparison of a password against a stored 'salt$hash'."""
    try:
        salt, _digest = stored.split("$", 1)
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)
