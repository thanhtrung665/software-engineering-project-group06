from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RoomSelectionRequest(BaseModel):
    room_type_id: int
    quantity: int = Field(ge=1, le=5)
    adults: int = Field(ge=1)
    children: int = Field(default=0, ge=0)


class OccupantRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=1, max_length=20)
    nationality: str | None = Field(default=None, max_length=80)


class QuoteRequest(BaseModel):
    check_in_date: date
    check_out_date: date
    rooms: list[RoomSelectionRequest] = Field(min_length=1)
    promo_code: str | None = Field(default=None, max_length=40)
    deposit_percentage: Decimal | None = None


class CreateBookingRequest(BaseModel):
    check_in_date: date
    check_out_date: date
    rooms: list[RoomSelectionRequest] = Field(min_length=1)
    deposit_percentage: Decimal
    accept_terms: bool
    promo_code: str | None = Field(default=None, max_length=40)
    occupant: OccupantRequest | None = None
    special_requests: str | None = Field(default=None, max_length=2000)
    estimated_arrival_time: time | None = None
    expected_total_amount: Decimal | None = Field(
        default=None, description="Tổng tiền đã hiển thị ở bước review; lệch -> 409 PRICE_CHANGED (A6)")


class CancelPendingRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


# ---------------- responses (số tiền VND nguyên) ----------------
class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class NightPriceResponse(_Out):
    stay_date: date
    rate_type: str
    unit_price: int
    quantity: int
    night_total: int
    night_discount: int


class QuoteLineResponse(_Out):
    room_type_id: int
    room_type_code: str
    quantity: int
    adults: int
    children: int
    nights: list[NightPriceResponse]
    line_subtotal: int
    line_discount: int
    line_total: int


class DepositOptionResponse(_Out):
    percentage: Decimal
    deposit_amount: int
    balance_at_check_in: int


class QuoteResponse(_Out):
    check_in_date: date
    check_out_date: date
    nights: int
    lines: list[QuoteLineResponse]
    subtotal_amount: int
    discount_amount: int
    total_amount: int
    promo_code: str | None
    deposit_options: list[DepositOptionResponse]
    deposit_percentage: Decimal | None
    deposit_amount: int | None
    balance_at_check_in: int | None
    policy: dict
    currency: str
    vat_included: bool
    room_assignment_note: str


class OccupantResponse(_Out):
    full_name: str
    phone: str | None
    nationality: str | None


class BookingResponse(_Out):
    booking_code: str
    booking_status: str
    payment_status: str
    check_in_date: date
    check_out_date: date
    nights: int
    adults: int
    children: int
    room_count: int
    lines: list[QuoteLineResponse]
    subtotal_amount: int
    discount_amount: int
    total_amount: int
    deposit_percentage: Decimal
    deposit_amount: int
    paid_amount: int
    remaining_amount: int
    promo_code: str | None
    contact_name: str
    contact_phone: str
    contact_email: str | None
    occupant: OccupantResponse | None
    special_requests: str | None
    estimated_arrival_time: time | None
    special_requests_notice: str | None
    hold_expires_at: datetime | None
    hold_remaining_seconds: int | None
    policy: dict
    created_at: datetime
    currency: str
