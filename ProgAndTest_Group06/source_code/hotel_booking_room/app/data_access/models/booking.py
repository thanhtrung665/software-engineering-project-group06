"""1.25–1.30: BOOKING, BOOKING_ITEM, BOOKING_NIGHT_RATE, BOOKING_ROOM_ASSIGNMENT,
BOOKING_GUEST, BOOKING_STATUS_HISTORY."""
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, LargeBinary,
                        Numeric, SmallInteger, Text, Time, Unicode, UniqueConstraint, false)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PkType, TimestampMixin, utcnow
from .room_type import RoomType

_BOOKING_STATUSES = ("PENDING_PAYMENT','CONFIRMED','CHECKED_IN','CHECKED_OUT',"
                     "'CANCELLED','PAYMENT_EXPIRED','NO_SHOW")
_PAYMENT_STATUSES = ("UNPAID','DEPOSIT_PAID','FULLY_PAID','PAYMENT_FAILED',"
                     "'REFUND_FAILED','PARTIALLY_REFUNDED','REFUNDED")


class Booking(Base, TimestampMixin):
    __tablename__ = "booking"
    __table_args__ = (
        CheckConstraint(f"booking_status IN ('{_BOOKING_STATUSES}')", name="ck_booking_status"),
        CheckConstraint(f"payment_status IN ('{_PAYMENT_STATUSES}')", name="ck_booking_payment_status"),
        CheckConstraint("booking_source IN ('ONLINE','FRONT_DESK')", name="ck_booking_source"),
        CheckConstraint("check_out_date > check_in_date", name="ck_booking_dates"),            # RBMGT09
        CheckConstraint("room_count >= 1 AND room_count <= 5 AND adults >= room_count AND children >= 0",
                        name="ck_booking_counts"),                                              # RBMGT09
        CheckConstraint("subtotal_amount >= 0 AND discount_amount >= 0 AND total_amount >= 0 "
                        "AND deposit_amount >= 0 AND paid_amount >= 0 AND remaining_amount >= 0",
                        name="ck_booking_amounts"),                                             # RBMGT10
        CheckConstraint("deposit_percentage > 0 AND deposit_percentage <= 100", name="ck_booking_deposit_pct"),
        # Index cho job quét hold hết hạn (VI.5 – Indexing)
        Index("ix_booking_status_hold", "booking_status", "hold_expires_at"),
        Index("ix_booking_status_dates", "booking_status", "check_in_date", "check_out_date"),
        Index("ix_booking_account_status", "account_id", "booking_status"),
    )

    booking_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    booking_code: Mapped[str] = mapped_column(Unicode(30), unique=True, nullable=False)
    account_id: Mapped[int | None] = mapped_column(PkType, ForeignKey("account.account_id"))
    created_by: Mapped[int | None] = mapped_column(PkType, ForeignKey("account.account_id"))
    booking_source: Mapped[str] = mapped_column(Unicode(15), nullable=False)
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    adults: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    children: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    room_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    guest_contact_name: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    guest_contact_phone: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    guest_contact_email: Mapped[str | None] = mapped_column(Unicode(254))
    special_requests: Mapped[str | None] = mapped_column(Text)
    estimated_arrival_time: Mapped[time | None] = mapped_column(Time)
    booking_status: Mapped[str] = mapped_column(Unicode(25), nullable=False)
    payment_status: Mapped[str] = mapped_column(Unicode(25), nullable=False)
    currency: Mapped[str] = mapped_column(Unicode(3), default="VND", nullable=False)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    deposit_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    hold_expires_at: Mapped[datetime | None] = mapped_column(DateTime)   # UTC; giữ phòng 15 phút
    policy_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    terms_accepted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancellation_reason: Mapped[str | None] = mapped_column(Unicode(500))

    items: Mapped[list["BookingItem"]] = relationship(
        back_populates="booking", order_by="BookingItem.room_type_id", cascade="all, delete-orphan")
    guests: Mapped[list["BookingGuest"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    status_history: Mapped[list["BookingStatusHistory"]] = relationship(
        back_populates="booking", order_by="BookingStatusHistory.booking_status_history_id")


class BookingItem(Base):
    __tablename__ = "booking_item"
    __table_args__ = (
        UniqueConstraint("booking_id", "room_type_id", name="uq_booking_item_type"),   # RBLB04
        CheckConstraint("quantity >= 1 AND adults >= quantity AND children >= 0", name="ck_item_counts"),
        Index("ix_item_roomtype_booking", "room_type_id", "booking_id"),
    )

    booking_item_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(PkType, ForeignKey("booking.booking_id"), nullable=False)
    room_type_id: Mapped[int] = mapped_column(PkType, ForeignKey("room_type.room_type_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    adults: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    children: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    line_subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    line_discount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="items")
    room_type: Mapped[RoomType] = relationship()
    night_rates: Mapped[list["BookingNightRate"]] = relationship(
        back_populates="item", order_by="BookingNightRate.stay_date", cascade="all, delete-orphan")


class BookingNightRate(Base):
    """Snapshot giá từng đêm (RBLQH05/06) – không bao giờ sửa khi ROOM_RATE đổi."""
    __tablename__ = "booking_night_rate"
    __table_args__ = (
        UniqueConstraint("booking_item_id", "stay_date", name="uq_night_rate"),         # RBLB04
        CheckConstraint("rate_type_applied IN ('BASE','WEEKEND','SEASON','HOLIDAY')", name="ck_night_rate_type"),
    )

    booking_night_rate_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    booking_item_id: Mapped[int] = mapped_column(PkType, ForeignKey("booking_item.booking_item_id"),
                                                 nullable=False)
    stay_date: Mapped[date] = mapped_column(Date, nullable=False)
    rate_type_applied: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    source_room_rate_id: Mapped[int | None] = mapped_column(PkType, ForeignKey("room_rate.room_rate_id"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    night_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    night_discount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)

    item: Mapped[BookingItem] = relationship(back_populates="night_rates")


class BookingRoomAssignment(Base):
    """1.29 – gán phòng vật lý lúc check-in (thuộc use case Check-in; khai báo để FK hợp lệ)."""
    __tablename__ = "booking_room_assignment"
    __table_args__ = (
        UniqueConstraint("booking_item_id", "room_id", name="uq_assignment_item_room"),  # RBLB10
    )

    assignment_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    booking_item_id: Mapped[int] = mapped_column(PkType, ForeignKey("booking_item.booking_item_id"),
                                                 nullable=False)
    room_id: Mapped[int] = mapped_column(PkType, ForeignKey("room.room_id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime)
    assigned_by: Mapped[int] = mapped_column(PkType, ForeignKey("account.account_id"), nullable=False)
    is_upgrade: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)
    upgrade_reason: Mapped[str | None] = mapped_column(Unicode(500))


class BookingGuest(Base):
    __tablename__ = "booking_guest"

    booking_guest_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(PkType, ForeignKey("booking.booking_id"), nullable=False)
    assignment_id: Mapped[int | None] = mapped_column(
        PkType, ForeignKey("booking_room_assignment.assignment_id"))
    full_name: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(Unicode(20))
    nationality: Mapped[str | None] = mapped_column(Unicode(80))
    document_type: Mapped[str | None] = mapped_column(Unicode(20))
    document_number_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary(512))
    document_key_version: Mapped[str | None] = mapped_column(Unicode(30))
    is_primary_guest: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(),
                                                   nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="guests")


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"
    __table_args__ = (
        CheckConstraint("changed_source IN ('USER','ADMIN','SYSTEM_SCHEDULER','PAYMENT_GATEWAY')",
                        name="ck_history_source"),                                              # RBMGT17
        CheckConstraint("(changed_source IN ('USER','ADMIN') AND changed_by IS NOT NULL) OR "
                        "(changed_source IN ('SYSTEM_SCHEDULER','PAYMENT_GATEWAY') AND changed_by IS NULL)",
                        name="ck_history_actor"),                                               # RBLTT15
    )

    booking_status_history_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(PkType, ForeignKey("booking.booking_id"),
                                            nullable=False, index=True)
    old_status: Mapped[str | None] = mapped_column(Unicode(25))
    new_status: Mapped[str] = mapped_column(Unicode(25), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(PkType, ForeignKey("account.account_id"))
    changed_source: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    change_reason: Mapped[str | None] = mapped_column(Unicode(500))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="status_history")
