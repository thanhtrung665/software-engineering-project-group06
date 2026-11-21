from fastapi import APIRouter, Depends, Request

from app.business.services import PaymentService
from app.composition import get_payment_service
from app.presentation.schemas.payment import PaymentCallbackResponse, PaymentCheckoutResponse
from app.presentation.security import get_current_account_id

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/vnpay/{booking_code}/create", response_model=PaymentCheckoutResponse,
             summary="Tạo giao dịch VNPay cho tiền cọc (booking đang Pending Payment)")
def create_vnpay_payment(booking_code: str, request: Request,
                         account_id: int = Depends(get_current_account_id),
                         service: PaymentService = Depends(get_payment_service)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    return service.create_vnpay_checkout(account_id, booking_code, client_ip)


@router.get("/vnpay/return", response_model=PaymentCallbackResponse,
            summary="VNPay redirect/callback: chỉ đổi dữ liệu khi chữ ký hợp lệ")
def vnpay_return(request: Request, service: PaymentService = Depends(get_payment_service)):
    return service.handle_vnpay_return(dict(request.query_params))
