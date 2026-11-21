from datetime import datetime
from decimal import Decimal

from app.business.dto import BookingDTO, NightPriceDTO, OccupantInfoDTO, QuoteLineDTO
from app.core.timeutil import to_vn
from app.data_access.unit_of_work import UnitOfWork

SPECIAL_REQUEST_NOTICE = ("The hotel will endeavor to accommodate your requests subject to availability, "
                          "without guarantee. Any chargeable services will be settled at the front desk.")


class BookingMapper:
    def to_dto(self, uow: UnitOfWork, booking, now: datetime) -> BookingDTO:
        lines = tuple(self._line(item) for item in booking.items)
        redemption = uow.promotions.get_redemption_by_booking(booking.booking_id)
        promo_code = uow.promotions.get(redemption.promotion_id).promo_code if redemption else None
        primary = next((g for g in booking.guests if g.is_primary_guest), None)
        remaining = None
        if booking.hold_expires_at is not None and booking.booking_status == "PENDING_PAYMENT":
            remaining = max(0, int((booking.hold_expires_at - now).total_seconds()))
        return BookingDTO(
            booking_code=booking.booking_code, booking_status=booking.booking_status,
            payment_status=booking.payment_status, check_in_date=booking.check_in_date,
            check_out_date=booking.check_out_date,
            nights=(booking.check_out_date - booking.check_in_date).days,
            adults=booking.adults, children=booking.children, room_count=booking.room_count, lines=lines,
            subtotal_amount=booking.subtotal_amount, discount_amount=booking.discount_amount,
            total_amount=booking.total_amount, deposit_percentage=booking.deposit_percentage,
            deposit_amount=booking.deposit_amount, paid_amount=booking.paid_amount,
            remaining_amount=booking.remaining_amount, promo_code=promo_code,
            contact_name=booking.guest_contact_name, contact_phone=booking.guest_contact_phone,
            contact_email=booking.guest_contact_email,
            occupant=OccupantInfoDTO(primary.full_name, primary.phone, primary.nationality) if primary else None,
            special_requests=booking.special_requests,
            estimated_arrival_time=booking.estimated_arrival_time,
            special_requests_notice=SPECIAL_REQUEST_NOTICE if booking.special_requests else None,
            hold_expires_at=to_vn(booking.hold_expires_at) if booking.hold_expires_at else None,
            hold_remaining_seconds=remaining, policy=booking.policy_snapshot, created_at=booking.created_at)

    @staticmethod
    def _line(item) -> QuoteLineDTO:
        nights = tuple(NightPriceDTO(
            stay_date=n.stay_date, rate_type=n.rate_type_applied, unit_price=n.unit_price, quantity=n.quantity,
            night_total=n.night_total, night_discount=n.night_discount, source_room_rate_id=n.source_room_rate_id)
            for n in item.night_rates)
        return QuoteLineDTO(
            room_type_id=item.room_type_id, room_type_code=item.room_type.room_type_code,
            quantity=item.quantity, adults=item.adults, children=item.children, nights=nights,
            line_subtotal=Decimal(item.line_subtotal), line_discount=Decimal(item.line_discount),
            line_total=Decimal(item.line_total))
