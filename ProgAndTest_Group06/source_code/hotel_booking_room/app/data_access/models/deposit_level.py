from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Numeric, Computed, true
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, PkType


class DepositLevel(Base):
    """1.21 DEPOSIT_LEVEL – mức đặt cọc do Admin cấu hình (mặc định 20/50/100)."""
    __tablename__ = "deposit_level"
    __table_args__ = (
        CheckConstraint("percentage >= 1 AND percentage <= 100", name="ck_deposit_pct"),
    )

    deposit_level_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime)
    updated_by: Mapped[int] = mapped_column(PkType, ForeignKey("account.account_id"), nullable=False)
    active_percentage_key: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), Computed("CASE WHEN is_active = 1 THEN percentage ELSE NULL END", persisted=True)
    )

# RBLB12: mỗi percentage chỉ có tối đa một mức active.
Index("uq_deposit_active_pct", DepositLevel.active_percentage_key, unique=True)
