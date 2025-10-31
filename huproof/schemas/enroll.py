from pydantic import BaseModel


class EnrollStartResponse(BaseModel):
    challenge: str
    nonce: str
    origin_hash: str
    tau: int
    timestamp: int


class EnrollFinishRequest(BaseModel):
    commitment: str
    proof: dict
    public_inputs: dict


class EnrollFinishResponse(BaseModel):
    success: bool
    user_id: str


