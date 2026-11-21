from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# BIGINT identity trên SQL Server; SQLite (dùng khi test) chỉ autoincrement với INTEGER.
PkType = BigInteger().with_variant(Integer, "sqlite")


def utcnow() -> datetime:
    """Timestamp lưu theo UTC (Data Model mục VI.5); hiển thị/nghiệp vụ đổi sang UTC+7."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
