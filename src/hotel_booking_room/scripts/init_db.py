"""Tạo database hotel_booking_system (nếu chưa có) rồi tạo toàn bộ bảng.

Chạy:  python -m scripts.init_db
"""
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.data_access.database import get_engine
from app.data_access.models import Base


def main() -> None:
    s = get_settings()
    master = create_engine(s.master_database_url, isolation_level="AUTOCOMMIT")
    with master.connect() as conn:
        # Collation tiếng Việt, tương ứng yêu cầu lưu tiếng Việt đúng (utf8mb4 trong tài liệu)
        conn.execute(text(
            f"IF DB_ID(N'{s.db_name}') IS NULL "
            f"CREATE DATABASE [{s.db_name}] COLLATE Vietnamese_100_CI_AS"))
    Base.metadata.create_all(get_engine())
    print(f"OK: database '{s.db_name}' và {len(Base.metadata.tables)} bảng đã sẵn sàng.")


if __name__ == "__main__":
    main()
