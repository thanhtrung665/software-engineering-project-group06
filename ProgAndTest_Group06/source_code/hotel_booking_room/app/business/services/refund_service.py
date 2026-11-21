"""Thực hiện các khoản hoàn tiền PENDING qua cổng thanh toán (sau khi transaction no-show / thanh toán trễ đã commit).

Mỗi khoản hoàn: gọi cổng (ngoài transaction DB) rồi ghi kết quả trong 1 transaction ngắn, chỉ cập nhật khi
refund còn PENDING nên chạy lặp lại không bị hoàn 2 lần.
"""
from typing import Callable

from app.business.clock import Clock
from app.business.dto import RefundBatchResultDTO
from app.data_access.gateways.vnpay_gateway import GatewayNotConfigured, GatewayResponseError, VnpayGateway
from app.data_access.unit_of_work import UnitOfWork, run_in_transaction

GATEWAY_METHOD = "VNPAY"


class RefundService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork], clock: Clock, gateway: VnpayGateway) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._gateway = gateway

    def process_pending_gateway_refunds(self, booking_code: str) -> RefundBatchResultDTO:
        if not self._gateway.merchant_code:
            return RefundBatchResultDTO(processed=0, reason="VNPay merchant credentials not configured")
        pending = run_in_transaction(
            self._uow_factory, lambda uow: uow.payments.list_pending_gateway_refunds(booking_code, GATEWAY_METHOD),
            readonly=True)
        processed, errors = 0, []
        for refund in pending:
            request_id = ("RF" + "".join(ch for ch in refund.refund_reference if ch.isalnum()))[:20]
            try:
                result = self._gateway.refund(
                    request_id=request_id, txn_ref=refund.payment_reference,
                    amount_vnd=int(refund.refund_amount), transaction_no=refund.gateway_transaction_id,
                    transaction_date=refund.paid_at, order_info="Hotel booking refund")
            except (GatewayResponseError, GatewayNotConfigured) as exc:
                errors.append({"refund_id": refund.refund_id, "error": str(exc)})
                continue
            ok = result.get("vnp_ResponseCode") == "00"
            gateway_id = str(result.get("vnp_TransactionNo") or request_id)
            run_in_transaction(self._uow_factory, lambda uow, r=refund: uow.payments.finish_refund(
                r.refund_id, succeeded=ok, gateway_refund_id=gateway_id, now=self._clock.now()))
            if ok:
                processed += 1
            else:
                errors.append({"refund_id": refund.refund_id, "response_code": result.get("vnp_ResponseCode")})
        return RefundBatchResultDTO(processed=processed, errors=tuple(errors))
