"""DTO của tầng Business: tầng trên không phải biết ORM entity."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RoomTypeDTO:
    room_type_id: int
    room_type_code: str
    area_sqm: Decimal
    bed_type: str
    max_adults: int
    max_children: int
    view_direction: str | None
    breakfast_included: bool
    base_price: Decimal
    selling_status: str


# ======================= Book room / giữ phòng =======================
from datetime import date, datetime, time  # noqa: E402


@dataclass(frozen=True)
class RoomSelectionDTO:
    room_type_id: int
    quantity: int
    adults: int
    children: int = 0


@dataclass(frozen=True)
class OccupantDTO:
    full_name: str
    phone: str
    nationality: str | None = None


@dataclass(frozen=True)
class QuoteCommand:
    check_in_date: date
    check_out_date: date
    rooms: tuple[RoomSelectionDTO, ...]
    promo_code: str | None = None
    deposit_percentage: Decimal | None = None


@dataclass(frozen=True)
class CreateBookingCommand:
    check_in_date: date
    check_out_date: date
    rooms: tuple[RoomSelectionDTO, ...]
    deposit_percentage: Decimal
    accept_terms: bool
    promo_code: str | None = None
    occupant: OccupantDTO | None = None            # None -> lấy từ tài khoản
    special_requests: str | None = None
    estimated_arrival_time: time | None = None
    expected_total_amount: Decimal | None = None   # tổng tiền user đã thấy ở bước review (A6)


@dataclass(frozen=True)
class NightPriceDTO:
    stay_date: date
    rate_type: str
    unit_price: Decimal
    quantity: int
    night_total: Decimal
    night_discount: Decimal
    source_room_rate_id: int | None = None


@dataclass(frozen=True)
class QuoteLineDTO:
    room_type_id: int
    room_type_code: str
    quantity: int
    adults: int
    children: int
    nights: tuple[NightPriceDTO, ...]
    line_subtotal: Decimal
    line_discount: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class DepositOptionDTO:
    percentage: Decimal
    deposit_amount: Decimal
    balance_at_check_in: Decimal


@dataclass(frozen=True)
class QuoteDTO:
    check_in_date: date
    check_out_date: date
    nights: int
    lines: tuple[QuoteLineDTO, ...]
    subtotal_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    promo_code: str | None
    deposit_options: tuple[DepositOptionDTO, ...]
    deposit_percentage: Decimal | None
    deposit_amount: Decimal | None
    balance_at_check_in: Decimal | None
    policy: dict
    currency: str = "VND"
    vat_included: bool = True
    room_assignment_note: str = "The specific room number is assigned by the hotel at check-in."


@dataclass(frozen=True)
class OccupantInfoDTO:
    full_name: str
    phone: str | None
    nationality: str | None


@dataclass(frozen=True)
class BookingDTO:
    booking_code: str
    booking_status: str
    payment_status: str
    check_in_date: date
    check_out_date: date
    nights: int
    adults: int
    children: int
    room_count: int
    lines: tuple[QuoteLineDTO, ...]
    subtotal_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    deposit_percentage: Decimal
    deposit_amount: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal
    promo_code: str | None
    contact_name: str
    contact_phone: str
    contact_email: str | None
    occupant: OccupantInfoDTO | None
    special_requests: str | None
    estimated_arrival_time: time | None
    special_requests_notice: str | None
    hold_expires_at: datetime | None          # có múi giờ UTC+7
    hold_remaining_seconds: int | None        # tính ở server: FE đếm ngược không phụ thuộc đồng hồ máy khách
    policy: dict
    created_at: datetime
    currency: str = "VND"


@dataclass(frozen=True)
class ExpiryReport:
    expired_booking_codes: tuple[str, ...]
    skipped: int      # đã được xử lý bởi luồng khác (thanh toán/hủy/job khác) – idempotent
    failed: int


# ======================= Process payment =======================
@dataclass(frozen=True)
class PaymentCheckoutDTO:
    payment_reference: str
    amount: int
    currency: str
    payment_url: str


@dataclass(frozen=True)
class RefundBatchResultDTO:
    processed: int
    errors: tuple[dict, ...] = ()
    reason: str | None = None


@dataclass(frozen=True)
class PaymentCallbackResultDTO:
    status: str                              # SUCCESS / FAILED
    booking_payment_reference: str
    idempotent: bool = False                 # callback trùng, đã xử lý trước đó
    outcome: str | None = None               # CONFIRMED / RESTORED / ALREADY_CONFIRMED / REFUND_REQUIRED
    refund_queued: bool = False
    refund_result: RefundBatchResultDTO | None = None
