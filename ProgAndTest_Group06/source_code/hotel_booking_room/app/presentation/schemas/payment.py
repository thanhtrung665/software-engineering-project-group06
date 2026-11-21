from pydantic import BaseModel, ConfigDict


class PaymentCheckoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_reference: str
    amount: int
    currency: str
    payment_url: str


class RefundBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    processed: int
    errors: list[dict] = []
    reason: str | None = None


class PaymentCallbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    booking_payment_reference: str
    idempotent: bool = False
    outcome: str | None = None
    refund_queued: bool = False
    refund_result: RefundBatchResponse | None = None
