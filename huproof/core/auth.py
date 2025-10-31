"""Authentication dependencies for protected endpoints."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Header, status
from sqlmodel import Session, select

from .logging import get_logger
from .security import decode_token
from ..config.settings import get_settings
from ..db.models import SessionToken, User
from ..db.session import get_session

logger = get_logger()


def get_current_user(
    authorization: Annotated[str, Header(..., description="Bearer token")],
    session: Session = Depends(get_session),
) -> User:
    """Dependency to get current authenticated user from JWT token.
    
    Verifies token signature, expiration, and revocation status.
    Raises HTTPException if token is invalid, expired, or revoked.
    """
    settings = get_settings()
    
    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Decode and verify token
    try:
        payload = decode_token(token, secret=settings.app_secret)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning("invalid_token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if token is revoked
    if jti:
        stmt = select(SessionToken).where(SessionToken.jti == jti)
        token_record = session.exec(stmt).first()
        if token_record and token_record.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Get user
    stmt = select(User).where(User.id == user_id)
    user = session.exec(stmt).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user

