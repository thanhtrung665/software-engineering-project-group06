"""Chặn lỗi chỉ xuất hiện trên MySQL (test chạy SQLite nên không tự phát hiện được).

Ví dụ: `col.is_(True)` trên MySQL sinh `col IS 1` – SQLite chấp nhận, MySQL báo lỗi cú pháp.
Test chạy một vòng nghiệp vụ đầy đủ, bắt MỌI câu lệnh SQLAlchemy thực thi, dịch sang cú pháp MySQL rồi kiểm tra.
"""
import re
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.dialects import mysql

from app.business.dto import CreateBookingCommand, QuoteCommand, RoomSelectionDTO
from app.business.services import BookingHoldService, HoldConfirmationService, HoldExpiryService
from app.data_access.unit_of_work import run_in_transaction
from tests.support import CHECK_IN, CHECK_OUT, add_promo, make_world

APP = Path(__file__).resolve().parent.parent / "app"


def _exercise_everything():
    world = make_world()
    captured = []

    @event.listens_for(world.engine, "before_execute")
    def grab(conn, clauseelement, multiparams, params, execution_options):
        captured.append(clauseelement)

    add_promo(world)
    svc = BookingHoldService(world.uow_factory, world.clock)
    rooms = (RoomSelectionDTO(1, 1, 2), RoomSelectionDTO(2, 1, 1))
    svc.quote(2, QuoteCommand(CHECK_IN, CHECK_OUT, rooms, "SALE10", Decimal(20)))
    a = svc.create_booking(2, CreateBookingCommand(CHECK_IN, CHECK_OUT, rooms, Decimal(20), True, "SALE10"))
    b = svc.create_booking(3, CreateBookingCommand(CHECK_IN, CHECK_OUT, rooms[:1], Decimal(50), True))
    svc.get_booking(2, a.booking_code)
    svc.cancel_pending_booking(3, b.booking_code)
    confirm = HoldConfirmationService(world.clock)
    run_in_transaction(world.uow_factory, lambda u: confirm.confirm_paid_booking(u, a.booking_code))
    c = svc.create_booking(4, CreateBookingCommand(CHECK_IN, CHECK_OUT, rooms[:1], Decimal(100), True))
    world.clock.advance(minutes=20)
    HoldExpiryService(world.uow_factory, world.clock).expire_overdue_holds()
    return captured


def _mysql(stmt) -> str:
    d = mysql.dialect()
    try:
        sql = str(stmt.compile(dialect=d, compile_kwargs={"literal_binds": True}))
    except Exception:                                     # kiểu không render được literal (JSON...)
        sql = str(stmt.compile(dialect=d))
    # placeholder %s của PyMySQL sẽ bị sqlglot hiểu nhầm là toán tử % -> thay bằng giá trị giả
    return re.sub(r"%\(\w+\)s|%s", "1", sql)


def test_no_invalid_mysql_boolean_comparison():
    statements = _exercise_everything()
    assert len(statements) > 30
    bad = [s for s in map(_mysql, statements) if re.search(r"\bIS\s+[01]\b", s)]
    assert not bad, "MySQL không có `IS 1`/`IS 0`:\n" + "\n".join(bad[:3])


def test_all_executed_statements_parse_as_mysql():
    sqlglot = pytest.importorskip("sqlglot")
    for stmt in _exercise_everything():
        sql = _mysql(stmt)
        if sql.lstrip().upper().startswith(("SELECT", "UPDATE", "DELETE", "INSERT")):
            sqlglot.parse_one(sql, read="mysql")         # ném lỗi nếu cú pháp MySQL sai


def test_source_never_uses_is_true_false():
    """Ràng buộc cho CẢ NHÓM: dùng `== true()` / `== false()`, không dùng `.is_(True/False)`."""
    offenders = [str(p.relative_to(APP)) for p in APP.rglob("*.py")
                 if re.search(r"\.is_(not)?\(\s*(True|False)\s*\)", p.read_text(encoding="utf-8"))]
    assert not offenders, f"Dùng .is_(True/False) (hỏng trên MySQL): {offenders}"


def test_booking_flow_uses_for_update_on_mysql():
    """Mọi luồng tạo/hết hạn/xác nhận phải thực sự phát ra `FOR UPDATE` khi chạy trên MySQL."""
    sql = " ".join(_mysql(s) for s in _exercise_everything())
    assert sql.count("FOR UPDATE") >= 8


def test_all_tables_compile_for_mysql():
    from sqlalchemy.schema import CreateIndex, CreateTable
    from app.data_access.models import Base
    dialect = mysql.dialect()
    for table in Base.metadata.sorted_tables:
        CreateTable(table).compile(dialect=dialect)
        for index in table.indexes:
            CreateIndex(index).compile(dialect=dialect)


def test_locking_compiles_to_mysql_for_update():
    from sqlalchemy import select
    from app.data_access.locking import for_update
    from app.data_access.models import RoomType
    sql = str(for_update(select(RoomType), RoomType).compile(dialect=mysql.dialect()))
    assert "FOR UPDATE" in sql and "WITH (UPDLOCK" not in sql
