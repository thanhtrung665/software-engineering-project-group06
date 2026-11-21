"""Test tích hợp trên MySQL/InnoDB THẬT (Docker). Mặc định bỏ qua.

Bật:   docker compose up -d   rồi   RUN_MYSQL_TESTS=1 pytest tests/test_mysql_integration.py -v
(PowerShell:  $env:RUN_MYSQL_TESTS=1; pytest tests/test_mysql_integration.py -v)
Test tạo database riêng `hotel_booking_test` (xóa & tạo lại mỗi lần) – KHÔNG đụng dữ liệu thật.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text

from app.business.dto import CreateBookingCommand, RoomSelectionDTO
from app.business.exceptions import RoomSoldOutError
from app.business.services import BookingHoldService, HoldExpiryService
from app.core.config import get_settings
from app.data_access.database import build_engine
from scripts.stress_oversell import run_round
from tests.support import CHECK_IN, CHECK_OUT, make_world

pytestmark = pytest.mark.skipif(os.getenv("RUN_MYSQL_TESTS") != "1",
                                reason="Đặt RUN_MYSQL_TESTS=1 và bật MySQL (docker compose up -d)")
TEST_DB = "hotel_booking_test"


@pytest.fixture(scope="module")
def world():
    s = get_settings()
    server_url = s.database_url.set(
        username="root", password=s.mysql_root_password, database=None
    )
    master = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with master.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS `{TEST_DB}`"))
        c.execute(text(f"CREATE DATABASE `{TEST_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    engine = build_engine(s._url(TEST_DB))
    w = make_world(engine)
    yield w
    engine.dispose()


def test_last_room_race_exactly_capacity_wins(world):
    for _ in range(3):
        r = run_round(world.session_factory, threads=24, room_type_code="DELUXE", days_ahead=400, clock=world.clock)
        assert r.other_errors == [], r.other_errors
        assert r.succeeded == r.capacity == 2 and r.sold_out == 22 and r.available_after == 0


def test_opposite_order_multi_room_type_bookings_do_not_deadlock(world):
    """Luồng A chọn (DELUXE, STANDARD), luồng B chọn (STANDARD, DELUXE): khóa luôn theo id tăng dần."""
    svc = BookingHoldService(world.uow_factory, world.clock)
    a = (RoomSelectionDTO(1, 1, 2), RoomSelectionDTO(2, 1, 1))
    b = (RoomSelectionDTO(2, 1, 1), RoomSelectionDTO(1, 1, 2))
    ci, co = CHECK_IN + timedelta(days=10), CHECK_OUT + timedelta(days=10)

    def go(args):
        account, rooms = args
        try:
            svc.create_booking(account, CreateBookingCommand(ci, co, rooms, Decimal(20), True))
            return "ok"
        except RoomSoldOutError:
            return "sold_out"

    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(go, [(2 + i % 5, a if i % 2 == 0 else b) for i in range(8)]))
    assert set(results) <= {"ok", "sold_out"} and results.count("ok") == 2     # DELUXE chỉ có 2 phòng


def test_expiry_and_new_booking_race_is_safe(world):
    svc = BookingHoldService(world.uow_factory, world.clock)
    cmd = CreateBookingCommand(CHECK_IN + timedelta(days=20), CHECK_OUT + timedelta(days=20),
                               (RoomSelectionDTO(1, 2, 2),), Decimal(20), True)
    svc.create_booking(2, cmd)
    world.clock.advance(minutes=16)
    job = HoldExpiryService(world.uow_factory, world.clock)
    with ThreadPoolExecutor(2) as ex:
        f1 = ex.submit(job.expire_overdue_holds)
        f2 = ex.submit(svc.create_booking, 3, cmd)
        f1.result(); assert f2.result().booking_status == "PENDING_PAYMENT"
