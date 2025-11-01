from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, select

from ..config.settings import get_settings
from ..core.challenge import generate_challenge, generate_nonce
from ..core.crypto import sha256_hex
from pathlib import Path

from ..core.security import create_access_token
from ..db.models import SessionToken
from ..core.zk import ZKVerifyError, verify_groth16
from ..core.ratelimit import rate_limit_login_start, rate_limit_finish
from ..core.logging import get_logger
from ..core.origin import validate_origin
from ..core.metrics import TimingContext, record_counter
from ..db.models import KeystrokeCommitment, NoncePurpose, NonceRecord, User
from ..db.session import get_session
from ..schemas.login import LoginFinishRequest, LoginFinishResponse, LoginStartResponse


router = APIRouter()


@router.get(
    "/start",
    response_model=LoginStartResponse,
    summary="Start login",
    description="Initiate login flow. Returns challenge phrase, nonce, and user's commitment.",
)
@rate_limit_login_start()
def login_start(
    *, request: Request, user_id: str = Query(..., description="User ID"), session: Session = Depends(get_session)
) -> LoginStartResponse:
    """Start login flow by generating a challenge and retrieving user's commitment."""
    validate_origin(request)
    settings = get_settings()
    origin_hash = sha256_hex(settings.origin)

    # Find active commitment for this user and origin
    stmt = select(KeystrokeCommitment).where(
        KeystrokeCommitment.user_id == user_id,
        KeystrokeCommitment.origin == origin_hash,
        KeystrokeCommitment.is_active == True,  # noqa: E712
    )
    commit = session.exec(stmt).first()
    if commit is None:
        # Don't reveal user_id existence
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    challenge = generate_challenge()
    nonce = generate_nonce()
    tau = commit.tau
    now = datetime.now(tz=timezone.utc)
    expires_at = now + timedelta(seconds=settings.nonce_ttl_s)

    # Persist nonce bound to user and purpose
    record = NonceRecord(
        value=nonce,
        purpose=NoncePurpose.login,
        origin_hash=origin_hash,
        user_id=user_id,
        created_at=now.replace(tzinfo=None),
        expires_at=expires_at.replace(tzinfo=None),
    )
    session.add(record)

    return LoginStartResponse(
        challenge=challenge,
        nonce=nonce,
        origin_hash=origin_hash,
        tau=tau,
        timestamp=int(now.timestamp()),
        commitment=commit.commitment_c,
    )


@router.post(
    "/finish",
    response_model=LoginFinishResponse,
    summary="Complete login",
    description="Submit keystroke proof to complete login. Returns JWT access token.",
)
@rate_limit_finish()
def login_finish(
    payload: LoginFinishRequest, *, request: Request, session: Session = Depends(get_session)
) -> LoginFinishResponse:
    """Complete login by submitting ZK proof. Returns access token on success."""
    validate_origin(request)
    # Validate nonce
    nonce_value = payload.public_inputs.nonce
    stmt = select(NonceRecord).where(NonceRecord.value == nonce_value, NonceRecord.purpose == NoncePurpose.login)
    record = session.exec(stmt).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
    now = datetime.utcnow()
    if record.consumed_at is not None or record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    # Look up user's active commitment
    origin_hash = payload.public_inputs.origin_hash
    stmt_c = select(KeystrokeCommitment).where(
        KeystrokeCommitment.user_id == record.user_id,
        KeystrokeCommitment.origin == origin_hash,
        KeystrokeCommitment.is_active == True,  # noqa: E712
    )
    commit = session.exec(stmt_c).first()
    if commit is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    # Ensure public_inputs.C matches stored commitment
    pin_c = payload.public_inputs.C
    if pin_c != commit.commitment_c:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    settings = get_settings()
    if not settings.bypass_zk_verify:
        repo_root = Path(__file__).resolve().parents[2]
        vkey_path = repo_root / "circuits" / "build" / "verification_key.json"
        try:
            # Convert Pydantic models to dict for snarkjs
            public_inputs_dict = payload.public_inputs.model_dump()
            proof_dict = payload.proof.model_dump()
            with TimingContext("zk_verify_time", endpoint="login_finish"):
                ok = verify_groth16(vkey_path, public_inputs_dict, proof_dict)
        except ZKVerifyError as e:
            logger.error("zk_verify_error", error=str(e))
            record_counter("zk_verify_errors", endpoint="login_finish")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Verification service unavailable")
        if not ok:
            record_counter("zk_verify_failures", endpoint="login_finish")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
        record_counter("zk_verify_successes", endpoint="login_finish")

    # Issue access token
    if record.user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
    
    settings = get_settings()
    expires_in_seconds = 3600
    token, jti = create_access_token(
        record.user_id,
        secret=settings.app_secret,
        expires_in_seconds=expires_in_seconds,
    )
    
    # Store session token record
    expires_at = now + timedelta(seconds=expires_in_seconds)
    session_token = SessionToken(
        user_id=record.user_id,
        jti=jti,
        issued_at=now,
        expires_at=expires_at.replace(tzinfo=None),
        revoked_at=None,
    )
    session.add(session_token)

    # consume nonce
    record.consumed_at = now
    
    record_counter("logins_total", success=1)

    return LoginFinishResponse(success=True, token=token)


