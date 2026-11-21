from datetime import datetime

from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Index,
                        SmallInteger, Unicode, text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PkType, TimestampMixin
from .role import Role


class Account(Base, TimestampMixin):
    __tablename__ = "account"
    __table_args__ = (
        CheckConstraint("account_status IN ('INACTIVE','ACTIVE','LOCKED')", name="ck_account_status"),
        # Email duy nhất trong các tài khoản chưa bị xóa mềm (email lưu chữ thường)
        Index("uq_account_email_active", "email", unique=True,
              mssql_where=text("deleted_at IS NULL"), sqlite_where=text("deleted_at IS NULL")),
    )

    account_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(PkType,
                                         ForeignKey("role.role_id"), nullable=False)
    full_name: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    email: Mapped[str] = mapped_column(Unicode(254), nullable=False)
    phone: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    nationality: Mapped[str | None] = mapped_column(Unicode(80))
    password_hash: Mapped[str | None] = mapped_column(Unicode(255))
    account_status: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    failed_login_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    login_locked_until: Mapped[datetime | None] = mapped_column(DateTime)
    locked_reason: Mapped[str | None] = mapped_column(Unicode(500))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime)
    privacy_consent_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    role: Mapped[Role] = relationship()
