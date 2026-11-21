from dataclasses import dataclass
from datetime import date, timedelta

from app.business.exceptions import ValidationFailed

MAX_NIGHTS = 30


@dataclass(frozen=True)
class StayPeriod:
    """Khoảng lưu trú: đêm tính từ check-in tới đêm TRƯỚC check-out (Shared Business Rules)."""
    check_in: date
    check_out: date

    @classmethod
    def validated(cls, check_in: date, check_out: date, today: date) -> "StayPeriod":
        """today = ngày hiện tại theo giờ Việt Nam. Lỗi gắn với trường nhập sai (UC Search A1)."""
        if check_in < today:
            raise ValidationFailed("Check-in date cannot be in the past.", {"field": "check_in_date"})
        if check_out <= check_in:
            raise ValidationFailed("Check-out date must be after the check-in date.",
                                   {"field": "check_out_date"})
        period = cls(check_in, check_out)
        if period.nights > MAX_NIGHTS:
            raise ValidationFailed(f"A booking is limited to {MAX_NIGHTS} nights.",
                                   {"field": "check_out_date"})
        return period

    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days

    @property
    def night_dates(self) -> list[date]:
        return [self.check_in + timedelta(days=i) for i in range(self.nights)]

    @property
    def last_night(self) -> date:
        return self.check_out - timedelta(days=1)
