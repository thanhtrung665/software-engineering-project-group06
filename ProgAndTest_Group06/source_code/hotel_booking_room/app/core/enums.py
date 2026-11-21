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


class BookingStatus(StrEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    CANCELLED = "CANCELLED"
    PAYMENT_EXPIRED = "PAYMENT_EXPIRED"
    NO_SHOW = "NO_SHOW"


class PaymentStatus(StrEnum):
    UNPAID = "UNPAID"
    DEPOSIT_PAID = "DEPOSIT_PAID"
    FULLY_PAID = "FULLY_PAID"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    REFUND_FAILED = "REFUND_FAILED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    REFUNDED = "REFUNDED"


class BookingSource(StrEnum):
    ONLINE = "ONLINE"
    FRONT_DESK = "FRONT_DESK"


class ChangedSource(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"
    SYSTEM_SCHEDULER = "SYSTEM_SCHEDULER"
    PAYMENT_GATEWAY = "PAYMENT_GATEWAY"


class RateType(StrEnum):
    BASE = "BASE"
    WEEKEND = "WEEKEND"
    SEASON = "SEASON"
    HOLIDAY = "HOLIDAY"


class DiscountType(StrEnum):
    PERCENT = "PERCENT"
    FIXED = "FIXED"


class PromotionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"


class RedemptionStatus(StrEnum):
    RESERVED = "RESERVED"    # đang giữ trong thời gian hold
    CONSUMED = "CONSUMED"    # đã thanh toán
    RELEASED = "RELEASED"    # đã hoàn lại


class MaintenanceStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SettingKey(StrEnum):
    CHECK_IN_TIME = "CHECK_IN_TIME"
    CHECK_OUT_TIME = "CHECK_OUT_TIME"
    HOLD_MINUTES = "HOLD_MINUTES"
    NO_SHOW_CUTOFF = "NO_SHOW_CUTOFF"
    CANCELLATION_HOURS = "CANCELLATION_HOURS"
    CANCELLATION_FEE_RULE = "CANCELLATION_FEE_RULE"
    MAX_PENDING_BOOKINGS = "MAX_PENDING_BOOKINGS"
