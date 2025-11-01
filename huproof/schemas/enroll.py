from pydantic import BaseModel, Field, field_validator, model_validator


class EnrollStartResponse(BaseModel):
    challenge: str
    nonce: str
    origin_hash: str
    tau: int
    timestamp: int


class PublicInputs(BaseModel):
    """Validated public inputs for ZK proof."""

    nonce: str = Field(..., min_length=1, max_length=200)
    origin_hash: str = Field(..., min_length=64, max_length=64)  # SHA256 hex = 64 chars
    tau: int = Field(..., ge=0, le=100000)  # Reasonable bounds
    timestamp: int = Field(..., ge=0)
    C: str = Field(..., min_length=1, max_length=200)  # Commitment as decimal string
    sig: str = Field(..., min_length=1, max_length=200)  # Signature as decimal string

    @field_validator("origin_hash")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        """Validate origin_hash is hex."""
        if not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("origin_hash must be hexadecimal")
        return v.lower()

    @field_validator("C", "sig")
    @classmethod
    def validate_decimal_string(cls, v: str) -> str:
        """Validate decimal string format."""
        if not v.strip():
            raise ValueError("Field cannot be empty")
        # Should be decimal digits (for BigInt strings)
        if not v.strip("-").replace(".", "").isdigit():
            raise ValueError("Field must be a valid decimal number string")
        return v


class ProofSchema(BaseModel):
    """Validated proof structure."""

    pi_a: list = Field(default_factory=list)
    pi_b: list = Field(default_factory=list)
    pi_c: list = Field(default_factory=list)


class EnrollFinishRequest(BaseModel):
    commitment: str = Field(..., min_length=1, max_length=200)
    proof: ProofSchema
    public_inputs: PublicInputs

    @field_validator("commitment")
    @classmethod
    def validate_commitment(cls, v: str) -> str:
        """Validate commitment format."""
        if not v.strip():
            raise ValueError("Commitment cannot be empty")
        if not v.strip("-").replace(".", "").isdigit():
            raise ValueError("Commitment must be a valid decimal number string")
        return v


class EnrollFinishResponse(BaseModel):
    success: bool
    user_id: str


