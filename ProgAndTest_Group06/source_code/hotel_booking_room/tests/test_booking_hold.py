"""Cơ chế giữ phòng 15 phút – khớp UC Book room / Process payment / Cancel booking."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.business.dto import CreateBookingCommand, OccupantDTO, QuoteCommand, RoomSelectionDTO
from app.business.exceptions import (InvalidStateTransition, NotFoundError, PermissionDenied, PriceChangedError,
                                     PromotionRejected, RoomSoldOutError, TooManyPendingBookings, ValidationFailed)
from app.business.services import (BookingHoldService, ConfirmationOutcome, HoldConfirmationService,
                                   HoldExpiryService)
from app.data_access.models import (Account, Booking, BookingItem, BookingStatusHistory, HolidayDate, Promotion,
                                    PromotionRedemption, RoomRate, RoomRateHoliday)
from app.data_access.unit_of_work import run_in_transaction
from tests.support import CHECK_IN, CHECK_OUT, add_promo, make_world

DELUXE, STANDARD = 1, 2


@pytest.fixture()
def world():
    return make_world()


@pytest.fixture()
def svc(world):
    return BookingHoldService(world.uow_factory, world.clock)


def cmd(rooms=((DELUXE, 1, 2, 0),), *, ci=CHECK_IN, co=CHECK_OUT, deposit=20, promo=None, **kw):
    return CreateBookingCommand(
        check_in_date=ci, check_out_date=co, rooms=tuple(RoomSelectionDTO(*r) for r in rooms),
        deposit_percentage=Decimal(deposit), accept_terms=True, promo_code=promo, **kw)


def fetch(world, model, *where):
    with world.session_factory() as s:
        return list(s.scalars(select(model).where(*where)))


# ------------------------------------------------------------------ giữ phòng 15 phút
def test_booking_is_pending_and_holds_rooms_for_15_minutes(world, svc):
    b = svc.create_booking(2, cmd())
    assert b.booking_status == "PENDING_PAYMENT" and b.payment_status == "UNPAID"
    assert b.hold_remaining_seconds == 15 * 60
    assert b.hold_expires_at.utcoffset() == timedelta(hours=7)
    assert b.total_amount == 3_600_000 and b.deposit_amount == 720_000 and b.remaining_amount == 3_600_000
    row = fetch(world, Booking)[0]
    assert row.hold_expires_at == world.clock.now() + timedelta(minutes=15)       # lưu UTC
    assert row.booking_code.startswith("HB261120-") and row.policy_snapshot["hold_minutes"] == 15
    hist = fetch(world, BookingStatusHistory)
    assert [(h.old_status, h.new_status, h.changed_source, h.changed_by) for h in hist] == [
        (None, "PENDING_PAYMENT", "USER", 2)]


def test_hold_minutes_comes_from_system_setting(world):
    from app.data_access.models import SystemSetting
    with world.session_factory() as s:
        s.add(SystemSetting(setting_key="HOLD_MINUTES", setting_value=5, updated_by=1))
        s.commit()
    b = BookingHoldService(world.uow_factory, world.clock).create_booking(2, cmd())
    assert b.hold_remaining_seconds == 300


def test_countdown_decreases_on_get(world, svc):
    code = svc.create_booking(2, cmd()).booking_code
    world.clock.advance(minutes=4, seconds=30)
    assert svc.get_booking(2, code).hold_remaining_seconds == 10 * 60 + 30
    with pytest.raises(NotFoundError):
        svc.get_booking(3, code)                         # không xem được booking của người khác


def test_rates_are_snapshotted_per_night_and_priority(world, svc):
    # 3/12 (Thu) có giá HOLIDAY, 4/12 (Fri) giá WEEKEND, 5/12 (Sat) giá SEASON; SEASON > WEEKEND
    with world.session_factory() as s:
        s.add(HolidayDate(holiday_date=date(2026, 12, 3), holiday_name="Lễ", is_active=True))
        s.flush()
        hol = RoomRate(room_type_id=DELUXE, rate_type="HOLIDAY", nightly_price=Decimal(3_000_000), created_by=1)
        season = RoomRate(room_type_id=DELUXE, rate_type="SEASON", start_date=date(2026, 12, 5),
                          end_date=date(2026, 12, 6), nightly_price=Decimal(2_500_000), created_by=1)
        s.add_all([hol, season]); s.flush()
        s.add(RoomRateHoliday(room_rate_id=hol.room_rate_id, holiday_date_id=1))
        s.commit()
    b = svc.create_booking(2, cmd(ci=date(2026, 12, 3), co=date(2026, 12, 6)))
    nights = [(n.stay_date.day, n.rate_type, int(n.unit_price)) for n in b.lines[0].nights]
    assert nights == [(3, "HOLIDAY", 3_000_000), (4, "WEEKEND", 2_200_000), (5, "SEASON", 2_500_000)]
    assert b.total_amount == 7_700_000
    # Đổi giá sau khi đặt không ảnh hưởng booking cũ (RBLQH06)
    with world.session_factory() as s:
        for r in s.scalars(select(RoomRate)):
            r.nightly_price = Decimal(1)
        s.commit()
    assert svc.get_booking(2, b.booking_code).total_amount == 7_700_000


# ------------------------------------------------------------------ chống overselling (A3)
def test_last_room_second_user_gets_sold_out(world, svc):
    svc.create_booking(2, cmd(((DELUXE, 2, 2, 0),)))     # giữ hết 2 phòng DELUXE
    with pytest.raises(RoomSoldOutError) as e:
        svc.create_booking(3, cmd())
    assert e.value.message == ("This room type just sold out for your selected dates. "
                               "Please choose another room type.")
    assert e.value.details == {"room_type_ids": [DELUXE]}
    assert len(fetch(world, Booking)) == 1               # rollback: không có booking dở dang


def test_sold_out_if_any_single_night_is_full(world, svc):
    svc.create_booking(2, cmd(((DELUXE, 2, 2, 0),), ci=date(2026, 12, 2), co=date(2026, 12, 3)))
    with pytest.raises(RoomSoldOutError):                # 1/12–3/12 đụng đêm 2/12 đã hết
        svc.create_booking(3, cmd())
    # Ngày check-out của booking trước (3/12) KHÔNG phải một đêm: đặt 3/12–4/12 vẫn được
    svc.create_booking(3, cmd(ci=date(2026, 12, 3), co=date(2026, 12, 4)))


def test_hold_stops_counting_after_expiry_even_before_job_runs(world, svc):
    svc.create_booking(2, cmd(((DELUXE, 2, 2, 0),)))
    world.clock.advance(minutes=14, seconds=59)
    with pytest.raises(RoomSoldOutError):
        svc.create_booking(3, cmd())
    world.clock.advance(seconds=2)                       # quá 15 phút, job CHƯA chạy
    assert svc.create_booking(3, cmd()).booking_status == "PENDING_PAYMENT"      # RBLQH19


def test_confirmed_and_maintenance_reduce_availability(world, svc):
    from app.data_access.models import RoomMaintenance
    with world.session_factory() as s:
        s.add(RoomMaintenance(room_id=1, start_date=date(2026, 12, 2), end_date=date(2026, 12, 2),
                              reason="sửa điều hòa", maintenance_status="PLANNED", created_by=1))
        s.commit()
    svc.create_booking(2, cmd(((DELUXE, 1, 2, 0),)))     # 2 phòng − 1 bảo trì đêm 2/12 = 1 trống, giờ hết
    with pytest.raises(RoomSoldOutError):
        svc.create_booking(3, cmd())


def test_race_for_last_room_exactly_one_succeeds(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from tests.support import sqlite_file_engine
    world = make_world(sqlite_file_engine(tmp_path / "race.db"))
    svc = BookingHoldService(world.uow_factory, world.clock)
    svc.create_booking(6, cmd(((DELUXE, 1, 2, 0),)))     # còn đúng 1 phòng DELUXE

    def attempt(account_id):
        try:
            return svc.create_booking(account_id, cmd()).booking_code
        except RoomSoldOutError:
            return "SOLD_OUT"

    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(attempt, [2, 3, 4, 5, 2, 3, 4, 5]))
    winners = [r for r in results if r != "SOLD_OUT"]
    assert len(winners) == 1, results                    # "Exactly one booking succeeds" (bảng kiểm NFR)
    with world.session_factory() as s:
        held = s.scalar(select(func.sum(BookingItem.quantity)))
    assert held == 2                                     # không vượt số phòng thật (2)


# ------------------------------------------------------------------ A5 / A6 / validation
def test_max_three_pending_bookings(world, svc):
    for _ in range(3):
        svc.create_booking(2, cmd(((STANDARD, 1, 1, 0),)))
    with pytest.raises(TooManyPendingBookings):
        svc.create_booking(2, cmd(((STANDARD, 1, 1, 0),)))
    svc.create_booking(3, cmd(((DELUXE, 1, 2, 0),)))     # user khác không bị ảnh hưởng
    world.clock.advance(minutes=16)                      # hold của user 2 đã hết hạn -> không còn bị tính
    assert svc.create_booking(2, cmd(((STANDARD, 1, 1, 0),))).booking_status == "PENDING_PAYMENT"


def test_price_change_requires_reconfirmation(world, svc):
    with pytest.raises(PriceChangedError) as e:
        svc.create_booking(2, cmd(expected_total_amount=Decimal(3_000_000)))
    assert e.value.details == {"previous_total_amount": 3_000_000, "new_total_amount": 3_600_000}
    assert fetch(world, Booking) == []                   # chưa tạo booking, chưa giữ phòng
    assert svc.create_booking(2, cmd(expected_total_amount=Decimal(3_600_000))).total_amount == 3_600_000


@pytest.mark.parametrize("kwargs,field", [
    (dict(ci=date(2026, 11, 19), co=date(2026, 11, 21)), "check_in_date"),
    (dict(ci=CHECK_IN, co=CHECK_IN), "check_out_date"),
    (dict(ci=CHECK_IN, co=CHECK_IN + timedelta(days=31)), "check_out_date"),
    (dict(rooms=((DELUXE, 1, 5, 0),)), "rooms"),                    # vượt sức chứa người lớn
    (dict(rooms=((DELUXE, 1, 2, 2),)), "rooms"),                    # vượt sức chứa trẻ em
    (dict(rooms=((DELUXE, 2, 1, 0),)), "adults"),                   # phòng > người lớn
    (dict(rooms=((DELUXE, 3, 3, 0), (STANDARD, 3, 3, 0))), "rooms"),   # > 5 phòng
    (dict(rooms=((DELUXE, 1, 1, 0), (DELUXE, 1, 1, 0))), "rooms"),     # trùng loại phòng
    (dict(deposit=30), "deposit_percentage"),                       # mức cọc không được cấu hình
])
def test_validation_errors_point_to_field(svc, kwargs, field):
    with pytest.raises(ValidationFailed) as e:
        svc.create_booking(2, cmd(**kwargs))
    assert e.value.details["field"] == field


def test_must_accept_terms_and_only_active_customers(world, svc):
    bad = CreateBookingCommand(CHECK_IN, CHECK_OUT, (RoomSelectionDTO(DELUXE, 1, 2),), Decimal(20), False)
    with pytest.raises(ValidationFailed):
        svc.create_booking(2, bad)
    with pytest.raises(PermissionDenied):
        svc.create_booking(1, cmd())                     # tài khoản Manager không đặt phòng online
    with world.session_factory() as s:
        s.get(Account, 3).account_status = "LOCKED"
        s.commit()
    with pytest.raises(PermissionDenied):
        svc.create_booking(3, cmd())


def test_occupant_and_special_requests(world, svc):
    b = svc.create_booking(2, cmd(occupant=OccupantDTO("Nguyen Van B", "0911", "US"),
                                  special_requests="Phòng không hút thuốc", estimated_arrival_time=time(21, 0)))
    assert (b.contact_name, b.contact_email) == ("Khach 2", "k2@h.vn")      # người đặt = tài khoản
    assert (b.occupant.full_name, b.occupant.nationality) == ("Nguyen Van B", "US")
    assert "without guarantee" in b.special_requests_notice
    default = svc.create_booking(3, cmd())
    assert default.occupant.full_name == "Khach 3" and default.special_requests_notice is None


# ------------------------------------------------------------------ khuyến mãi (A2, RBLQH07)
def test_promotion_reserved_then_released_on_expiry(world, svc):
    add_promo(world, max_discount=Decimal(200_000))
    b = svc.create_booking(2, cmd(promo="sale10"))       # không phân biệt hoa/thường
    assert b.discount_amount == 200_000 and b.total_amount == 3_400_000 and b.promo_code == "SALE10"
    assert sum(n.night_discount for n in b.lines[0].nights) == 200_000
    assert fetch(world, Promotion)[0].used_count == 1
    assert fetch(world, PromotionRedemption)[0].redemption_status == "RESERVED"
    world.clock.advance(minutes=16)
    HoldExpiryService(world.uow_factory, world.clock).expire_overdue_holds()
    assert fetch(world, Promotion)[0].used_count == 0
    assert fetch(world, PromotionRedemption)[0].redemption_status == "RELEASED"


def test_promotion_limits_and_reasons(world, svc):
    add_promo(world, "ONCE", per_account_limit=1)
    add_promo(world, "EXPIRED", valid_to=datetime(2026, 6, 1), valid_from=datetime(2026, 1, 1))
    add_promo(world, "PAUSED", promotion_status="PAUSED")
    add_promo(world, "LONGSTAY", min_nights=5)
    add_promo(world, "CAP1", total_usage_limit=1, per_account_limit=5)
    reasons = {}
    for code in ("NOPE", "EXPIRED", "PAUSED", "LONGSTAY"):
        with pytest.raises(PromotionRejected) as e:
            svc.create_booking(2, cmd(((STANDARD, 1, 1, 0),), promo=code))
        reasons[code] = e.value.message
    assert len(set(reasons.values())) == 4               # mỗi trường hợp nêu lý do riêng
    svc.create_booking(2, cmd(((STANDARD, 1, 1, 0),), promo="ONCE"))
    with pytest.raises(PromotionRejected):               # per-account limit
        svc.create_booking(2, cmd(((STANDARD, 1, 1, 0),), promo="ONCE"))
    svc.create_booking(3, cmd(((STANDARD, 1, 1, 0),), promo="CAP1"))
    with pytest.raises(PromotionRejected):               # total limit
        svc.create_booking(4, cmd(((STANDARD, 1, 1, 0),), promo="CAP1"))


def test_promotion_for_specific_room_types_only_discounts_them(world, svc):
    pid = add_promo(world, "DLX", discount_type="FIXED", discount_value=Decimal(500_000))
    with world.session_factory() as s:
        from app.data_access.models import PromotionRoomType
        s.add(PromotionRoomType(promotion_id=pid, room_type_id=DELUXE)); s.commit()
    b = svc.create_booking(2, cmd(((DELUXE, 1, 2, 0), (STANDARD, 1, 1, 0)), promo="DLX"))
    by_code = {l.room_type_code: l for l in b.lines}
    assert by_code["DELUXE"].line_discount == 500_000 and by_code["STANDARD"].line_discount == 0
    assert b.total_amount == b.subtotal_amount - 500_000
    for l in b.lines:                                    # RBLTT04
        assert l.line_total == l.line_subtotal - l.line_discount
        assert sum(n.night_total for n in l.nights) == l.line_subtotal


def test_quote_does_not_hold_rooms(world, svc):
    q = svc.quote(2, QuoteCommand(CHECK_IN, CHECK_OUT, (RoomSelectionDTO(DELUXE, 2, 2),), None, Decimal(50)))
    assert q.total_amount == 7_200_000 and q.deposit_amount == 3_600_000 and q.balance_at_check_in == 3_600_000
    assert [int(o.percentage) for o in q.deposit_options] == [20, 50, 100] and q.vat_included
    assert fetch(world, Booking) == []
    svc.create_booking(3, cmd(((DELUXE, 2, 2, 0),)))     # vẫn còn phòng sau khi quote


# ------------------------------------------------------------------ hết hạn hold (A4)
def test_expiry_job_releases_once_and_records_history(world, svc):
    code = svc.create_booking(2, cmd()).booking_code
    job = HoldExpiryService(world.uow_factory, world.clock)
    assert job.expire_overdue_holds().expired_booking_codes == ()          # chưa tới hạn
    world.clock.advance(minutes=15, seconds=1)
    report = job.expire_overdue_holds()
    assert report.expired_booking_codes == (code,) and report.failed == 0
    assert job.expire_overdue_holds().expired_booking_codes == ()          # idempotent
    b = fetch(world, Booking)[0]
    assert b.booking_status == "PAYMENT_EXPIRED" and b.remaining_amount == 0
    last = fetch(world, BookingStatusHistory)[-1]
    assert (last.old_status, last.new_status, last.changed_source, last.changed_by) == (
        "PENDING_PAYMENT", "PAYMENT_EXPIRED", "SYSTEM_SCHEDULER", None)


def test_expiry_never_touches_paid_booking(world, svc):
    code = svc.create_booking(2, cmd()).booking_code
    confirm = HoldConfirmationService(world.clock)
    run_in_transaction(world.uow_factory, lambda uow: confirm.confirm_paid_booking(uow, code))
    world.clock.advance(hours=1)
    assert HoldExpiryService(world.uow_factory, world.clock).expire_one(1) is None
    assert fetch(world, Booking)[0].booking_status == "CONFIRMED"


# ------------------------------------------------------------------ xác nhận / thanh toán trễ
def confirm_payment(world, code):
    svc = HoldConfirmationService(world.clock)
    return run_in_transaction(world.uow_factory, lambda uow: svc.confirm_paid_booking(uow, code))


def test_payment_within_hold_confirms_and_consumes_promo(world, svc):
    add_promo(world)
    code = svc.create_booking(2, cmd(promo="SALE10")).booking_code
    world.clock.advance(minutes=10)
    assert confirm_payment(world, code) == ConfirmationOutcome.CONFIRMED
    assert fetch(world, Booking)[0].booking_status == "CONFIRMED"
    assert fetch(world, PromotionRedemption)[0].redemption_status == "CONSUMED"
    assert confirm_payment(world, code) == ConfirmationOutcome.ALREADY_CONFIRMED   # callback trùng
    hist = fetch(world, BookingStatusHistory)
    assert [h.new_status for h in hist] == ["PENDING_PAYMENT", "CONFIRMED"] and hist[-1].changed_by is None
    # Đã Confirmed: hold hết hạn cũng KHÔNG nhả phòng (vẫn chiếm chỗ)
    world.clock.advance(hours=1)
    with pytest.raises(RoomSoldOutError):
        svc.create_booking(3, cmd(((DELUXE, 2, 2, 0),)))


def test_late_payment_restores_when_rooms_still_available(world, svc):
    add_promo(world)
    code = svc.create_booking(2, cmd(promo="SALE10")).booking_code
    world.clock.advance(minutes=20)                      # quá hold, job CHƯA chạy
    assert confirm_payment(world, code) == ConfirmationOutcome.RESTORED
    assert fetch(world, Booking)[0].booking_status == "CONFIRMED"
    assert fetch(world, PromotionRedemption)[0].redemption_status == "CONSUMED"
    assert fetch(world, Promotion)[0].used_count == 1
    assert [h.new_status for h in fetch(world, BookingStatusHistory)] == [
        "PENDING_PAYMENT", "PAYMENT_EXPIRED", "CONFIRMED"]


def test_late_payment_requires_refund_when_rooms_taken(world, svc):
    code = svc.create_booking(2, cmd(((DELUXE, 2, 2, 0),))).booking_code
    world.clock.advance(minutes=16)
    HoldExpiryService(world.uow_factory, world.clock).expire_overdue_holds()
    svc.create_booking(3, cmd(((DELUXE, 2, 2, 0),)))     # người khác lấy hết phòng
    assert confirm_payment(world, code) == ConfirmationOutcome.REFUND_REQUIRED
    assert fetch(world, Booking, Booking.booking_code == code)[0].booking_status == "PAYMENT_EXPIRED"


def test_late_payment_after_no_show_cutoff_and_cancelled_need_refund(world, svc):
    code = svc.create_booking(2, cmd()).booking_code
    world.clock.now = lambda: datetime(2026, 12, 1, 23, 0)      # 06:00 ngày 2/12 VN = 23:00 UTC ngày 1/12
    assert confirm_payment(world, code) == ConfirmationOutcome.REFUND_REQUIRED
    w2 = make_world(); s2 = BookingHoldService(w2.uow_factory, w2.clock)
    code2 = s2.create_booking(2, cmd()).booking_code
    s2.cancel_pending_booking(2, code2)
    assert confirm_payment(w2, code2) == ConfirmationOutcome.REFUND_REQUIRED


# ------------------------------------------------------------------ hủy khi Pending (Cancel booking A2)
def test_cancel_pending_releases_rooms_and_promo(world, svc):
    add_promo(world)
    code = svc.create_booking(2, cmd(((DELUXE, 2, 2, 0),), promo="SALE10")).booking_code
    b = svc.cancel_pending_booking(2, code, "đổi kế hoạch")
    assert b.booking_status == "CANCELLED" and b.remaining_amount == 0
    assert fetch(world, Promotion)[0].used_count == 0
    svc.create_booking(3, cmd(((DELUXE, 2, 2, 0),)))     # phòng được nhả ngay
    with pytest.raises(InvalidStateTransition):
        svc.cancel_pending_booking(2, code)              # đã hủy rồi
    with pytest.raises(NotFoundError):
        svc.cancel_pending_booking(4, code)              # không phải chủ booking
    h = fetch(world, BookingStatusHistory, BookingStatusHistory.new_status == "CANCELLED")[0]
    assert (h.changed_source, h.changed_by, h.change_reason) == ("USER", 2, "đổi kế hoạch")


def test_cancel_confirmed_is_not_handled_here(world, svc):
    code = svc.create_booking(2, cmd()).booking_code
    confirm_payment(world, code)
    with pytest.raises(InvalidStateTransition):
        svc.cancel_pending_booking(2, code)
