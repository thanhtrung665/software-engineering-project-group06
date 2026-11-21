"""UC Process payment: PaymentService + RefundService (tầng Business).

Bảng PAYMENT/REFUND chỉ có trong schema MySQL 40 bảng nên ở đây thay PaymentRepository bằng bản giả trong bộ nhớ;
booking, giữ phòng, khuyến mãi vẫn chạy thật trên SQLite. Cổng VNPay được thay bằng bản giả (không gọi mạng).
"""
import hashlib
import hmac
from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.business.dto import CreateBookingCommand, RoomSelectionDTO
from app.business.exceptions import NotFoundError, PaymentGatewayUnavailable, PaymentRejected
from app.business.services import (BookingHoldService, HoldConfirmationService, HoldExpiryService, PaymentService,
                                   RefundService)
from app.data_access.gateways.vnpay_gateway import VnpayGateway, _canonical
from app.data_access.models import Booking, BookingStatusHistory, PromotionRedemption
from app.data_access.repositories import PaymentRecord, PendingRefund
from app.data_access.unit_of_work import UnitOfWork
from tests.support import CHECK_IN, CHECK_OUT, add_promo, make_world

SECRET, TMN = "unit-test-secret", "HOTEL01"


# ------------------------------------------------------------------ test doubles
class FakePaymentStore:
    def __init__(self):
        self.payments: dict[str, dict] = {}
        self.refunds: list[dict] = []


class FakePaymentRepository:
    def __init__(self, session, store: FakePaymentStore):
        self.session, self.store = session, store

    def add_pending_online_payment(self, *, booking_id, reference, method, purpose, amount, now):
        code = self.session.get(Booking, booking_id).booking_code
        self.store.payments[reference] = dict(payment_id=len(self.store.payments) + 1, booking_id=booking_id,
                                              booking_code=code, amount=Decimal(amount), payment_status="PENDING",
                                              method=method, purpose=purpose, txn=None, paid_at=None)

    def get_by_reference_for_update(self, reference):
        p = self.store.payments.get(reference)
        return PaymentRecord(p["payment_id"], p["booking_id"], p["booking_code"], p["amount"],
                             p["payment_status"]) if p else None

    def _by_id(self, payment_id):
        return next(p for p in self.store.payments.values() if p["payment_id"] == payment_id)

    def mark_success(self, payment_id, transaction_no, now):
        self._by_id(payment_id).update(payment_status="SUCCESS", txn=transaction_no, paid_at=now)

    def mark_failed(self, payment_id, transaction_no):
        self._by_id(payment_id).update(payment_status="FAILED", txn=transaction_no)

    def add_pending_refund(self, **fields):
        self.store.refunds.append({**fields, "refund_id": len(self.store.refunds) + 1, "status": "PENDING"})

    def list_pending_gateway_refunds(self, booking_code, method):
        out = []
        for r in self.store.refunds:
            p = self._by_id(r["payment_id"])
            if r["status"] == "PENDING" and p["booking_code"] == booking_code and p["payment_status"] == "SUCCESS":
                out.append(PendingRefund(r["refund_id"], r["amount"], r["reference"], next(
                    ref for ref, x in self.store.payments.items() if x is p), p["txn"], p["paid_at"]))
        return out

    def finish_refund(self, refund_id, *, succeeded, gateway_refund_id, now):
        r = self.store.refunds[refund_id - 1]
        if r["status"] != "PENDING":
            return False
        r.update(status="SUCCESS" if succeeded else "FAILED", gateway_refund_id=gateway_refund_id)
        return True


class FakeGateway(VnpayGateway):
    def __init__(self, configured=True, refund_code="00"):
        super().__init__({"VNPAY_TMN_CODE": TMN, "VNPAY_HASH_SECRET": SECRET} if configured else {})
        self.refund_calls, self._refund_code = [], refund_code

    def refund(self, **kw):
        self.refund_calls.append(kw)
        return {"vnp_ResponseCode": self._refund_code, "vnp_TransactionNo": f"R{len(self.refund_calls)}"}


def signed(**params) -> dict:
    data = {"vnp_TmnCode": TMN, "vnp_ResponseCode": "00", "vnp_TransactionStatus": "00",
            "vnp_TransactionNo": "14000001", **params}
    data["vnp_SecureHash"] = hmac.new(SECRET.encode(), _canonical(data).encode(), hashlib.sha512).hexdigest()
    return data


@pytest.fixture()
def env():
    world = make_world()
    store = FakePaymentStore()

    class PayUoW(UnitOfWork):
        def __enter__(self):
            super().__enter__()
            self.payments = FakePaymentRepository(self.session, store)
            return self

    world.uow_factory = lambda: PayUoW(world.session_factory)
    gateway = FakeGateway()
    refunds = RefundService(world.uow_factory, world.clock, gateway)
    payments = PaymentService(world.uow_factory, world.clock, gateway, HoldConfirmationService(world.clock), refunds)
    holds = BookingHoldService(world.uow_factory, world.clock)
    return world, store, gateway, payments, holds


