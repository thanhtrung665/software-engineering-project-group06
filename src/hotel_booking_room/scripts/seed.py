"""Dữ liệu mẫu tối thiểu: role, 1 khách sạn, 4 loại phòng, vài phòng.

Chạy:  python -m scripts.seed
"""
from decimal import Decimal

from app.core.enums import RoleCode, RoomStatus, SellingStatus
from app.data_access.database import get_session_factory
from app.data_access.models import Hotel, Role, Room, RoomType


def main() -> None:
    with get_session_factory()() as s:
        if s.query(Role).count():
            print("Đã có dữ liệu, bỏ qua.")
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


if __name__ == "__main__":
    main()
