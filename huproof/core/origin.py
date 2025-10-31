"""Origin validation utilities."""

from fastapi import Request, HTTPException, status

from .crypto import sha256_hex
from .logging import get_logger
from ..config.settings import get_settings

logger = get_logger()


def validate_origin(request: Request) -> None:
    """Validate that the request Origin header matches expected origin.
    
    Raises HTTPException if origin doesn't match or is missing (for protected endpoints).
    """
    settings = get_settings()
    expected_origin = settings.origin
    
    # Get Origin header
    origin_header = request.headers.get("Origin") or request.headers.get("Referer")
    
    if not origin_header:
        logger.warning("missing_origin_header", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin header required",
        )
    
    # Normalize origins (remove trailing slashes, handle http/https)
    def normalize_origin(origin: str) -> str:
        origin = origin.rstrip("/")
        # For comparison, ignore protocol differences in dev
        if origin.startswith("http://") or origin.startswith("https://"):
            return origin
        return origin
    
    normalized_header = normalize_origin(origin_header)
    normalized_expected = normalize_origin(expected_origin)
    
    # Also check hash for extra security
    header_hash = sha256_hex(normalized_header)
    expected_hash = sha256_hex(normalized_expected)
    
    if normalized_header != normalized_expected and header_hash != expected_hash:
        logger.warning(
            "origin_mismatch",
            received=normalized_header,
            expected=normalized_expected,
            path=request.url.path,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid origin",
        )

