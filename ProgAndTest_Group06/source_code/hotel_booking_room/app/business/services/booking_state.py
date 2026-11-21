"""Máy trạng thái booking (RBLQH10) + ghi BOOKING_STATUS_HISTORY (mọi thay đổi đều có lịch sử)."""
from datetime import datetime
from decimal import Decimal

from app.business.exceptions import InvalidStateTransition
from app.core.enums import BookingStatus as S, ChangedSource
from app.data_access.unit_of_work import UnitOfWork

_ALLOWED: dict[str, set[str]] = {
    S.PENDING_PAYMENT: {S.CONFIRMED, S.CANCELLED, S.PAYMENT_EXPIRED},
    S.CONFIRMED: {S.CHECKED_IN, S.CANCELLED, S.NO_SHOW},
    S.CHECKED_IN: {S.CHECKED_OUT},
    S.PAYMENT_EXPIRED: {S.CONFIRMED},   # chỉ khi thanh toán trễ hợp lệ (RBLQH21b)
}
_ZERO_REMAINING = {S.CANCELLED, S.NO_SHOW, S.PAYMENT_EXPIRED}   # RBLTT03


class BookingStateMachine:
    def transition(self, uow: UnitOfWork, booking, new_status: str, *, source: ChangedSource,
                   by: int | None, reason: str | None, now: datetime) -> None:
        old = booking.booking_status
        if new_status not in _ALLOWED.get(old, set()):
            raise InvalidStateTransition(f"Booking cannot change from {old} to {new_status}.")
        if (source in (ChangedSource.USER, ChangedSource.ADMIN)) != (by is not None):   # RBLTT15
            raise ValueError("changed_by bắt buộc với USER/ADMIN và phải NULL với tiến trình hệ thống")
        booking.booking_status = new_status
        if new_status in _ZERO_REMAINING:
            booking.remaining_amount = Decimal(0)
        elif new_status == S.CONFIRMED:
            booking.remaining_amount = max(Decimal(0), booking.total_amount - booking.paid_amount)
        if new_status == S.CANCELLED:
            booking.cancelled_at = now
            booking.cancellation_reason = reason
        uow.bookings.add_status_history(booking, old_status=old, new_status=new_status, changed_by=by,
                                        changed_source=source, change_reason=reason, changed_at=now)


class BookingLocker:
    """Quy ước khóa DUY NHẤT cho mọi luồng sửa booking/giải phóng hold (RBLQH18, RBLQH20, VI.5):
        1) khóa các ROOM_TYPE liên quan theo id tăng dần;  2) khóa hàng BOOKING.
    Đọc không khóa trước để biết loại phòng, sau đó đọc lại có khóa để thấy trạng thái mới nhất."""

    def lock(self, uow: UnitOfWork, *, booking_id: int | None = None, booking_code: str | None = None):
        probe = uow.bookings.get(booking_id) if booking_id is not None else uow.bookings.get_by_code(booking_code)
        if probe is None:
            return None
        uow.room_types.lock_for_update([i.room_type_id for i in probe.items])
        return uow.bookings.get_for_update(probe.booking_id)
