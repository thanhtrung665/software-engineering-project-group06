"""Kiểm tra cơ chế khóa SELECT ... FOR UPDATE (RBLQH03, RBLQH18) và hạ tầng liên quan."""
import time
from decimal import Decimal

from sqlalchemy import event, select
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.business.dto import CreateBookingCommand, RoomSelectionDTO
from app.business.scheduling import HoldExpiryScheduler
from app.business.services import BookingHoldService, HoldExpiryService
from app.data_access.locking import for_update
from app.data_access.models import Base, RoomType
from tests.support import CHECK_IN, CHECK_OUT, make_world


def test_lock_statement_is_select_for_update():
    stmt = for_update(select(RoomType).where(RoomType.room_type_id == 1), RoomType)
    assert str(stmt.compile(dialect=mysql.dialect())).rstrip().endswith("FOR UPDATE")


def test_room_types_locked_in_ascending_id_order():
    world = make_world()
    seen = []

    @event.listens_for(world.engine, "before_cursor_execute")
    def spy(conn, cursor, statement, params, context, executemany):
        if "FROM room_type" in statement:
            seen.append(params[0])

    with world.uow_factory() as uow:
        uow.room_types.lock_for_update([2, 1, 2])
    assert seen == [1, 2]


def test_booking_locks_before_reading_availability():
    """Thứ tự trong 1 transaction: khóa ROOM_TYPE -> rồi mới đọc số phòng đã giữ -> rồi mới INSERT."""
    world = make_world()
    log = []

    @event.listens_for(world.engine, "before_cursor_execute")
    def spy(conn, cursor, statement, params, context, executemany):
        s = " ".join(statement.split())
        if s.startswith("SELECT") and "FROM room_type" in s and "WHERE room_type.room_type_id = ?" in s:
            log.append("lock")
        elif "FROM booking_item JOIN booking" in s:
            log.append("read_booked")
        elif s.startswith("INSERT INTO booking "):
            log.append("insert_booking")

    BookingHoldService(world.uow_factory, world.clock).create_booking(
        2, CreateBookingCommand(CHECK_IN, CHECK_OUT, (RoomSelectionDTO(1, 1, 2), RoomSelectionDTO(2, 1, 1)),
                                Decimal(20), True))
    assert log.index("lock") < log.index("read_booked") < log.index("insert_booking")
    assert log.count("lock") >= 2                         # đã khóa cả 2 loại phòng


def test_all_tables_have_valid_mysql_ddl():
    d = mysql.dialect()
    for t in Base.metadata.sorted_tables:
        CreateTable(t).compile(dialect=d)
        for i in t.indexes:
            CreateIndex(i).compile(dialect=d)


def test_scheduler_releases_expired_holds_in_background(tmp_path):
    # SQLite file: mỗi luồng 1 kết nối riêng. Với in-memory/StaticPool, test và scheduler dùng CHUNG 1 kết nối
    # nên test có thể đọc thấy thay đổi chưa commit của scheduler (test chập chờn).
    from tests.support import sqlite_file_engine
    world = make_world(sqlite_file_engine(tmp_path / "scheduler.db"))
    BookingHoldService(world.uow_factory, world.clock).create_booking(
        2, CreateBookingCommand(CHECK_IN, CHECK_OUT, (RoomSelectionDTO(1, 1, 2),), Decimal(20), True))
    world.clock.advance(minutes=16)
    sched = HoldExpiryScheduler(HoldExpiryService(world.uow_factory, world.clock), interval_seconds=0.05)
    sched.start()
    try:
        deadline = time.time() + 5
        while time.time() < deadline:
            with world.session_factory() as s:
                from app.data_access.models import Booking
                if s.scalar(select(Booking.booking_status)) == "PAYMENT_EXPIRED":
                    break
            time.sleep(0.05)
    finally:
        sched.stop()
    with world.session_factory() as s:
        assert s.scalar(select(Booking.booking_status)) == "PAYMENT_EXPIRED"
