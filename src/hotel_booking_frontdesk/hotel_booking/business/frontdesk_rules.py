"""Các quy tắc nghiệp vụ THUẦN (không đụng database) của lễ tân.

Tách riêng để dễ viết unit test. Tham chiếu theo đề: RBLQH12, RBLQH24, RBLQH25,
RBLQH09, RBLQH27, RBLQH29 và Use case 14 (Manage bookings and front desk).
Tiền là số nguyên VND.
"""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .errors import FrontDeskError

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
DEFAULT_NO_SHOW_CUTOFF = time(6, 0)
FRONT_DESK_PAYMENT_METHODS = {"CASH", "BANK_TRANSFER", "POS"}
INCIDENTAL_TYPES = {"MINIBAR", "EXTRA_BED", "LATE_CHECKOUT", "OTHER"}


def now_vn() -> datetime:
    """Giờ Việt Nam, bỏ tzinfo để lưu thẳng vào cột TIMESTAMP."""
    return datetime.now(VN_TZ).replace(tzinfo=None)


def parse_hhmm(value, default: time = DEFAULT_NO_SHOW_CUTOFF) -> time:
    if value is None:
        return default
    if isinstance(value, time):
        return value
    text = str(value).strip().strip('"')
    hour, minute = text.split(":")[:2]
    return time(int(hour), int(minute))


def no_show_cutoff_at(check_in_date: date, cutoff: time) -> datetime:
    """Mốc no-show: mặc định 06:00 NGÀY HÔM SAU ngày check-in."""
    return datetime.combine(check_in_date + timedelta(days=1), cutoff)


def check_in_allowed(check_in_date: date, now: datetime, cutoff: time) -> None:
    """Cho check-in từ 00:00 ngày check-in đến trước mốc no-show (RBLQH12)."""
    start = datetime.combine(check_in_date, time(0, 0))
    end = no_show_cutoff_at(check_in_date, cutoff)
    if now < start:
        raise FrontDeskError("Chưa đến ngày check-in (cho phép từ 00:00 ngày check-in).")
    if now >= end:
        raise FrontDeskError("Đã quá mốc no-show, không thể check-in.")


def no_show_allowed(check_in_date: date, now: datetime, cutoff: time) -> None:
    if now < no_show_cutoff_at(check_in_date, cutoff):
        raise FrontDeskError("Chưa quá mốc no-show nên chưa thể đánh dấu No-show.")


def balance_due(total_amount: int, incidental_total: int, net_paid: int) -> int:
    """RBLQH25: còn phải thu = tổng tiền + phụ phí - (thanh toán thành công - hoàn tiền thành công)."""
    return total_amount + incidental_total - net_paid


def split_inclusive(gross: int, percent: float) -> int:
    """Tách phần thuế/phí đã NẰM TRONG giá (giá đã gồm VAT, không cộng thêm)."""
    if not percent:
        return 0
    return round(gross * percent / (100 + percent))


def first_night_net(nights: list) -> int:
    """Tiền đêm đầu (sau giảm giá, tất cả phòng) = SUM(night_total - night_discount) của stay_date nhỏ nhất."""
    if not nights:
        return 0
    first_date = min(n["stay_date"] for n in nights)
    return sum(int(n["night_total"]) - int(n["night_discount"]) for n in nights if n["stay_date"] == first_date)


def no_show_fee_and_refund(first_night: int, net_paid: int) -> tuple:
    """No-show: phí = tiền đêm đầu nhưng không vượt số đã trả; phần còn lại được hoàn (RBLQH09)."""
    fee = min(first_night, net_paid)
    return fee, net_paid - fee


def allocate_refund(refund_total: int, payments: list) -> list:
    """Chia số tiền hoàn lên các payment (mới nhất trước), mỗi payment không hoàn quá số tiền của nó (RBLTT14).

    payments: [{"payment_id": .., "refundable": ..}, ...] đã sắp xếp mới -> cũ.
    Trả về [(payment_id, amount), ...].
    """
    result, left = [], refund_total
    for p in payments:
        if left <= 0:
            break
        part = min(left, int(p["refundable"]))
        if part > 0:
            result.append((p["payment_id"], part))
            left -= part
    if left > 0:
        raise FrontDeskError("Số tiền hoàn lớn hơn tổng các khoản đã thu, cần Manager xử lý thủ công.")
    return result


def validate_guests(guests: list, expected_count: int, assigned_room_ids: set) -> None:
    """RBLQH27: đủ số khách, có 1 khách chính, mỗi khách thuộc đúng 1 phòng đã gán."""
    if len(guests) != expected_count:
        raise FrontDeskError(f"Cần khai báo đủ {expected_count} khách, hiện có {len(guests)}.")
    primaries = [g for g in guests if g.get("is_primary")]
    if len(primaries) != 1:
        raise FrontDeskError("Phải có đúng 1 khách chính (is_primary).")
    main = primaries[0]
    if not main.get("document_type") or not main.get("document_number"):
        raise FrontDeskError("Khách chính phải có loại giấy tờ (CITIZEN_ID/PASSPORT) và số giấy tờ.")
    if main["document_type"] not in ("CITIZEN_ID", "PASSPORT"):
        raise FrontDeskError("document_type chỉ nhận CITIZEN_ID hoặc PASSPORT.")
    for g in guests:
        if not g.get("full_name"):
            raise FrontDeskError("Mỗi khách phải có họ tên.")
        if g.get("room_id") not in assigned_room_ids:
            raise FrontDeskError(f"Khách {g['full_name']} chưa được xếp vào phòng nào đã gán.")


def validate_incidentals(charges: list) -> int:
    """Kiểm tra phụ phí và trả về tổng tiền phụ phí."""
    total = 0
    for c in charges:
        if c.get("item_type") not in INCIDENTAL_TYPES:
            raise FrontDeskError(f"item_type phải thuộc {sorted(INCIDENTAL_TYPES)}.")
        if not c.get("description"):
            raise FrontDeskError("Mỗi phụ phí cần mô tả.")
        if c["quantity"] <= 0 or c["unit_price"] < 0:
            raise FrontDeskError("Số lượng phải > 0 và đơn giá không âm.")
        total += round(c["quantity"] * c["unit_price"])
    return total
