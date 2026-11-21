"""Tồn kho phòng theo đêm + khóa điều phối (RBLQH01, RBLQH03, RBLQH18)."""
from datetime import date, datetime

from app.business.domain import AvailabilityCalculator, StayPeriod
from app.business.exceptions import RoomSoldOutError
from app.data_access.unit_of_work import UnitOfWork

SOLD_OUT_MESSAGE = "This room type just sold out for your selected dates. Please choose another room type."


class InventoryService:
    def lock_inventory(self, uow: UnitOfWork, room_type_ids) -> None:
        """BƯỚC BẮT BUỘC trước khi kiểm tra/giữ phòng: SELECT ... FOR UPDATE các ROOM_TYPE liên quan,
        theo room_type_id tăng dần. Khóa giữ đến hết transaction => các request đặt cùng loại phòng
        chạy tuần tự; request sau thấy dữ liệu đã commit của request trước."""
        uow.room_types.lock_for_update(room_type_ids)

    def availability(self, uow: UnitOfWork, room_type_ids, period: StayPeriod, now: datetime,
                     exclude_booking_id: int | None = None) -> dict[int, dict[date, int]]:
        """Số phòng trống từng đêm của từng loại phòng, tính lại từ DB (không dùng số liệu cũ từ UI)."""
        ids = sorted(set(room_type_ids))
        active = uow.inventory.count_active_rooms(ids)
        maint_rows = uow.inventory.maintenance_periods(ids, period.check_in, period.last_night)
        booked_rows = uow.inventory.booked_quantities(ids, period.check_in, period.check_out, now,
                                                      exclude_booking_id)
        result: dict[int, dict[date, int]] = {}
        for rid in ids:
            result[rid] = AvailabilityCalculator.per_night(
                period, active.get(rid, 0),
                [(room, s, e) for t, room, s, e in maint_rows if t == rid],
                [(ci, co, q) for t, ci, co, q in booked_rows if t == rid])
        return result

    def ensure_available(self, uow: UnitOfWork, requested: dict[int, int], period: StayPeriod,
                         now: datetime, exclude_booking_id: int | None = None) -> None:
        """Mọi đêm: số phòng trống >= số phòng yêu cầu; nếu không -> RoomSoldOutError (UC Book room A3)."""
        per_type = self.availability(uow, requested.keys(), period, now, exclude_booking_id)
        sold_out = sorted(rid for rid, qty in requested.items() if min(per_type[rid].values()) < qty)
        if sold_out:
            raise RoomSoldOutError(SOLD_OUT_MESSAGE, {"room_type_ids": sold_out})
