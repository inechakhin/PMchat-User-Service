from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Config(BaseSettings):
    
    # Пути и директории
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    LOGS_DIR: Path = BASE_DIR / "logs"

    # Postgres
    POSTGRES_HOST: str = Field("localhost", validation_alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, validation_alias="POSTGRES_PORT")
    POSTGRES_USER: str | None = Field(None, validation_alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str | None = Field(None, validation_alias="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("pmchat_user_postgres", validation_alias="POSTGRES_DB")
    
    # JWT
    SECRET_KEY: str | None = Field(None, validation_alias="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Config()

