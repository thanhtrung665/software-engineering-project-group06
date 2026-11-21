from fastapi import APIRouter, Depends

from app.business.dto import CreateBookingCommand, OccupantDTO, QuoteCommand, RoomSelectionDTO
from app.business.services import BookingHoldService
from app.composition import get_booking_hold_service
from app.presentation.schemas.booking import (BookingResponse, CancelPendingRequest, CreateBookingRequest,
                                              QuoteRequest, QuoteResponse)
from app.presentation.security import get_current_account_id

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _rooms(body) -> tuple[RoomSelectionDTO, ...]:
    return tuple(RoomSelectionDTO(r.room_type_id, r.quantity, r.adults, r.children) for r in body.rooms)


@router.post("/quote", response_model=QuoteResponse,
             summary="Review booking: tính giá, áp mã khuyến mãi, tiền cọc (chưa giữ phòng)")
def quote_booking(body: QuoteRequest, account_id: int = Depends(get_current_account_id),
                  service: BookingHoldService = Depends(get_booking_hold_service)):
    return service.quote(account_id, QuoteCommand(
        body.check_in_date, body.check_out_date, _rooms(body), body.promo_code, body.deposit_percentage))


@router.post("", response_model=BookingResponse, status_code=201,
             summary="Confirm booking: tạo booking Pending Payment và giữ phòng 15 phút")
def create_booking(body: CreateBookingRequest, account_id: int = Depends(get_current_account_id),
                   service: BookingHoldService = Depends(get_booking_hold_service)):
    occupant = OccupantDTO(**body.occupant.model_dump()) if body.occupant else None
    return service.create_booking(account_id, CreateBookingCommand(
        check_in_date=body.check_in_date, check_out_date=body.check_out_date, rooms=_rooms(body),
        deposit_percentage=body.deposit_percentage, accept_terms=body.accept_terms, promo_code=body.promo_code,
        occupant=occupant, special_requests=body.special_requests,
        estimated_arrival_time=body.estimated_arrival_time, expected_total_amount=body.expected_total_amount))


@router.get("/{booking_code}", response_model=BookingResponse,
            summary="Chi tiết booking (kèm hold_remaining_seconds cho đồng hồ đếm ngược)")
def get_booking(booking_code: str, account_id: int = Depends(get_current_account_id),
                service: BookingHoldService = Depends(get_booking_hold_service)):
    return service.get_booking(account_id, booking_code)


@router.post("/{booking_code}/cancel-pending", response_model=BookingResponse,
             summary="Hủy booking đang Pending Payment (nhả phòng ngay, hoàn mã KM)")
def cancel_pending(booking_code: str, body: CancelPendingRequest | None = None,
                   account_id: int = Depends(get_current_account_id),
                   service: BookingHoldService = Depends(get_booking_hold_service)):
    return service.cancel_pending_booking(account_id, booking_code, body.reason if body else None)
