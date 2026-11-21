"""Truy vấn số liệu tồn kho thô (RBLQH01). Quy tắc tính nằm ở tầng Business."""
from datetime import date, datetime

from sqlalchemy import and_, func, or_, select, true

from app.core.enums import BookingStatus, MaintenanceStatus
from app.data_access.models import Booking, BookingItem, Room, RoomMaintenance
from .base import BaseRepository


class InventoryRepository(BaseRepository[Room]):
    model = Room

    def count_active_rooms(self, room_type_ids) -> dict[int, int]:
        stmt = (select(Room.room_type_id, func.count(Room.room_id))
                .where(Room.room_type_id.in_(list(room_type_ids)), Room.is_active == true())
                .group_by(Room.room_type_id))
        return {rid: n for rid, n in self.session.execute(stmt)}

    def maintenance_periods(self, room_type_ids, first_night: date, last_night: date
                            ) -> list[tuple[int, int, date, date]]:
        """(room_type_id, room_id, start, end_inclusive) của phòng đang active, giao với khoảng đêm."""
        stmt = (select(Room.room_type_id, Room.room_id, RoomMaintenance.start_date, RoomMaintenance.end_date)
                .join(RoomMaintenance, RoomMaintenance.room_id == Room.room_id)
                .where(Room.room_type_id.in_(list(room_type_ids)), Room.is_active == true(),
                       RoomMaintenance.maintenance_status.in_(
                           [MaintenanceStatus.PLANNED, MaintenanceStatus.IN_PROGRESS]),
                       RoomMaintenance.start_date <= last_night, RoomMaintenance.end_date >= first_night))
        return [tuple(r) for r in self.session.execute(stmt)]

    def booked_quantities(self, room_type_ids, check_in: date, check_out: date, now: datetime,
                          exclude_booking_id: int | None = None) -> list[tuple[int, date, date, int]]:
        """(room_type_id, check_in, check_out, quantity) của booking đang chiếm phòng:
        CONFIRMED / CHECKED_IN, hoặc PENDING_PAYMENT còn trong thời hạn giữ (hold_expires_at > now)."""
        counted = or_(
            Booking.booking_status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
            and_(Booking.booking_status == BookingStatus.PENDING_PAYMENT, Booking.hold_expires_at > now),
        )
        stmt = (select(BookingItem.room_type_id, Booking.check_in_date, Booking.check_out_date,
                       BookingItem.quantity)
                .join(Booking, Booking.booking_id == BookingItem.booking_id)
                .where(BookingItem.room_type_id.in_(list(room_type_ids)),
                       Booking.check_in_date < check_out, Booking.check_out_date > check_in, counted))
        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.booking_id != exclude_booking_id)
        return [tuple(r) for r in self.session.execute(stmt)]
