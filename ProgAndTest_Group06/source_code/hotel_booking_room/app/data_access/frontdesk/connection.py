"""Kết nối MySQL (mysql-connector) cho nghiệp vụ lễ tân – dùng chung cấu hình `.env` với backend chính."""
from app.core.config import get_settings


def get_connection():
    """Mỗi thao tác lễ tân dùng 1 kết nối + 1 transaction (autocommit tắt)."""
    import mysql.connector  # import trễ để unit test không cần driver

    s = get_settings()
    return mysql.connector.connect(
        host=s.db_server,
        port=s.db_port,
        user=s.db_user,
        password=s.db_password,
        database=s.db_name,
        charset="utf8mb4",
        use_unicode=True,
        autocommit=False,
    )
