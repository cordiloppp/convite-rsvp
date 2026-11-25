from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_user: str
    postgres_password: str
    postgres_db: str

    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 480

    brand_name: str = "Convite"
    brand_url: str = "https://convite.example.com"
    public_app_url: str = "http://localhost:5173"
    app_timezone: str = "America/Tijuana"
    seed_demo: bool = False

    def url_for(self, database: str) -> URL:
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
        return self.url_for(self.postgres_db)

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.app_timezone)


@lru_cache
def get_settings() -> Settings:
    return Settings()
