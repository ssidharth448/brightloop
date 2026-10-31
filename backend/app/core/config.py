"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://brightloop_user:your_password@localhost:5433/brightloop_db"

    # JWT settings
    SECRET_KEY: str = "changeme-generate-a-real-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Tax rate (percentage, e.g. 18 = 18%)
    DEFAULT_TAX_RATE: float = 18.0

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
    )


settings = Settings()
