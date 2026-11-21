"""Phần "giữ phòng" của UC Process payment: chuyển hold -> đặt phòng xác nhận (bước 6), thanh toán trễ (A4).

Hàm nhận UoW của NGƯỜI GỌI (service thanh toán) để cùng một transaction với việc ghi PAYMENT và cập nhật
paid_amount / payment_status (RBLQH22, NFR Reliability). Hàm KHÔNG commit. Sau khi gọi, service thanh toán:
  CONFIRMED / RESTORED       -> ghi PAYMENT SUCCESS, tính payment_status (RBLQH29), gửi email xác nhận.
  ALREADY_CONFIRMED          -> callback trùng: xử lý idempotent; phần vượt mức cọc thì hoàn tiền (RBLQH21c).
  REFUND_REQUIRED            -> hoàn tiền 100% tự động + email (RBLQH21 a/b).
"""
from datetime import datetime, timedelta
from enum import StrEnum

from app.business.clock import Clock
from app.business.exceptions import NotFoundError
from app.business.services.booking_state import BookingLocker, BookingStateMachine
from app.business.services.inventory_service import InventoryService
from app.business.services.promotion_service import PromotionLedger
from app.business.services.settings_provider import BookingSettingsProvider
from app.business.domain import StayPeriod
from app.business.exceptions import RoomSoldOutError
from app.core.enums import BookingStatus, ChangedSource
from app.core.timeutil import vn_local_to_utc_naive
from app.data_access.unit_of_work import UnitOfWork


class ConfirmationOutcome(StrEnum):
    CONFIRMED = "CONFIRMED"                  # hold còn hạn -> Confirmed
    RESTORED = "RESTORED"                    # đã hết hạn nhưng còn phòng & chưa quá no-show -> Confirmed lại
    ALREADY_CONFIRMED = "ALREADY_CONFIRMED"  # đã Confirmed/Checked-in/out: không đổi gì
    REFUND_REQUIRED = "REFUND_REQUIRED"      # Cancelled/No-show/hết phòng/quá no-show: hoàn tiền đầy đủ


class HoldConfirmationService:
    def __init__(self, clock: Clock, *, inventory: InventoryService | None = None,
                 state: BookingStateMachine | None = None, ledger: PromotionLedger | None = None,
                 locker: BookingLocker | None = None, settings: BookingSettingsProvider | None = None,
                 ) -> None:
        self._clock = clock
        self._inventory = inventory or InventoryService()
        self._state = state or BookingStateMachine()
        self._ledger = ledger or PromotionLedger()
        self._locker = locker or BookingLocker()
        self._settings = settings or BookingSettingsProvider()

    def confirm_paid_booking(self, uow: UnitOfWork, booking_code: str) -> ConfirmationOutcome:
        now = self._clock.now()
        booking = self._locker.lock(uow, booking_code=booking_code)        # ROOM_TYPE -> BOOKING
        if booking is None:
            raise NotFoundError(f"Booking {booking_code} not found")
        status = booking.booking_status

        if status == BookingStatus.PENDING_PAYMENT:
            if booking.hold_expires_at is not None and now < booking.hold_expires_at:
                self._confirm(uow, booking, now, "Payment received within the room hold")      # RBLQH19
                return ConfirmationOutcome.CONFIRMED
            # Hold đã quá hạn nhưng job chưa quét: luồng thường KHÔNG được xác nhận -> hết hạn rồi xét như thanh toán trễ
            self._state.transition(uow, booking, BookingStatus.PAYMENT_EXPIRED,
                                   source=ChangedSource.SYSTEM_SCHEDULER, by=None,
                                   reason="Room hold expired without payment", now=now)
            self._ledger.release(uow, booking.booking_id)
            status = BookingStatus.PAYMENT_EXPIRED

        if status == BookingStatus.PAYMENT_EXPIRED:
            return self._try_restore(uow, booking, now)
        if status in (BookingStatus.CANCELLED, BookingStatus.NO_SHOW):
            return ConfirmationOutcome.REFUND_REQUIRED
        return ConfirmationOutcome.ALREADY_CONFIRMED

    # ---- nội bộ
    def _confirm(self, uow, booking, now: datetime, reason: str) -> None:
        self._state.transition(uow, booking, BookingStatus.CONFIRMED, source=ChangedSource.PAYMENT_GATEWAY,
                               by=None, reason=reason, now=now)
        self._ledger.consume(uow, booking.booking_id)       # RESERVED -> CONSUMED

    def _try_restore(self, uow, booking, now: datetime) -> ConfirmationOutcome:
        """RBLQH21(b): kiểm tra lại no-show cut-off + tồn kho (đã khóa ROOM_TYPE) trong cùng transaction."""
        settings = self._settings.load(uow)
        cutoff = vn_local_to_utc_naive(booking.check_in_date + timedelta(days=1), settings.no_show_cutoff)
        if now >= cutoff:
            return ConfirmationOutcome.REFUND_REQUIRED
        period = StayPeriod(booking.check_in_date, booking.check_out_date)
        try:
            self._inventory.ensure_available(
                uow, {i.room_type_id: i.quantity for i in booking.items}, period, now,
                exclude_booking_id=booking.booking_id)
        except RoomSoldOutError:
            return ConfirmationOutcome.REFUND_REQUIRED
        self._state.transition(uow, booking, BookingStatus.CONFIRMED, source=ChangedSource.PAYMENT_GATEWAY,
                               by=None, reason="Late payment accepted: rooms still available", now=now)
        self._ledger.reinstate(uow, booking.booking_id)     # ghi lại lượt dùng KM dù đã chạm total_usage_limit
        return ConfirmationOutcome.RESTORED
