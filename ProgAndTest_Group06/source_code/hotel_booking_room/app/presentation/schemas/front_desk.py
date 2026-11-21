from pydantic import BaseModel, Field

from app.presentation.schemas.payment import RefundBatchResponse


class AssignmentRequest(BaseModel):
    booking_item_id: int
    room_id: int
    upgrade_reason: str | None = None


class GuestRequest(BaseModel):
    full_name: str
    phone: str | None = None
    nationality: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    is_primary: bool = False
    room_id: int


class CheckInRequest(BaseModel):
    assignments: list[AssignmentRequest]
    guests: list[GuestRequest]
    collected_amount: int = 0
    payment_method: str | None = None


class ChargeRequest(BaseModel):
    item_type: str
    description: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)


class CheckOutRequest(BaseModel):
    extra_charges: list[ChargeRequest] = Field(default_factory=list)
    collected_amount: int = 0
    payment_method: str | None = None


class CheckInResponse(BaseModel):
    booking_code: str
    status: str
    rooms: list[int]
    collected: int


class CheckOutResponse(BaseModel):
    booking_code: str
    status: str
    invoice_id: int
    invoice_total: int
    collected: int


class NoShowResponse(BaseModel):
    booking_code: str
    status: str
    fee: int
    refund: int
    gateway_refunds: RefundBatchResponse
