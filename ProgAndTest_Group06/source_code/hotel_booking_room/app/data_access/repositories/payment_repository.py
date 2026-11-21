"""PAYMENT / REFUND (schema 40 bảng, sql/00_schema_40_tables.sql).

Hai bảng này chưa có ORM model riêng nên dùng SQL tham số hóa trên CÙNG session của UnitOfWork
(cùng transaction với booking). Chỉ truy cập dữ liệu, không có quy tắc nghiệp vụ, không commit.
Thời gian truyền vào từ Clock của tầng Business (UTC, giống mọi bảng khác).
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class PaymentRecord:
    payment_id: int
    booking_id: int
    booking_code: str
    amount: Decimal
    payment_status: str


@dataclass(frozen=True)
class PendingRefund:
    refund_id: int
    refund_amount: Decimal
    refund_reference: str
    payment_reference: str
    gateway_transaction_id: str
    paid_at: datetime | None


class PaymentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ---- payment
    def add_pending_online_payment(self, *, booking_id: int, reference: str, method: str, purpose: str,
                                   amount: int, now: datetime) -> None:
        self.session.execute(text(
            "INSERT INTO payment (booking_id, payment_reference, gateway_transaction_id, payment_channel,"
            " payment_method, payment_purpose, amount, payment_status, gateway_signature_valid, created_at)"
            " VALUES (:bid, :ref, 'PENDING', 'ONLINE', :method, :purpose, :amount, 'PENDING', NULL, :now)"),
            {"bid": booking_id, "ref": reference, "method": method, "purpose": purpose, "amount": amount,
             "now": now})

    def get_by_reference_for_update(self, reference: str) -> PaymentRecord | None:
        row = self.session.execute(text(
            "SELECT p.payment_id, p.booking_id, b.booking_code, p.amount, p.payment_status"
            " FROM payment p JOIN booking b ON b.booking_id = p.booking_id"
            " WHERE p.payment_reference = :ref FOR UPDATE"), {"ref": reference}).mappings().first()
        return PaymentRecord(**row) if row else None

    def mark_success(self, payment_id: int, transaction_no: str, now: datetime) -> None:
        self.session.execute(text(
            "UPDATE payment SET payment_status = 'SUCCESS', gateway_transaction_id = :txn,"
            " gateway_signature_valid = 1, paid_at = :now WHERE payment_id = :id"),
            {"txn": transaction_no, "now": now, "id": payment_id})

    def mark_failed(self, payment_id: int, transaction_no: str) -> None:
        self.session.execute(text(
            "UPDATE payment SET payment_status = 'FAILED', gateway_transaction_id = :txn,"
            " gateway_signature_valid = 1 WHERE payment_id = :id"), {"txn": transaction_no, "id": payment_id})

    # ---- refund
    def add_pending_refund(self, *, booking_id: int, payment_id: int, reference: str, amount: Decimal,
                           reason: str, refund_type: str, channel: str, now: datetime) -> None:
        self.session.execute(text(
            "INSERT INTO refund (booking_id, payment_id, refund_reference, refund_amount, cancellation_fee,"
            " refund_reason, refund_type, refund_channel, refund_status, gateway_refund_id, requested_at)"
            " VALUES (:bid, :pid, :ref, :amount, 0, :reason, :type, :channel, 'PENDING', :ref, :now)"),
            {"bid": booking_id, "pid": payment_id, "ref": reference, "amount": amount, "reason": reason,
             "type": refund_type, "channel": channel, "now": now})

    def list_pending_gateway_refunds(self, booking_code: str, method: str) -> list[PendingRefund]:
        rows = self.session.execute(text(
            "SELECT r.refund_id, r.refund_amount, r.refund_reference, p.payment_reference,"
            " p.gateway_transaction_id, p.paid_at"
            " FROM refund r JOIN payment p ON p.payment_id = r.payment_id"
            " JOIN booking b ON b.booking_id = r.booking_id"
            " WHERE b.booking_code = :code AND r.refund_status = 'PENDING'"
            " AND p.payment_method = :method AND p.payment_status = 'SUCCESS'"
            " ORDER BY r.refund_id"), {"code": booking_code, "method": method}).mappings().all()
        return [PendingRefund(**r) for r in rows]

    def finish_refund(self, refund_id: int, *, succeeded: bool, gateway_refund_id: str, now: datetime) -> bool:
        """Chỉ cập nhật refund còn PENDING (an toàn khi chạy lặp). Trả về True nếu có cập nhật."""
        result = self.session.execute(text(
            "UPDATE refund SET refund_status = :status, gateway_refund_id = :gid,"
            " completed_at = CASE WHEN :ok = 1 THEN :now ELSE completed_at END"
            " WHERE refund_id = :id AND refund_status = 'PENDING'"),
            {"status": "SUCCESS" if succeeded else "FAILED", "gid": gateway_refund_id,
             "ok": 1 if succeeded else 0, "now": now, "id": refund_id})
        return result.rowcount == 1
