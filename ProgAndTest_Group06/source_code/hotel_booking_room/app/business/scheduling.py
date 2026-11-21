"""Tiến trình nền định kỳ giải phóng hold quá hạn (đặc tả: "enforced by a background scheduled job")."""
import logging
import threading

from app.business.services.hold_expiry_service import HoldExpiryService

log = logging.getLogger(__name__)


class HoldExpiryScheduler:
    """Chạy HoldExpiryService mỗi `interval_seconds`. Tính đúng đắn KHÔNG phụ thuộc tần suất job:
    tồn kho và luồng thanh toán đều xét hold_expires_at, job chỉ dọn trạng thái + trả mã khuyến mãi."""

    def __init__(self, service: HoldExpiryService, interval_seconds: float = 30) -> None:
        self._service = service
        self._interval = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="hold-expiry", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout)

    def run_once(self):
        return self._service.expire_overdue_holds()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                report = self.run_once()
                if report.expired_booking_codes:
                    log.info("Released %d expired hold(s): %s", len(report.expired_booking_codes),
                             ", ".join(report.expired_booking_codes))
            except Exception:                                    # noqa: BLE001
                log.exception("Hold expiry run failed")
            self._stop.wait(self._interval)
