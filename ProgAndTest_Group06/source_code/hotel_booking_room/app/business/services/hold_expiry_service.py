"""Giải phóng phòng khi quá hạn 15 phút (UC Book room A4, UC Process payment A2, RBLQH20, RBLQH23)."""
import logging
from typing import Callable

from app.business.clock import Clock
from app.business.dto import ExpiryReport
from app.business.services.booking_state import BookingLocker, BookingStateMachine
from app.business.services.promotion_service import PromotionLedger
from app.core.enums import BookingStatus, ChangedSource
from app.data_access.unit_of_work import UnitOfWork, run_in_transaction

log = logging.getLogger(__name__)


class HoldExpiryService:
    """Mỗi booking xử lý trong transaction riêng: lỗi một booking không chặn các booking khác.

    Idempotent: sau khi khóa, đọc lại trạng thái; chỉ giải phóng nếu VẪN là PENDING_PAYMENT và hold đã hết hạn.
    Booking vừa được thanh toán/hủy bởi luồng khác sẽ bị bỏ qua (không bao giờ giải phóng booking đã Confirmed)."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork], clock: Clock, *, batch_size: int = 200,
                 state: BookingStateMachine | None = None, ledger: PromotionLedger | None = None,
                 locker: BookingLocker | None = None) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._batch_size = batch_size
        self._state = state or BookingStateMachine()
        self._ledger = ledger or PromotionLedger()
        self._locker = locker or BookingLocker()

    def expire_overdue_holds(self) -> ExpiryReport:
        now = self._clock.now()
        ids = run_in_transaction(self._uow_factory,
                                 lambda uow: uow.bookings.find_expired_hold_ids(now, self._batch_size),
                                 readonly=True)
        expired: list[str] = []
        skipped = failed = 0
        for booking_id in ids:
            try:
                code = self.expire_one(booking_id)
            except Exception:                                   # noqa: BLE001 – job nền không được dừng
                log.exception("Failed to expire hold of booking %s", booking_id)
                failed += 1
                continue
            if code is None:
                skipped += 1
            else:
                expired.append(code)
        return ExpiryReport(tuple(expired), skipped, failed)

    def expire_one(self, booking_id: int) -> str | None:
        """Trả về booking_code nếu vừa giải phóng; None nếu đã được xử lý/không còn quá hạn."""
        def work(uow: UnitOfWork) -> str | None:
            now = self._clock.now()
            booking = self._locker.lock(uow, booking_id=booking_id)
            if (booking is None or booking.booking_status != BookingStatus.PENDING_PAYMENT
                    or booking.hold_expires_at is None or booking.hold_expires_at > now):
                return None
            self._state.transition(uow, booking, BookingStatus.PAYMENT_EXPIRED,
                                   source=ChangedSource.SYSTEM_SCHEDULER, by=None,
                                   reason="Room hold expired without payment", now=now)
            self._ledger.release(uow, booking.booking_id)       # trả lại lượt dùng mã KM
            return booking.booking_code

        return run_in_transaction(self._uow_factory, work)
