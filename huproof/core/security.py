import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt


def generate_jti() -> str:
    """Generate a unique JWT ID (JTI) for token tracking."""
    return secrets.token_urlsafe(32)


def create_access_token(
    subject: str,
    *,
    secret: str,
    jti: Optional[str] = None,
    expires_in_seconds: int = 3600,
    claims: Optional[dict[str, Any]] = None,
) -> tuple[str, str]:
    """Create a signed JWT access token with JTI.

    Parameters
    ----------
    subject: str
        Principal identifier (e.g., user id)
    secret: str
        Signing secret key
    jti: str | None
        JWT ID (JTI). If None, generates a new one.
    expires_in_seconds: int
        Expiration in seconds (default: 3600)
    claims: dict[str, Any] | None
        Additional claims to embed in the token

    Returns
    -------
    tuple[str, str]
        (token_string, jti) - The encoded token and its JTI
    """

    now = datetime.now(tz=timezone.utc)
    jti_value = jti or generate_jti()
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "jti": jti_value,
    }
    if expires_in_seconds:
        payload["exp"] = int((now + timedelta(seconds=expires_in_seconds)).timestamp())
    if claims:
        payload.update(claims)
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, jti_value


def decode_token(token: str, *, secret: str) -> dict[str, Any]:
    """Decode and verify a JWT token."""
    return jwt.decode(token, secret, algorithms=["HS256"])  # type: ignore[no-any-return]


