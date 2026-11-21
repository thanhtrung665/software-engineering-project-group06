from datetime import date

from sqlalchemy import select, true

from app.data_access.models import HolidayDate, RoomRate, RoomRateHoliday
from .base import BaseRepository


class RateRepository(BaseRepository[RoomRate]):
    model = RoomRate

    def active_rates(self, room_type_ids) -> list[RoomRate]:
        stmt = (select(RoomRate)
                .where(RoomRate.room_type_id.in_(list(room_type_ids)), RoomRate.is_active == true())
                .order_by(RoomRate.room_rate_id))
        return list(self.session.scalars(stmt))

    def holiday_dates_by_rate(self, rate_ids) -> dict[int, set[date]]:
        """room_rate_id (HOLIDAY) -> các ngày lễ còn hiệu lực gắn với giá đó."""
        rate_ids = list(rate_ids)
        if not rate_ids:
            return {}
        stmt = (select(RoomRateHoliday.room_rate_id, HolidayDate.holiday_date)
                .join(HolidayDate, HolidayDate.holiday_date_id == RoomRateHoliday.holiday_date_id)
                .where(RoomRateHoliday.room_rate_id.in_(rate_ids), HolidayDate.is_active == true()))
        out: dict[int, set[date]] = {}
        for rid, d in self.session.execute(stmt):
            out.setdefault(rid, set()).add(d)
        return out
