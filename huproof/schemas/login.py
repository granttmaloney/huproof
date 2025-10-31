from pydantic import BaseModel, Field, field_validator

from .enroll import PublicInputs, ProofSchema


class LoginStartResponse(BaseModel):
    challenge: str
    nonce: str
    origin_hash: str
    tau: int
    timestamp: int
    commitment: str


class LoginFinishRequest(BaseModel):
    proof: ProofSchema
    public_inputs: PublicInputs


class LoginFinishResponse(BaseModel):
    success: bool
    token: str | None = None


