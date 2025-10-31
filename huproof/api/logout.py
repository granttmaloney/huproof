"""Logout endpoint for token revocation."""

from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlmodel import Session, select

from ..core.logging import get_logger
from ..core.origin import validate_origin
from ..core.ratelimit import rate_limit_finish
from ..core.security import decode_token
from ..config.settings import get_settings
from ..db.models import SessionToken
from ..db.session import get_session

logger = get_logger()
router = APIRouter()


@router.post(
    "/logout",
    summary="Logout",
    description="Revoke current access token. Requires Bearer token in Authorization header.",
    response_description="Success status",
)
@rate_limit_finish()
def logout(
    *,
    request: Request,
    authorization: str = Header(..., description="Bearer token"),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    """Revoke an access token by marking it as revoked.
    
    Requires Authorization header with Bearer token.
    """
    validate_origin(request)
    
    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Decode token to get JTI
    settings = get_settings()
    try:
        payload = decode_token(token, secret=settings.app_secret)
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token missing JTI",
            )
    except jwt.ExpiredSignatureError:
        # Token already expired, but we can still revoke it if it exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning("invalid_token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    # Find and revoke token
    stmt = select(SessionToken).where(SessionToken.jti == jti)
    token_record = session.exec(stmt).first()
    
    if token_record:
        if token_record.revoked_at is None:
            token_record.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            session.add(token_record)
            logger.info("token_revoked", jti=jti, user_id=token_record.user_id)
        else:
            logger.info("token_already_revoked", jti=jti)
    else:
        # Token not in database (might be from before we started tracking)
        logger.warning("token_not_found", jti=jti)
    
    return {"success": True}


