from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# backend/.env — resolved from this file so it works no matter where you run commands from.
# Real environment variables (e.g. set by the hosting platform) always win over this file.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

# Not configurable on purpose: letting an env variable pick the algorithm opens known JWT attacks.
JWT_ALGORITHM = "HS256"


class Settings(BaseSettings):
    # hide_input_in_errors: a rejected JWT_SECRET / DATABASE_URL must not be printed into the logs.
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore", hide_input_in_errors=True
    )

    # Required: no default, so the app refuses to start without them.
    DATABASE_URL: str
    # HS256 keys should be at least 256 bits; 32+ characters of random text covers that.
    JWT_SECRET: str = Field(min_length=32)
    JWT_EXPIRE_MINUTES: int = Field(default=60, gt=0)
    # NoDecode: read the raw string ("a,b") instead of expecting a JSON list; split it below.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, value):
        if isinstance(value, str):
            # "http://a.com, http://b.com/" → ["http://a.com", "http://b.com"] (browsers send no trailing /)
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
