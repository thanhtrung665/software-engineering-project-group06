from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, PkType, utcnow


class SystemSetting(Base):
    """1.40 SYSTEM_SETTING – tham số nghiệp vụ Admin chỉnh được (RBLQH17: không hard-code)."""
    __tablename__ = "system_setting"

    setting_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    setting_key: Mapped[str] = mapped_column(Unicode(80), unique=True, nullable=False)
    setting_value: Mapped[Any] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Unicode(255))
    updated_by: Mapped[int] = mapped_column(PkType, ForeignKey("account.account_id"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
