"""Dữ liệu mẫu tối thiểu: role, 1 khách sạn, 4 loại phòng, vài phòng.

Chạy:  python -m scripts.seed
"""
from datetime import datetime
from decimal import Decimal

from app.core.enums import RoleCode, RoomStatus, SellingStatus
from app.data_access.database import get_session_factory
from app.data_access.models import (Account, DepositLevel, Hotel, Promotion, Role, Room, RoomRate, RoomType,
                                    SystemSetting)


def seed_booking_data(s) -> None:
    """Dữ liệu cho cơ chế giữ phòng: tài khoản mẫu, giá, mức cọc, tham số hệ thống, mã khuyến mãi."""
    if s.query(DepositLevel).count():
        print("Dữ liệu booking đã có, bỏ qua.")
        return
    roles = {r.role_code: r.role_id for r in s.query(Role)}
    # password_hash chỉ là placeholder: use case Login/Register sẽ tạo hash bcrypt thật.
    manager = Account(role_id=roles[RoleCode.MANAGER], full_name="Hotel Manager", email="manager@hotel.example",
                      phone="0900000001", account_status="ACTIVE", password_hash="SEED_PLACEHOLDER")
    customer = Account(role_id=roles[RoleCode.CUSTOMER], full_name="Nguyen Van A", email="guest@hotel.example",
                       phone="0900000002", nationality="Vietnam", account_status="ACTIVE",
                       password_hash="SEED_PLACEHOLDER")
    s.add_all([manager, customer])
    s.flush()
    for rt in s.query(RoomType):
        s.add(RoomRate(room_type_id=rt.room_type_id, rate_type="BASE", nightly_price=rt.base_price,
                       created_by=manager.account_id))
        s.add(RoomRate(room_type_id=rt.room_type_id, rate_type="WEEKEND", weekday_no=5,
                       nightly_price=rt.base_price * Decimal("1.2"), created_by=manager.account_id))
        s.add(RoomRate(room_type_id=rt.room_type_id, rate_type="WEEKEND", weekday_no=6,
                       nightly_price=rt.base_price * Decimal("1.2"), created_by=manager.account_id))
    for pct in (20, 50, 100):
        s.add(DepositLevel(percentage=Decimal(pct), effective_from=datetime(2020, 1, 1),
                           updated_by=manager.account_id))
    for key, value, desc in (("HOLD_MINUTES", 15, "Thời gian giữ phòng chờ thanh toán (phút)"),
                             ("MAX_PENDING_BOOKINGS", 3, "Số booking Pending Payment tối đa / User"),
                             ("NO_SHOW_CUTOFF", "06:00", "Giờ chốt no-show (ngày sau check-in)")):
        s.add(SystemSetting(setting_key=key, setting_value=value, description=desc,
                            updated_by=manager.account_id))
    s.add(Promotion(promo_code="WELCOME10", discount_type="PERCENT", discount_value=Decimal(10),
                    max_discount=Decimal(300_000), valid_from=datetime(2026, 1, 1),
                    valid_to=datetime(2027, 12, 31), per_account_limit=1, promotion_status="ACTIVE",
                    is_public=True, created_by=manager.account_id))
    s.commit()
    print("Seed booking xong (khách để thử: account_id của guest@hotel.example, header X-Account-Id).")


def main() -> None:
    with get_session_factory()() as s:
        if s.query(Role).count():
            print("Đã có dữ liệu cơ bản, bỏ qua.")
            seed_booking_data(s)
            return
        s.add_all([
            Role(role_code=RoleCode.CUSTOMER, role_name="Customer"),
            Role(role_code=RoleCode.MANAGER, role_name="Manager"),
            Role(role_code=RoleCode.RECEPTIONIST, role_name="Receptionist"),
        ])
        hotel = Hotel(star_rating=4, address="Ho Chi Minh City", hotline="0900000000",
                      contact_email="contact@hotel.example")
        s.add(hotel)
        s.flush()
        specs = [("STANDARD", 25, "DOUBLE", 2, 1, 900_000), ("SUPERIOR", 30, "QUEEN", 2, 1, 1_200_000),
                 ("DELUXE", 38, "KING", 3, 1, 1_800_000), ("SUITE", 55, "KING", 4, 2, 3_200_000)]
        for floor, (code, area, bed, adults, kids, price) in enumerate(specs, start=2):
            rt = RoomType(hotel_id=hotel.hotel_id, room_type_code=code, area_sqm=Decimal(area),
                          bed_type=bed, max_adults=adults, max_children=kids,
                          base_price=Decimal(price), selling_status=SellingStatus.ON_SALE)
            s.add(rt)
            s.flush()
            for n in range(1, 4):
                s.add(Room(room_type_id=rt.room_type_id, room_number=f"{floor}0{n}",
                           floor_number=floor, room_status=RoomStatus.VACANT))
        s.commit()
        print("Seed xong.")
        seed_booking_data(s)


if __name__ == "__main__":
    main()
