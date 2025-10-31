from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt


def create_access_token(
    subject: str,
    *,
    secret: str,
    expires_in_seconds: int = 3600,
    claims: Optional[dict[str, Any]] = None,
) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    subject: str
        Principal identifier (e.g., user id)
    secret: str
        Signing secret key
    expires_in_seconds: int
        Expiration in seconds (default: 3600)
    claims: dict[str, Any] | None
        Additional claims to embed in the token
    """

    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {"sub": subject, "iat": int(now.timestamp())}
    if expires_in_seconds:
        payload["exp"] = int((now + timedelta(seconds=expires_in_seconds)).timestamp())
    if claims:
        payload.update(claims)
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, *, secret: str) -> dict[str, Any]:
    """Decode and verify a JWT token."""
    return jwt.decode(token, secret, algorithms=["HS256"])  # type: ignore[no-any-return]


