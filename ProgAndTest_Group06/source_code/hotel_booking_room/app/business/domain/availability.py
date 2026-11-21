"""Tính số phòng trống từng đêm – Shared Business Rules / RBLQH01 (thuần, không truy cập DB)."""
from datetime import date

from .stay_period import StayPeriod


class AvailabilityCalculator:
    """Available(night) = phòng active − phòng bảo trì đêm đó − số phòng đã bị booking chiếm đêm đó."""

    @staticmethod
    def per_night(period: StayPeriod, active_rooms: int,
                  maintenance: list[tuple[int, date, date]],
                  booked: list[tuple[date, date, int]]) -> dict[date, int]:
        """maintenance: (room_id, start, end_inclusive); booked: (check_in, check_out, quantity)."""
        result: dict[date, int] = {}
        for night in period.night_dates:
            under_maintenance = len({rid for rid, s, e in maintenance if s <= night <= e})
            taken = sum(q for ci, co, q in booked if ci <= night < co)
            result[night] = max(0, active_rooms - under_maintenance - taken)
        return result
