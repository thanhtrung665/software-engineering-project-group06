"""Chọn giá từng đêm theo thứ tự ưu tiên HOLIDAY > SEASON > WEEKEND > BASE (RBLQH05)."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.business.exceptions import ConfigurationError
from app.core.enums import RateType


@dataclass(frozen=True)
class RateRule:
    rate_id: int
    rate_type: str
    price: Decimal
    start: date | None = None
    end: date | None = None            # inclusive
    weekday_no: int | None = None      # ISO: Thứ Sáu=5, Thứ Bảy=6
    holiday_dates: frozenset[date] = frozenset()


@dataclass(frozen=True)
class ResolvedRate:
    rate_id: int
    rate_type: str
    price: Decimal


class RateBook:
    """Bảng giá đang áp dụng của MỘT loại phòng."""

    def __init__(self, room_type_id: int, rules: list[RateRule]) -> None:
        self.room_type_id = room_type_id
        self._holiday = [r for r in rules if r.rate_type == RateType.HOLIDAY]
        self._season = [r for r in rules if r.rate_type == RateType.SEASON]
        self._weekend = [r for r in rules if r.rate_type == RateType.WEEKEND]
        self._base = next((r for r in rules if r.rate_type == RateType.BASE), None)

    def resolve(self, night: date) -> ResolvedRate:
        for rule in self._holiday:
            if night in rule.holiday_dates:
                return ResolvedRate(rule.rate_id, RateType.HOLIDAY, rule.price)
        for rule in self._season:
            if rule.start and rule.end and rule.start <= night <= rule.end:
                return ResolvedRate(rule.rate_id, RateType.SEASON, rule.price)
        for rule in self._weekend:
            if rule.weekday_no == night.isoweekday():
                return ResolvedRate(rule.rate_id, RateType.WEEKEND, rule.price)
        if self._base is None:
            raise ConfigurationError(f"Room type {self.room_type_id} has no active base rate.")
        return ResolvedRate(self._base.rate_id, RateType.BASE, self._base.price)
