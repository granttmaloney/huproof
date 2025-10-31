from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


class NoncePurpose(str, Enum):
    enroll = "enroll"
    login = "login"


def _uuid_str() -> str:
    return str(uuid4())


class User(SQLModel, table=True):
    id: str = Field(default_factory=_uuid_str, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class KeystrokeCommitment(SQLModel, table=True):
    id: str = Field(default_factory=_uuid_str, primary_key=True, index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    origin: str = Field(index=True)
    commitment_c: str = Field(index=True)
    tau: int = Field(default=400)
    vkey_id: Optional[str] = Field(default=None, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class NonceRecord(SQLModel, table=True):
    id: str = Field(default_factory=_uuid_str, primary_key=True)
    value: str = Field(index=True, unique=True)
    purpose: NoncePurpose = Field()
    origin_hash: str = Field(index=True)
    user_id: Optional[str] = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field()
    consumed_at: Optional[datetime] = Field(default=None, index=True)


class SessionToken(SQLModel, table=True):
    id: str = Field(default_factory=_uuid_str, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    jti: str = Field(index=True, unique=True)
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field()
    revoked_at: Optional[datetime] = Field(default=None)


