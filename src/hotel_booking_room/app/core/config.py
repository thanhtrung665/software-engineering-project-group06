"""Cấu hình ứng dụng, đọc từ biến môi trường / file .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Hotel Booking System"
    app_env: str = "dev"
    api_prefix: str = "/api/v1"

    db_server: str = "localhost"
    db_port: int = 1433
    db_name: str = "hotel_booking_system"
    db_user: str = "sa"
    db_password: str = ""
    db_driver: str = "ODBC Driver 18 for SQL Server"

    def _url(self, database: str) -> URL:
        return URL.create(
            "mssql+pyodbc",
            username=self.db_user,
            password=self.db_password,  # SQLAlchemy tự escape ký tự đặc biệt
            host=self.db_server,
            port=self.db_port,
            database=database,
            query={"driver": self.db_driver, "TrustServerCertificate": "yes"},
        )

    @property
    def database_url(self) -> URL:
        return self._url(self.db_name)

    @property
    def master_database_url(self) -> URL:
        """Dùng để tạo database lần đầu (chưa tồn tại)."""
        return self._url("master")


@lru_cache
def get_settings() -> Settings:
    return Settings()
