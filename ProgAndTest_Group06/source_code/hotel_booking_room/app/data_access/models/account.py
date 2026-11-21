from datetime import datetime

from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Index,
                        SmallInteger, Unicode, Computed)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PkType, TimestampMixin
from .role import Role


class Account(Base, TimestampMixin):
    __tablename__ = "account"
    __table_args__ = (
        CheckConstraint("account_status IN ('INACTIVE','ACTIVE','LOCKED')", name="ck_account_status"),
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
    active_email_key: Mapped[str | None] = mapped_column(
        Unicode(254), Computed("CASE WHEN deleted_at IS NULL THEN email ELSE NULL END", persisted=True)
    )

    role: Mapped[Role] = relationship()

# Unique key chỉ có giá trị với tài khoản chưa xóa mềm.
Index("uq_account_email_active", Account.active_email_key, unique=True)
