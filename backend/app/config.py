from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CIDADE_PADRAO: str = "Concórdia"
    ESTADO_PADRAO: str = "SC"
    CORS_ORIGINS: list[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        normalized = value.casefold()
        if (
            len(value) < 32
            or "substitua" in normalized
            or "sua_chave" in normalized
            or "change-me" in normalized
        ):
            raise ValueError("SECRET_KEY must be a non-default secret of at least 32 characters")
        return value


settings = Settings()
