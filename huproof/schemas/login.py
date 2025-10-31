from pydantic import BaseModel


class LoginStartResponse(BaseModel):
    challenge: str
    nonce: str
    origin_hash: str
    tau: int
    timestamp: int
    commitment: str


class LoginFinishRequest(BaseModel):
    proof: dict
    public_inputs: dict


class LoginFinishResponse(BaseModel):
    success: bool
    token: str | None = None


