"""Hạ tầng test cho cơ chế giữ phòng: đồng hồ giả + dữ liệu mẫu."""
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.business.clock import Clock
from app.data_access.models import (Account, Base, DepositLevel, Hotel, Promotion, Role, Room, RoomRate,
                                    RoomType)
from app.data_access.unit_of_work import UnitOfWork

NOW0 = datetime(2026, 11, 20, 3, 0)          # 10:00 giờ Việt Nam
CHECK_IN = date(2026, 12, 1)                  # Thứ Ba
CHECK_OUT = date(2026, 12, 3)                 # 2 đêm: Thứ Ba, Thứ Tư (giá BASE)


class FakeClock(Clock):
    def __init__(self, now: datetime = NOW0) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance(self, **kw) -> None:
        self._now += timedelta(**kw)


class World:
    """DELUXE (id=1, 2 phòng, 1.800.000) · STANDARD (id=2, 3 phòng, 900.000) · khách id 2..6 · quản lý id 1."""

    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory
        self.clock = FakeClock()

    def uow_factory(self):
        return UnitOfWork(self.session_factory)


def make_world(engine=None) -> World:
    if engine is None:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as s:
        s.add_all([Role(role_code="MANAGER", role_name="Manager"), Role(role_code="CUSTOMER", role_name="Customer")])
        s.flush()
        s.add(Account(role_id=1, full_name="Manager", email="m@h.vn", phone="0", account_status="ACTIVE"))
        for i in range(2, 7):
            s.add(Account(role_id=2, full_name=f"Khach {i}", email=f"k{i}@h.vn", phone=f"09000000{i}",
                          nationality="VN", account_status="ACTIVE"))
        s.add(Hotel(star_rating=4, address="HCMC", hotline="1", contact_email="a@b.c"))
        s.flush()
        for code, rooms, price in (("DELUXE", 2, 1_800_000), ("STANDARD", 3, 900_000)):
            rt = RoomType(hotel_id=1, room_type_code=code, area_sqm=Decimal(30), bed_type="KING", max_adults=2,
                          max_children=1, base_price=Decimal(price), selling_status="ON_SALE")
            s.add(rt)
            s.flush()
            s.add(RoomRate(room_type_id=rt.room_type_id, rate_type="BASE", nightly_price=Decimal(price),
                           created_by=1))
            s.add(RoomRate(room_type_id=rt.room_type_id, rate_type="WEEKEND", weekday_no=5,
                           nightly_price=Decimal(price + 400_000), created_by=1))
            for n in range(rooms):
                s.add(Room(room_type_id=rt.room_type_id, room_number=f"{code[0]}{n}", floor_number=2,
                           room_status="VACANT"))
        for pct in (20, 50, 100):
            s.add(DepositLevel(percentage=Decimal(pct), effective_from=datetime(2020, 1, 1), updated_by=1))
        s.commit()
    w = World(factory)
    w.engine = engine
    return w


def add_promo(world: World, code="SALE10", **kw) -> int:
    fields = dict(promo_code=code, discount_type="PERCENT", discount_value=Decimal(10), min_nights=1,
                  min_order_value=Decimal(0), valid_from=datetime(2026, 1, 1), valid_to=datetime(2027, 1, 1),
                  total_usage_limit=None, per_account_limit=1, promotion_status="ACTIVE", created_by=1)
    fields.update(kw)
    with world.session_factory() as s:
        p = Promotion(**fields)
        s.add(p)
        s.commit()
        return p.promotion_id


def sqlite_file_engine(path):
    """SQLite file + BEGIN IMMEDIATE: mô phỏng việc tuần tự hóa của khóa ghi để test đồng thời.
    (SQLite không có khóa hàng; việc khóa thật trên MySQL/InnoDB được kiểm tra riêng qua SQL sinh ra.)"""
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False, "timeout": 60})

    @event.listens_for(engine, "connect")
    def _no_autobegin(dbapi_conn, _):
        dbapi_conn.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin_immediate(conn):
        conn.exec_driver_sql("BEGIN IMMEDIATE")

    return engine
