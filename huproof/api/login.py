from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from ..config.settings import get_settings
from ..core.challenge import generate_challenge, generate_nonce
from ..core.crypto import sha256_hex
from pathlib import Path

from ..core.security import create_access_token
from ..core.zk import ZKVerifyError, verify_groth16
from ..db.models import KeystrokeCommitment, NoncePurpose, NonceRecord, User
from ..db.session import get_session
from ..schemas.login import LoginFinishRequest, LoginFinishResponse, LoginStartResponse


router = APIRouter()


@router.get("/start", response_model=LoginStartResponse)
def login_start(
    *, user_id: str = Query(..., description="User ID"), session: Session = Depends(get_session)
) -> LoginStartResponse:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active commitment")

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


@router.post("/finish", response_model=LoginFinishResponse)
def login_finish(
    payload: LoginFinishRequest, *, session: Session = Depends(get_session)
) -> LoginFinishResponse:
    # Validate nonce
    nonce_value = str(payload.public_inputs.get("nonce", ""))
    if not nonce_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing nonce")

    stmt = select(NonceRecord).where(NonceRecord.value == nonce_value, NonceRecord.purpose == NoncePurpose.login)
    record = session.exec(stmt).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid nonce")
    now = datetime.utcnow()
    if record.consumed_at is not None or record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nonce expired or consumed")

    # Look up user's active commitment
    origin_hash = str(payload.public_inputs.get("origin_hash", ""))
    stmt_c = select(KeystrokeCommitment).where(
        KeystrokeCommitment.user_id == record.user_id,
        KeystrokeCommitment.origin == origin_hash,
        KeystrokeCommitment.is_active == True,  # noqa: E712
    )
    commit = session.exec(stmt_c).first()
    if commit is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active commitment for origin")

    # Optional sanity: ensure public_inputs.C matches stored commitment
    pin_c = str(payload.public_inputs.get("C", commit.commitment_c))
    if pin_c != commit.commitment_c:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Commitment mismatch")

    settings = get_settings()
    if not settings.bypass_zk_verify:
        repo_root = Path(__file__).resolve().parents[2]
        vkey_path = repo_root / "circuits" / "build" / "verification_key.json"
        try:
            ok = verify_groth16(vkey_path, payload.public_inputs, payload.proof)
        except ZKVerifyError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proof")

    # Issue access token
    if record.user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nonce not bound to user")
    token = create_access_token(record.user_id, secret=get_settings().app_secret, expires_in_seconds=3600)

    # consume nonce
    record.consumed_at = now

    return LoginFinishResponse(success=True, token=token)


