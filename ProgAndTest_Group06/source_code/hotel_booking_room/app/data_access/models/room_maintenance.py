from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, PkType, utcnow


class RoomMaintenance(Base):
    """1.17 ROOM_MAINTENANCE – giai đoạn phòng không bán được (end_date inclusive)."""
    __tablename__ = "room_maintenance"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_maint_dates"),
        CheckConstraint("maintenance_status IN ('PLANNED','IN_PROGRESS','COMPLETED','CANCELLED')",
                        name="ck_maint_status"),
        Index("ix_maint_room_dates", "room_id", "start_date", "end_date"),
    )

    maintenance_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(PkType, ForeignKey("room.room_id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Unicode(500), nullable=False)
    maintenance_status: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    created_by: Mapped[int] = mapped_column(PkType, ForeignKey("account.account_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
