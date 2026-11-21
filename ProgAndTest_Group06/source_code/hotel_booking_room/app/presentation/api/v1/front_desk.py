from fastapi import APIRouter, Depends

from app.business.frontdesk.frontdesk_service import FrontDeskService
from app.business.services import RefundService
from app.composition import get_front_desk_service, get_refund_service
from app.presentation.schemas.front_desk import (CheckInRequest, CheckInResponse, CheckOutRequest, CheckOutResponse,
                                                 NoShowResponse)
from app.presentation.security import get_current_account_id

router = APIRouter(prefix="/front-desk", tags=["front-desk"])


@router.post("/{booking_code}/check-in", response_model=CheckInResponse, summary="Check-in tại quầy")
def check_in(booking_code: str, body: CheckInRequest, admin_id: int = Depends(get_current_account_id),
             service: FrontDeskService = Depends(get_front_desk_service)):
    return service.check_in(booking_code, admin_id, [a.model_dump() for a in body.assignments],
                            [g.model_dump() for g in body.guests], body.collected_amount, body.payment_method)


@router.post("/{booking_code}/check-out", response_model=CheckOutResponse, summary="Check-out, xuất hóa đơn")
def check_out(booking_code: str, body: CheckOutRequest, admin_id: int = Depends(get_current_account_id),
              service: FrontDeskService = Depends(get_front_desk_service)):
    return service.check_out(booking_code, admin_id, [c.model_dump() for c in body.extra_charges],
                             body.collected_amount, body.payment_method)


@router.post("/{booking_code}/no-show", response_model=NoShowResponse,
             summary="Đánh dấu No-show, tính phí đêm đầu và hoàn phần còn lại")
def no_show(booking_code: str, admin_id: int = Depends(get_current_account_id),
            service: FrontDeskService = Depends(get_front_desk_service),
            refunds: RefundService = Depends(get_refund_service)):
    result = service.mark_no_show(booking_code, admin_id)
    # Transaction no-show đã commit; giờ mới gọi cổng thanh toán cho các khoản hoàn PENDING.
    return {**result, "gateway_refunds": refunds.process_pending_gateway_refunds(booking_code)}
