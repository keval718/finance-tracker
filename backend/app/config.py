from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, overridable through environment variables or a .env file."""

    database_url: str = "sqlite:///./finance.db"
    secret_key: str = "dev-secret-change-me-in-production-0123456789"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
