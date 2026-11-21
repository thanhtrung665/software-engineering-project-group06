from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (Boolean, CheckConstraint, Date, DateTime, ForeignKey, Numeric,
                        SmallInteger, Unicode, true)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, PkType, utcnow


class RoomRate(Base):
    """1.18 ROOM_RATE – giá theo loại phòng (đã gồm VAT/phí, VND)."""
    __tablename__ = "room_rate"
    __table_args__ = (
        CheckConstraint("rate_type IN ('BASE','WEEKEND','SEASON','HOLIDAY')", name="ck_rate_type"),
        CheckConstraint("nightly_price >= 0", name="ck_rate_price"),
    )

    room_rate_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    room_type_id: Mapped[int] = mapped_column(PkType, ForeignKey("room_type.room_type_id"),
                                              nullable=False, index=True)
    rate_type: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)       # SEASON
    end_date: Mapped[date | None] = mapped_column(Date)         # SEASON (inclusive)
    weekday_no: Mapped[int | None] = mapped_column(SmallInteger)  # WEEKEND: ISO 5=Fri, 6=Sat
    nightly_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)
    created_by: Mapped[int] = mapped_column(PkType, ForeignKey("account.account_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class HolidayDate(Base):
    """1.19 HOLIDAY_DATE"""
    __tablename__ = "holiday_date"

    holiday_date_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    holiday_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    holiday_name: Mapped[str] = mapped_column(Unicode(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)


class RoomRateHoliday(Base):
    """1.20 ROOM_RATE_HOLIDAY – gắn giá HOLIDAY với từng ngày lễ."""
    __tablename__ = "room_rate_holiday"

    room_rate_id: Mapped[int] = mapped_column(PkType, ForeignKey("room_rate.room_rate_id"),
                                              primary_key=True, autoincrement=False)
    holiday_date_id: Mapped[int] = mapped_column(PkType, ForeignKey("holiday_date.holiday_date_id"),
                                                 primary_key=True, autoincrement=False)
