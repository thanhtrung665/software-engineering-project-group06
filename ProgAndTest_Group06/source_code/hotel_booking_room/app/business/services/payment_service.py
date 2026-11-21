"""UC Process payment – thanh toán tiền cọc online qua VNPay.

1. create_vnpay_checkout : khóa booking, tính số tiền cọc còn thiếu, ghi PAYMENT PENDING, trả URL thanh toán.
2. handle_vnpay_return   : chỉ đổi dữ liệu SAU KHI chữ ký VNPay hợp lệ; trong CÙNG 1 transaction:
     ghi PAYMENT SUCCESS -> HoldConfirmationService quyết định booking (giữ phòng 15 phút / thanh toán trễ)
       CONFIRMED / RESTORED  -> cộng paid_amount, tính remaining_amount & payment_status (RBLQH22, RBLQH29)
       ALREADY_CONFIRMED     -> callback/khoản thanh toán trùng: hoàn lại khoản thừa (RBLQH21c)
       REFUND_REQUIRED       -> thanh toán trễ không giữ được phòng: hoàn 100% (RBLQH21 a/b)
   Sau commit mới gọi cổng để hoàn tiền (không giữ khóa DB trong lúc gọi mạng).
"""
import uuid
from decimal import Decimal
from typing import Callable

from app.business.clock import Clock
from app.business.dto import PaymentCallbackResultDTO, PaymentCheckoutDTO
from app.business.exceptions import (ConflictError, InvalidStateTransition, NotFoundError, PaymentGatewayUnavailable,
                                     PaymentRejected)
from app.business.services.hold_confirmation_service import ConfirmationOutcome, HoldConfirmationService
from app.business.services.refund_service import GATEWAY_METHOD, RefundService
from app.core.enums import BookingStatus, PaymentStatus
from app.data_access.gateways.vnpay_gateway import GatewayNotConfigured, VnpayGateway
from app.data_access.unit_of_work import UnitOfWork, run_in_transaction

_REFUND_REASON = {
    ConfirmationOutcome.REFUND_REQUIRED: "Late payment after room hold expired",
    ConfirmationOutcome.ALREADY_CONFIRMED: "Duplicate successful payment; excess amount refunded",
}


