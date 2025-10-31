from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "huproof"
    app_version: str = "0.1.0"

    app_secret: str = Field(..., alias="APP_SECRET")
    db_url: str = Field("sqlite:///./dev.db", alias="DB_URL")
    nonce_ttl_s: int = Field(120, alias="NONCE_TTL_S")
    tau_default: int = Field(400, alias="TAU_DEFAULT")
    origin: str = Field("http://localhost:5173", alias="ORIGIN")
    bypass_zk_verify: bool = Field(False, alias="BYPASS_ZK_VERIFY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


