from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..config.settings import get_settings
from ..core.challenge import generate_challenge, generate_nonce
from ..core.crypto import sha256_hex
from pathlib import Path

from ..core.zk import ZKVerifyError, verify_groth16
from ..db.models import KeystrokeCommitment, NoncePurpose, NonceRecord, User
from ..db.session import get_session
from ..schemas.enroll import EnrollFinishRequest, EnrollFinishResponse, EnrollStartResponse


router = APIRouter()


@router.get("/start", response_model=EnrollStartResponse)
def enroll_start(*, session: Session = Depends(get_session)) -> EnrollStartResponse:
    settings = get_settings()
    challenge = generate_challenge()
    nonce = generate_nonce()
    origin_hash = sha256_hex(settings.origin)
    tau = settings.tau_default
    now = datetime.now(tz=timezone.utc)
    expires_at = now + timedelta(seconds=settings.nonce_ttl_s)

    # Persist nonce
    record = NonceRecord(
        value=nonce,
        purpose=NoncePurpose.enroll,
        origin_hash=origin_hash,
        user_id=None,
        created_at=now.replace(tzinfo=None),
        expires_at=expires_at.replace(tzinfo=None),
    )
    session.add(record)

    return EnrollStartResponse(
        challenge=challenge,
        nonce=nonce,
        origin_hash=origin_hash,
        tau=tau,
        timestamp=int(now.timestamp()),
    )


@router.post("/finish", response_model=EnrollFinishResponse)
def enroll_finish(
    payload: EnrollFinishRequest, *, session: Session = Depends(get_session)
) -> EnrollFinishResponse:
    # Minimal validation: check nonce is valid and not expired/consumed
    nonce_value = str(payload.public_inputs.get("nonce", ""))
    if not nonce_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing nonce")

    statement = select(NonceRecord).where(NonceRecord.value == nonce_value, NonceRecord.purpose == NoncePurpose.enroll)
    record = session.exec(statement).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid nonce")
    now = datetime.utcnow()
    if record.consumed_at is not None or record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nonce expired or consumed")

    if not payload.commitment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing commitment")

    settings = get_settings()
    if not settings.bypass_zk_verify:
        # Verify proof against local vkey (PoC path)
        repo_root = Path(__file__).resolve().parents[2]
        vkey_path = repo_root / "circuits" / "build" / "verification_key.json"
        try:
            ok = verify_groth16(vkey_path, payload.public_inputs, payload.proof)
        except ZKVerifyError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proof")

    # Create user and store commitment
    user = User()
    session.add(user)
    session.flush()  # assign id

    tau_input = int(payload.public_inputs.get("tau", 0)) or 400
    origin_hash = str(payload.public_inputs.get("origin_hash", ""))
    commit = KeystrokeCommitment(
        user_id=user.id,
        origin=origin_hash,
        commitment_c=str(payload.commitment),
        tau=tau_input,
        vkey_id=None,
        is_active=True,
    )
    session.add(commit)

    # consume nonce
    record.consumed_at = now

    return EnrollFinishResponse(success=True, user_id=user.id)