class PaymentService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork], clock: Clock, gateway: VnpayGateway,
                 confirmation: HoldConfirmationService, refunds: RefundService) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._gateway = gateway
        self._confirmation = confirmation
        self._refunds = refunds

    # ------------------------------------------------------------------ tạo giao dịch
    def create_vnpay_checkout(self, account_id: int, booking_code: str, client_ip: str) -> PaymentCheckoutDTO:
        if not self._gateway.merchant_code:          # kiểm tra trước để không ghi PAYMENT thừa
            raise PaymentGatewayUnavailable("VNPAY_TMN_CODE is not configured")
        reference = "VNP-" + uuid.uuid4().hex[:18].upper()

        def work(uow: UnitOfWork) -> int:
            probe = uow.bookings.get_by_code(booking_code)
            if probe is None or probe.account_id != account_id:
                raise NotFoundError("Booking not found")
            booking = uow.bookings.get_for_update(probe.booking_id)
            if booking.booking_status != BookingStatus.PENDING_PAYMENT:
                raise InvalidStateTransition("Booking is not awaiting payment")
            amount = max(0, int(booking.deposit_amount) - int(booking.paid_amount))
            if amount <= 0:
                raise ConflictError("No deposit amount is due")
            uow.payments.add_pending_online_payment(booking_id=booking.booking_id, reference=reference,
                                                    method=GATEWAY_METHOD, purpose="DEPOSIT", amount=amount,
                                                    now=self._clock.now())
            return amount

        amount = run_in_transaction(self._uow_factory, work)
        try:
            url = self._gateway.build_payment_url(txn_ref=reference, amount_vnd=amount,
                                                  order_info=f"Hotel booking {booking_code}", client_ip=client_ip)
        except GatewayNotConfigured as exc:
            raise PaymentGatewayUnavailable(str(exc)) from exc
        return PaymentCheckoutDTO(payment_reference=reference, amount=amount, currency="VND", payment_url=url)

    # ------------------------------------------------------------------ callback
    def handle_vnpay_return(self, params: dict) -> PaymentCallbackResultDTO:
        try:
            valid = self._gateway.verify_callback(params)
        except GatewayNotConfigured as exc:
            raise PaymentGatewayUnavailable(str(exc)) from exc
        if not valid:
            raise PaymentRejected("Invalid VNPay signature")
        reference, transaction_no = params.get("vnp_TxnRef"), params.get("vnp_TransactionNo")
        if not reference or not transaction_no:
            raise PaymentRejected("Missing transaction reference")
        paid_ok = params.get("vnp_ResponseCode") == "00" and params.get("vnp_TransactionStatus", "00") == "00"

        def work(uow: UnitOfWork) -> tuple[PaymentCallbackResultDTO, str | None]:
            payment = uow.payments.get_by_reference_for_update(reference)
            if payment is None:
                raise NotFoundError("Payment reference not found")
            if payment.payment_status == "SUCCESS":
                return PaymentCallbackResultDTO("SUCCESS", reference, idempotent=True), None
            if params.get("vnp_TmnCode") != self._gateway.merchant_code:
                raise PaymentRejected("Unexpected VNPay merchant code")
            try:
                callback_amount = int(params.get("vnp_Amount", "-1"))
            except (TypeError, ValueError):
                raise PaymentRejected("Invalid VNPay amount") from None
            if callback_amount != int(payment.amount) * 100:
                raise PaymentRejected("VNPay amount does not match the payment record")
            if not paid_ok:
                uow.payments.mark_failed(payment.payment_id, transaction_no)
                return PaymentCallbackResultDTO("FAILED", reference), None

            now = self._clock.now()
            uow.payments.mark_success(payment.payment_id, transaction_no, now)
            outcome = self._confirmation.confirm_paid_booking(uow, payment.booking_code)
            if outcome in (ConfirmationOutcome.CONFIRMED, ConfirmationOutcome.RESTORED):
                self._apply_payment(uow, payment.booking_code, payment.amount)
                return PaymentCallbackResultDTO("SUCCESS", reference, outcome=outcome), None
            uow.payments.add_pending_refund(
                booking_id=payment.booking_id, payment_id=payment.payment_id, reference=f"AUTO-{reference}",
                amount=payment.amount, reason=_REFUND_REASON[outcome], refund_type="FULL",
                channel=GATEWAY_METHOD, now=now)
            return (PaymentCallbackResultDTO("SUCCESS", reference, outcome=outcome, refund_queued=True),
                    payment.booking_code)

        result, refund_booking_code = run_in_transaction(self._uow_factory, work)
        if refund_booking_code:
            refund = self._refunds.process_pending_gateway_refunds(refund_booking_code)
            result = PaymentCallbackResultDTO(result.status, reference, outcome=result.outcome,
                                              refund_queued=True, refund_result=refund)
        return result

    @staticmethod
    def _apply_payment(uow: UnitOfWork, booking_code: str, amount: Decimal) -> None:
        """RBLQH22: paid_amount = tổng thanh toán thành công; RBLQH29: payment_status theo số còn lại."""
        booking = uow.bookings.get_by_code(booking_code)       # cùng session: đúng đối tượng đã khóa
        booking.paid_amount = booking.paid_amount + Decimal(amount)
        booking.remaining_amount = max(Decimal(0), booking.total_amount - booking.paid_amount)
        booking.payment_status = (PaymentStatus.FULLY_PAID if booking.remaining_amount == 0
                                  else PaymentStatus.DEPOSIT_PAID)
        booking.hold_expires_at = None
