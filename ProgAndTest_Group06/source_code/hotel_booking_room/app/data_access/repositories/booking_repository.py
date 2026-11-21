from datetime import datetime

from sqlalchemy import func, select

from app.core.enums import BookingStatus
from app.data_access.locking import for_update
from app.data_access.models import (Booking, BookingGuest, BookingItem, BookingNightRate,
                                    BookingStatusHistory)
from .base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    """Business tạo bản ghi qua các factory method (không phải import ORM model)."""
    model = Booking

    # ---- factory ----
    def create(self, **fields) -> Booking:
        booking = Booking(**fields)
        self.session.add(booking)
        return booking

    def add_item(self, booking: Booking, **fields) -> BookingItem:
        item = BookingItem(**fields)
        booking.items.append(item)
        return item

    def add_night_rate(self, item: BookingItem, **fields) -> BookingNightRate:
        rate = BookingNightRate(**fields)
        item.night_rates.append(rate)
        return rate

    def add_guest(self, booking: Booking, **fields) -> BookingGuest:
        guest = BookingGuest(**fields)
        booking.guests.append(guest)
        return guest

    def add_status_history(self, booking: Booking, **fields) -> BookingStatusHistory:
        row = BookingStatusHistory(booking_id=booking.booking_id, **fields)
        self.session.add(row)
        return row

    def flush(self) -> None:
        self.session.flush()

    # ---- query ----
    def get_by_code(self, code: str) -> Booking | None:
        return self.session.scalar(select(Booking).where(Booking.booking_code == code))

    def get_for_update(self, booking_id: int) -> Booking | None:
        """Khóa hàng booking (job hết hạn, luồng thanh toán, hủy: cùng một cách khóa – RBLQH20)."""
        return self.session.scalar(for_update(select(Booking).where(Booking.booking_id == booking_id), Booking))

    def code_exists(self, code: str) -> bool:
        return self.session.scalar(select(func.count()).select_from(Booking)
                                   .where(Booking.booking_code == code)) > 0

    def count_valid_pending(self, account_id: int, now: datetime) -> int:
        """Số booking Pending Payment còn hold hợp lệ của tài khoản (UC Book room A5)."""
        return self.session.scalar(
            select(func.count()).select_from(Booking)
            .where(Booking.account_id == account_id,
                   Booking.booking_status == BookingStatus.PENDING_PAYMENT,
                   Booking.hold_expires_at > now))

    def find_expired_hold_ids(self, now: datetime, limit: int) -> list[int]:
        stmt = (select(Booking.booking_id)
                .where(Booking.booking_status == BookingStatus.PENDING_PAYMENT,
                       Booking.hold_expires_at <= now)
                .order_by(Booking.hold_expires_at).limit(limit))
        return list(self.session.scalars(stmt))
