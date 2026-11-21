"""Cấu hình ứng dụng, đọc từ biến môi trường / file .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Hotel Booking System"
    app_env: str = "dev"
    api_prefix: str = "/api/v1"

    # Job nền giải phóng phòng giữ quá hạn (UC Book room A4 / RBLQH23)
    hold_expiry_scheduler_enabled: bool = True
    hold_expiry_interval_seconds: int = 30

    db_server: str = "localhost"
    db_port: int = 3306
    db_name: str = "hotel_booking_system"
    db_user: str = "hotel_user"
    db_password: str = ""
    mysql_root_password: str = ""

    def _url(self, database: str) -> URL:
        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_server,
            port=self.db_port,
            database=database,
            query={"charset": "utf8mb4"},
        )

    @property
    def database_url(self) -> URL:
        return self._url(self.db_name)


@lru_cache
def get_settings() -> Settings:
    return Settings()
