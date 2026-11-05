from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase
    SUPABASE_PUBLISHABLE_KEY: str
    SUPABASE_URL: str
    # Not used by the app today. Kept optional so it is not a required secret.
    SUPABASE_SECRET_KEY: str | None = None

    # Allowed origins (JSON list, e.g. '["http://localhost:5173"]').
    # Credentials are enabled, so "*" is rejected.
    ALLOWED_ORIGINS: list[str]

    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""

    # Database pool
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Security
    COOKIE_SECURE: bool = False
    # Turn off in production if the API docs must not be public.
    ENABLE_DOCS: bool = True
    # In-process limiter for the unauthenticated auth endpoints. It is per
    # worker process, so also limit at the edge when running several workers.
    RATE_LIMIT_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def _origins_must_be_explicit(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            if origin.strip() == "*" or not origin.startswith(("http://", "https://")):
                raise ValueError(
                    "ALLOWED_ORIGINS must list explicit http(s) origins; '*' is not allowed with credentials"
                )
        return origins


settings = Settings()  # type: ignore[call-arg]
