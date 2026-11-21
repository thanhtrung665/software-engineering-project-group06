"""Tầng Presentation (bản dòng lệnh đơn giản để demo). Chạy:  python -m hotel_booking.presentation.frontdesk_cli

Nhóm Frontend (Admin Portal) sẽ gọi trực tiếp FrontDeskService, không dùng file này.
"""
from ..business.errors import FrontDeskError
from ..business.frontdesk_service import FrontDeskService
from ..config import get_connection


def _ask_int(text):
    return int(input(text).strip() or 0)


def _check_in(service, admin_id):
    code = input("Mã booking: ").strip()
    print("Nhập từng phòng được gán. Để trống booking_item_id để kết thúc.")
    assignments = []
    while True:
        item = input("  booking_item_id: ").strip()
        if not item:
            break
        assignments.append({"booking_item_id": int(item), "room_id": _ask_int("  room_id: "),
                            "upgrade_reason": input("  lý do nâng hạng (nếu có): ").strip() or None})
    guests = []
    print("Nhập từng khách. Để trống họ tên để kết thúc.")
    while True:
        name = input("  Họ tên: ").strip()
        if not name:
            break
        guests.append({"full_name": name, "phone": input("  SĐT: ").strip() or None,
                       "nationality": input("  Quốc tịch: ").strip() or None,
                       "document_type": input("  Loại giấy tờ (CITIZEN_ID/PASSPORT): ").strip() or None,
                       "document_number": input("  Số giấy tờ: ").strip() or None,
                       "is_primary": input("  Khách chính? (y/n): ").strip().lower() == "y",
                       "room_id": _ask_int("  Ở phòng (room_id): ")})
    amount = _ask_int("Số tiền thu nốt (0 nếu không): ")
    method = input("Hình thức (CASH/BANK_TRANSFER/POS, để trống nếu không thu): ").strip() or None
    print(service.check_in(code, admin_id, assignments, guests, amount, method))


def _check_out(service, admin_id):
    code = input("Mã booking: ").strip()
    charges = []
    while True:
        kind = input("Loại phụ phí (MINIBAR/EXTRA_BED/LATE_CHECKOUT/OTHER, trống = xong): ").strip()
        if not kind:
            break
        charges.append({"item_type": kind, "description": input("  Mô tả: ").strip(),
                        "quantity": _ask_int("  Số lượng: "), "unit_price": _ask_int("  Đơn giá VND: ")})
    amount = _ask_int("Số tiền thu: ")
    method = input("Hình thức (CASH/BANK_TRANSFER/POS): ").strip() or None
    print(service.check_out(code, admin_id, charges, amount, method))


def main():
    service = FrontDeskService(get_connection)
    admin_id = _ask_int("ID tài khoản lễ tân đang đăng nhập: ")
    actions = {"1": _check_in, "2": _check_out,
               "3": lambda s, a: print(s.mark_no_show(input("Mã booking: ").strip(), a))}
    while True:
        choice = input("\n1) Check-in  2) Check-out  3) No-show  0) Thoát: ").strip()
        if choice == "0":
            break
        if choice not in actions:
            continue
        try:
            actions[choice](service, admin_id)
        except FrontDeskError as err:
            print("LỖI NGHIỆP VỤ:", err)


if __name__ == "__main__":
    main()
