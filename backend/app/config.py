from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    # Option 1: a full connection string (Neon / Vercel set DATABASE_URL).
    database_url_env: str | None = Field(default=None, alias="DATABASE_URL")

    # Option 2: separate parts (docker compose).
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_db: str | None = None

    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 480

    brand_name: str = "Convite"
    brand_url: str = "https://convite.example.com"
    public_app_url: str = "http://localhost:5173"
    app_timezone: str = "America/Tijuana"
    seed_demo: bool = False

    # Public demo: anyone can log in with the demo account and look around,
    # but only a session opened with OWNER_PASSWORD can change data.
    demo_readonly: bool = False
    owner_password: str | None = Field(default=None, min_length=12)

    @model_validator(mode="after")
    def _require_database(self) -> "Settings":
        if not self.database_url_env and not (
            self.postgres_user and self.postgres_password and self.postgres_db
        ):
            raise ValueError(
                "Define DATABASE_URL o POSTGRES_USER, POSTGRES_PASSWORD y POSTGRES_DB"
            )
        return self

    def url_for(self, database: str) -> URL:
        if self.database_url_env:
            url = make_url(self.database_url_env)
            # Use the psycopg 3 driver whatever scheme the provider gives.
            return url.set(drivername="postgresql+psycopg", database=database)
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=database,
        )

    @property
    def database_url(self) -> URL:
        if self.database_url_env:
            return self.url_for(make_url(self.database_url_env).database or "")
        return self.url_for(self.postgres_db or "")

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.app_timezone)


@lru_cache
def get_settings() -> Settings:
    return Settings()