def book(holds, account=2, quantity=1, promo=None):
    return holds.create_booking(account, CreateBookingCommand(
        CHECK_IN, CHECK_OUT, (RoomSelectionDTO(1, quantity, 2),), Decimal(20), True, promo)).booking_code


def booking(world, code) -> Booking:
    with world.session_factory() as s:
        return s.query(Booking).filter_by(booking_code=code).one()


def pay(payments, account, code):
    checkout = payments.create_vnpay_checkout(account, code, "10.0.0.1")
    return checkout, signed(vnp_TxnRef=checkout.payment_reference, vnp_Amount=str(checkout.amount * 100))


# ------------------------------------------------------------------ tạo giao dịch
def test_checkout_records_pending_deposit_and_signed_url(env):
    world, store, gateway, payments, holds = env
    code = book(holds)
    checkout = payments.create_vnpay_checkout(2, code, "10.0.0.1")
    assert checkout.amount == 720_000 and checkout.currency == "VND"
    assert checkout.payment_reference.startswith("VNP-")
    assert "vnp_Amount=72000000" in checkout.payment_url and "vnp_SecureHash=" in checkout.payment_url
    assert store.payments[checkout.payment_reference]["payment_status"] == "PENDING"
    with pytest.raises(NotFoundError):
        payments.create_vnpay_checkout(3, code, "10.0.0.1")           # không phải chủ booking


def test_checkout_fails_fast_when_gateway_not_configured(env):
    world, store, _, _, holds = env
    svc = PaymentService(world.uow_factory, world.clock, FakeGateway(configured=False),
                         HoldConfirmationService(world.clock), RefundService(world.uow_factory, world.clock,
                                                                             FakeGateway(configured=False)))
    with pytest.raises(PaymentGatewayUnavailable):
        svc.create_vnpay_checkout(2, book(holds), "10.0.0.1")
    assert store.payments == {}                                          # không ghi PAYMENT thừa


# ------------------------------------------------------------------ callback
def test_paid_within_hold_confirms_booking_and_updates_money(env):
    world, store, _, payments, holds = env
    add_promo(world)
    code = book(holds, promo="SALE10")
    _, callback = pay(payments, 2, code)
    result = payments.handle_vnpay_return(callback)
    assert (result.status, result.outcome, result.refund_queued) == ("SUCCESS", "CONFIRMED", False)
    b = booking(world, code)
    assert b.booking_status == "CONFIRMED" and b.payment_status == "DEPOSIT_PAID"
    assert b.paid_amount == b.deposit_amount and b.remaining_amount == b.total_amount - b.deposit_amount
    assert b.hold_expires_at is None
    with world.session_factory() as s:
        last = s.query(BookingStatusHistory).order_by(BookingStatusHistory.booking_status_history_id.desc()).first()
        assert (last.new_status, last.changed_source) == ("CONFIRMED", "PAYMENT_GATEWAY")
        assert s.query(PromotionRedemption).one().redemption_status == "CONSUMED"
    again = payments.handle_vnpay_return(callback)                        # callback lặp lại
    assert again.idempotent and booking(world, code).paid_amount == b.paid_amount


def test_rejects_bad_signature_wrong_amount_and_merchant(env):
    world, store, _, payments, holds = env
    code = book(holds)
    checkout, callback = pay(payments, 2, code)
    with pytest.raises(PaymentRejected, match="signature"):
        payments.handle_vnpay_return({**callback, "vnp_Amount": "1"})    # sửa số tiền sau khi ký
    with pytest.raises(PaymentRejected, match="amount"):
        payments.handle_vnpay_return(signed(vnp_TxnRef=checkout.payment_reference, vnp_Amount="100"))
    with pytest.raises(PaymentRejected, match="merchant"):
        payments.handle_vnpay_return(signed(vnp_TxnRef=checkout.payment_reference, vnp_TmnCode="OTHER",
                                            vnp_Amount=str(checkout.amount * 100)))
    with pytest.raises(NotFoundError):
        payments.handle_vnpay_return(signed(vnp_TxnRef="VNP-UNKNOWN", vnp_Amount="100"))
    assert booking(world, code).booking_status == "PENDING_PAYMENT"
    assert store.payments[checkout.payment_reference]["payment_status"] == "PENDING"


def test_failed_payment_keeps_booking_pending(env):
    world, store, _, payments, holds = env
    code = book(holds)
    checkout = payments.create_vnpay_checkout(2, code, "10.0.0.1")
    result = payments.handle_vnpay_return(signed(vnp_TxnRef=checkout.payment_reference, vnp_ResponseCode="24",
                                                 vnp_Amount=str(checkout.amount * 100)))
    assert result.status == "FAILED"
    assert store.payments[checkout.payment_reference]["payment_status"] == "FAILED"
    assert booking(world, code).booking_status == "PENDING_PAYMENT"


