from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..config.settings import get_settings
from ..core.challenge import generate_challenge, generate_nonce
from ..core.crypto import sha256_hex
from pathlib import Path

from ..core.zk import ZKVerifyError, verify_groth16
from ..core.ratelimit import rate_limit_enroll_start, rate_limit_finish
from ..core.logging import get_logger
from ..core.origin import validate_origin
from ..core.metrics import TimingContext, record_counter
from ..db.models import KeystrokeCommitment, NoncePurpose, NonceRecord, User
from ..db.session import get_session
from ..schemas.enroll import EnrollFinishRequest, EnrollFinishResponse, EnrollStartResponse

logger = get_logger()


router = APIRouter()


@router.get(
    "/start",
    response_model=EnrollStartResponse,
    summary="Start enrollment",
    description="Initiate user enrollment. Returns a challenge phrase and nonce for keystroke capture.",
)
@rate_limit_enroll_start()
def enroll_start(*, request: Request, session: Session = Depends(get_session)) -> EnrollStartResponse:
    """Start enrollment flow by generating a challenge and nonce."""
    validate_origin(request)
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


@router.post(
    "/finish",
    response_model=EnrollFinishResponse,
    summary="Complete enrollment",
    description="Submit keystroke proof and commitment to complete enrollment. Returns user_id.",
)
@rate_limit_finish()
def enroll_finish(
    payload: EnrollFinishRequest, *, request: Request, session: Session = Depends(get_session)
) -> EnrollFinishResponse:
    """Complete enrollment by submitting ZK proof and commitment."""
    validate_origin(request)
    # Validate nonce is valid and not expired/consumed
    nonce_value = payload.public_inputs.nonce
    statement = select(NonceRecord).where(NonceRecord.value == nonce_value, NonceRecord.purpose == NoncePurpose.enroll)
    record = session.exec(statement).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
    now = datetime.utcnow()
    if record.consumed_at is not None or record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    settings = get_settings()
    if not settings.bypass_zk_verify:
        # Verify proof against local vkey (PoC path)
        repo_root = Path(__file__).resolve().parents[2]
        vkey_path = repo_root / "circuits" / "build" / "verification_key.json"
        try:
            # Convert Pydantic models to dict for snarkjs
            public_inputs_dict = payload.public_inputs.model_dump()
            proof_dict = payload.proof.model_dump()
            with TimingContext("zk_verify_time", endpoint="enroll_finish"):
                ok = verify_groth16(vkey_path, public_inputs_dict, proof_dict)
        except ZKVerifyError as e:
            logger.error("zk_verify_error", error=str(e))
            record_counter("zk_verify_errors", endpoint="enroll_finish")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Verification service unavailable")
        if not ok:
            record_counter("zk_verify_failures", endpoint="enroll_finish")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
        record_counter("zk_verify_successes", endpoint="enroll_finish")

    # Create user and store commitment
    user = User()
    session.add(user)
    session.flush()  # assign id

    tau_input = payload.public_inputs.tau or 400
    origin_hash = payload.public_inputs.origin_hash
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
    
    record_counter("enrollments_total", success=1)

    return EnrollFinishResponse(success=True, user_id=user.id)


