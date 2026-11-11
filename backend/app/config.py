import os

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev-secret-change-me-in-production-0123456789"
ON_VERCEL = bool(os.environ.get("VERCEL"))


def _default_database_url() -> str:
    # Vercel functions can only write to /tmp, and that storage is temporary:
    # fine for a demo, but set DATABASE_URL to a Postgres database to keep data.
    return "sqlite:////tmp/finance.db" if ON_VERCEL else "sqlite:///./finance.db"


class Settings(BaseSettings):
    """Application settings, overridable through environment variables or a .env file."""

    database_url: str = Field(default_factory=_default_database_url)
    secret_key: str = DEV_SECRET_KEY
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_for_postgres(cls, url: str) -> str:
        """Hosted Postgres gives postgres:// URLs; SQLAlchemy needs the driver named."""
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url

    @model_validator(mode="after")
    def _require_real_secret_when_deployed(self) -> "Settings":
        if ON_VERCEL and self.secret_key == DEV_SECRET_KEY:
            raise ValueError("Set the SECRET_KEY environment variable before deploying.")
        return self


settings = Settings()