def test_late_payment_restores_booking_when_rooms_still_free(env):
    world, _, gateway, payments, holds = env
    code = book(holds)
    _, callback = pay(payments, 2, code)
    world.clock.advance(minutes=20)                                     # quá 15 phút giữ phòng
    result = payments.handle_vnpay_return(callback)
    assert result.outcome == "RESTORED" and not result.refund_queued and gateway.refund_calls == []
    assert booking(world, code).booking_status == "CONFIRMED"


def test_late_payment_when_rooms_taken_is_refunded_in_full(env):
    world, store, gateway, payments, holds = env
    code = book(holds, quantity=2)
    _, callback = pay(payments, 2, code)
    world.clock.advance(minutes=16)
    HoldExpiryService(world.uow_factory, world.clock).expire_overdue_holds()
    book(holds, account=3, quantity=2)                                  # người khác lấy hết phòng
    result = payments.handle_vnpay_return(callback)
    assert (result.outcome, result.refund_queued) == ("REFUND_REQUIRED", True)
    assert result.refund_result.processed == 1 and len(gateway.refund_calls) == 1
    assert gateway.refund_calls[0]["amount_vnd"] == int(booking(world, code).deposit_amount)
    assert store.refunds[0]["refund_type"] == "FULL" and store.refunds[0]["status"] == "SUCCESS"
    assert booking(world, code).booking_status == "PAYMENT_EXPIRED"


def test_second_payment_for_confirmed_booking_is_refunded(env):
    world, store, _, payments, holds = env
    code = book(holds)
    _, first = pay(payments, 2, code)
    checkout2 = payments.create_vnpay_checkout(2, code, "10.0.0.1")    # mở 2 tab thanh toán
    payments.handle_vnpay_return(first)
    result = payments.handle_vnpay_return(signed(vnp_TxnRef=checkout2.payment_reference,
                                                 vnp_TransactionNo="14000002",
                                                 vnp_Amount=str(checkout2.amount * 100)))
    assert (result.outcome, result.refund_queued) == ("ALREADY_CONFIRMED", True)
    assert "Duplicate" in store.refunds[0]["reason"]
    assert booking(world, code).paid_amount == booking(world, code).deposit_amount   # không cộng 2 lần


def test_refunds_skipped_without_credentials_and_failed_refund_reported(env):
    world, store, _, _, holds = env
    assert RefundService(world.uow_factory, world.clock, FakeGateway(configured=False)) \
        .process_pending_gateway_refunds("X").reason == "VNPay merchant credentials not configured"
    code = book(holds)
    gateway = FakeGateway(refund_code="94")
    refunds = RefundService(world.uow_factory, world.clock, gateway)
    payments = PaymentService(world.uow_factory, world.clock, gateway, HoldConfirmationService(world.clock), refunds)
    _, first = pay(payments, 2, code)
    checkout2 = payments.create_vnpay_checkout(2, code, "10.0.0.1")
    payments.handle_vnpay_return(first)
    result = payments.handle_vnpay_return(signed(vnp_TxnRef=checkout2.payment_reference, vnp_TransactionNo="2",
                                                 vnp_Amount=str(checkout2.amount * 100)))
    assert result.refund_result.processed == 0
    assert result.refund_result.errors == ({"refund_id": 1, "response_code": "94"},)
    assert store.refunds[0]["status"] == "FAILED"


# ------------------------------------------------------------------ API (mã HTTP)
def test_payment_api_error_codes(env, monkeypatch):
    from app.composition import get_payment_service
    from app.main import app
    world, _, _, payments, holds = env
    app.dependency_overrides[get_payment_service] = lambda: payments
    try:
        client = TestClient(app)
        r = client.get("/api/v1/payments/vnpay/return", params={"vnp_TxnRef": "X", "vnp_SecureHash": "bad"})
        assert r.status_code == 400 and r.json()["code"] == "PAYMENT_REJECTED"
        code = book(holds)
        r = client.post(f"/api/v1/payments/vnpay/{code}/create", headers={"X-Account-Id": "2"})
        assert r.status_code == 200 and r.json()["amount"] == 720_000
        unconfigured = PaymentService(world.uow_factory, world.clock, FakeGateway(configured=False),
                                      HoldConfirmationService(world.clock), None)
        app.dependency_overrides[get_payment_service] = lambda: unconfigured
        r = client.post(f"/api/v1/payments/vnpay/{code}/create", headers={"X-Account-Id": "2"})
        assert r.status_code == 503 and r.json()["code"] == "PAYMENT_GATEWAY_UNAVAILABLE"
    finally:
        app.dependency_overrides.clear()
