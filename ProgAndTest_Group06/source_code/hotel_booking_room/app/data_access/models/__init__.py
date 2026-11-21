"""Import tất cả model để Base.metadata biết đủ bảng (create_all / Alembic)."""
from .account import Account
from .base import Base
from .booking import (Booking, BookingGuest, BookingItem, BookingNightRate, BookingRoomAssignment,
                      BookingStatusHistory)
from .deposit_level import DepositLevel
from .hotel import Hotel
from .promotion import Promotion, PromotionRedemption, PromotionRoomType
from .role import Role
from .room import Room
from .room_maintenance import RoomMaintenance
from .room_rate import HolidayDate, RoomRate, RoomRateHoliday
from .room_type import RoomType
from .system_setting import SystemSetting
from .specification import SpecificationModelRegistry, load_specification_models

# Khóa engine/charset cho mọi bảng, không phụ thuộc cấu hình mặc định của server MySQL.
for _table in Base.metadata.tables.values():
    _table.dialect_options["mysql"]["engine"] = "InnoDB"
    _table.dialect_options["mysql"]["charset"] = "utf8mb4"
    _table.dialect_options["mysql"]["collate"] = "utf8mb4_unicode_ci"

__all__ = [
    "Base", "Role", "Account", "Hotel", "RoomType", "Room", "RoomMaintenance",
    "RoomRate", "HolidayDate", "RoomRateHoliday", "DepositLevel", "SystemSetting",
    "Promotion", "PromotionRoomType", "PromotionRedemption",
    "Booking", "BookingItem", "BookingNightRate", "BookingRoomAssignment", "BookingGuest",
    "BookingStatusHistory", "SpecificationModelRegistry", "load_specification_models",
]
