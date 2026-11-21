"""Hằng số nghiệp vụ dùng chung giữa các tầng (khớp Data Model mục VI)."""
from enum import StrEnum


class RoleCode(StrEnum):
    CUSTOMER = "CUSTOMER"
    MANAGER = "MANAGER"
    RECEPTIONIST = "RECEPTIONIST"


class AccountStatus(StrEnum):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"


class SellingStatus(StrEnum):
    ON_SALE = "ON_SALE"
    DISCONTINUED = "DISCONTINUED"


class RoomStatus(StrEnum):
    VACANT = "VACANT"
    OCCUPIED = "OCCUPIED"
    NEEDS_CLEANING = "NEEDS_CLEANING"
    MAINTENANCE = "MAINTENANCE"
