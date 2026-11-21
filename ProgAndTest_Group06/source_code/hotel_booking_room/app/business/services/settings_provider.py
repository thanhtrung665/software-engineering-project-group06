"""Đọc tham số nghiệp vụ từ SYSTEM_SETTING (RBLQH17) – không hard-code; có mặc định theo đặc tả."""
from dataclasses import dataclass
from datetime import time

from app.core.enums import SettingKey
from app.data_access.unit_of_work import UnitOfWork


def _parse_time(value, default: time) -> time:
    try:
        h, m = str(value).split(":")[:2]
        return time(int(h), int(m))
    except (ValueError, TypeError):
        return default


@dataclass(frozen=True)
class BookingSettings:
    hold_minutes: int = 15
    max_pending_bookings: int = 3
    check_in_time: time = time(14, 0)
    check_out_time: time = time(12, 0)
    no_show_cutoff: time = time(6, 0)          # 06:00 ngày sau ngày check-in
    cancellation_free_hours: int = 48
    cancellation_fee_rule: object = None

    def policy_snapshot(self) -> dict:
        """Snapshot chính sách tại thời điểm đặt (BOOKING.policy_snapshot, có version)."""
        return {
            "version": 1,
            "hold_minutes": self.hold_minutes,
            "check_in_time": self.check_in_time.strftime("%H:%M"),
            "check_out_time": self.check_out_time.strftime("%H:%M"),
            "no_show_cutoff": self.no_show_cutoff.strftime("%H:%M"),
            "cancellation_free_hours": self.cancellation_free_hours,
            "cancellation_fee_rule": self.cancellation_fee_rule or {"type": "FIRST_NIGHT"},
            "vat_included": True,
        }


class BookingSettingsProvider:
    def load(self, uow: UnitOfWork) -> BookingSettings:
        raw = uow.settings.get_all()
        d = BookingSettings()

        def num(key: SettingKey, default: int) -> int:
            try:
                value = int(raw.get(key, default))
                return value if value > 0 else default
            except (TypeError, ValueError):
                return default

        return BookingSettings(
            hold_minutes=num(SettingKey.HOLD_MINUTES, d.hold_minutes),
            max_pending_bookings=num(SettingKey.MAX_PENDING_BOOKINGS, d.max_pending_bookings),
            check_in_time=_parse_time(raw.get(SettingKey.CHECK_IN_TIME), d.check_in_time),
            check_out_time=_parse_time(raw.get(SettingKey.CHECK_OUT_TIME), d.check_out_time),
            no_show_cutoff=_parse_time(raw.get(SettingKey.NO_SHOW_CUTOFF), d.no_show_cutoff),
            cancellation_free_hours=num(SettingKey.CANCELLATION_HOURS, d.cancellation_free_hours),
            cancellation_fee_rule=raw.get(SettingKey.CANCELLATION_FEE_RULE),
        )
