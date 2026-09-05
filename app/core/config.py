from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    PROJECT_NAME: str = "s247 Core API"
    API_PREFIX: str = "/v1"
    DEBUG: bool = False

    # Database configuration
    DATABASE_URL: str = "postgresql+asyncpg://db_admin:SuperBezpieczneHasloPostgres123!@s247_postgres:5432/s247_database"

    # JWT Security settings (human users)
    SECRET_KEY: str = "s247_development_secret_key_needs_override_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # RabbitMQ settings
    RABBITMQ_URL: str = "amqp://core_app:password123@s247_rabbitmq:5672/hub"
    RABBITMQ_JWT_KEY_PATH: str | None = "/etc/rabbitmq/jwt_private_key.pem"
    RABBITMQ_TOKEN_EXPIRE_MINUTES: int = 15

    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]


settings = Settings()
