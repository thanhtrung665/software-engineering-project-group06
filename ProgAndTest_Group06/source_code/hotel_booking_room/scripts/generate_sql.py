"""Sinh sql/01_create_schema.sql (MySQL) từ các model SQLAlchemy.

Chạy: python -m scripts.generate_sql
"""
from pathlib import Path

from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.data_access.models import Base

OUT = Path(__file__).resolve().parent.parent / "sql" / "01_core_models_schema.sql"
DB = "hotel_booking_system"


def main() -> None:
    d = mysql.dialect()
    parts = [
        "-- Sinh tự động bởi `python -m scripts.generate_sql` – sửa model rồi sinh lại.",
        "CREATE DATABASE IF NOT EXISTS `hotel_booking_system` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "USE `hotel_booking_system`;",
    ]
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=d)).strip().replace(")ENGINE=", ") ENGINE=")
        idx = [str(CreateIndex(i).compile(dialect=d)).strip()
               for i in sorted(table.indexes, key=lambda x: x.name)]
        parts.append(";\n".join([ddl] + idx) + ";")
    OUT.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"Đã ghi {OUT} ({len(Base.metadata.sorted_tables)} bảng)")


if __name__ == "__main__":
    main()
