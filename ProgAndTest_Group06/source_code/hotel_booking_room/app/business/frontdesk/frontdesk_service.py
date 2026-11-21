"""Tầng Business Logic: nghiệp vụ lễ tân (Front-desk operations) - phần của Bình An.

3 chức năng:
  1. check_in    : gán phòng vật lý, thu nốt tiền còn lại, chuyển booking -> CHECKED_IN, phòng -> OCCUPIED
  2. check_out   : tính phụ phí, thu đủ, xuất hóa đơn, booking -> CHECKED_OUT, phòng -> NEEDS_CLEANING
  3. mark_no_show: quá mốc no-show -> NO_SHOW, tính phí đêm đầu, tạo yêu cầu hoàn phần còn lại

Mỗi chức năng chạy trong 1 transaction duy nhất: lỗi giữa chừng thì rollback hết (ACID).
Tầng này KHÔNG viết SQL (gọi data_access) và KHÔNG in/nhập dữ liệu (việc của presentation).
"""
import os
import uuid
from contextlib import contextmanager

from app.data_access.frontdesk import frontdesk_dao as dao
from . import frontdesk_rules as rules
from .errors import FrontDeskError


def _encrypt_document(number: str):
    """Mã hóa số CCCD/hộ chiếu trước khi lưu (RBLQH13). Khóa lấy từ biến môi trường HOTEL_ID_KEY.

    Tạo khóa 1 lần:  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    from cryptography.fernet import Fernet

    key = os.getenv("HOTEL_ID_KEY")
    if not key:
        raise FrontDeskError("Thiếu biến môi trường HOTEL_ID_KEY để mã hóa giấy tờ khách.")
    return Fernet(key.encode()).encrypt(number.encode()), "v1"


class FrontDeskService:
    def __init__(self, conn_factory):
        """conn_factory: hàm không tham số trả về 1 kết nối MySQL (vd config.get_connection)."""
        self._conn_factory = conn_factory

    @contextmanager
    def _transaction(self):
        conn = self._conn_factory()
        try:
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------ CHECK-IN
    def check_in(self, booking_code, admin_id, assignments, guests,
                 collected_amount=0, payment_method=None, now=None):
        """
        assignments: [{"booking_item_id": 1, "room_id": 101, "upgrade_reason": None}, ...]
                     đúng `quantity` dòng cho mỗi booking_item. upgrade_reason chỉ cần khi gán phòng hạng cao hơn.
        guests     : [{"full_name", "phone", "nationality", "document_type", "document_number",
                       "is_primary", "room_id"}, ...]  đủ số người lớn + trẻ em.
        collected_amount: tiền thu nốt tại quầy (phải đúng bằng số còn thiếu nếu booking mới cọc).
        """
        now = now or rules.now_vn()
        with self._transaction() as cur:
            booking = dao.get_booking_for_update(cur, booking_code)
            if not booking:
                raise FrontDeskError("Không tìm thấy booking.")
            if booking["booking_status"] != "CONFIRMED":
                raise FrontDeskError(
                    f"Booking đang ở trạng thái {booking['booking_status']}, chỉ check-in được booking CONFIRMED.")
            cutoff = rules.parse_hhmm(dao.get_setting(cur, "NO_SHOW_CUTOFF"))
            rules.check_in_allowed(booking["check_in_date"], now, cutoff)

            booking_id = booking["booking_id"]
            items = dao.get_booking_items(cur, booking_id)

            # --- 1. kiểm tra & gán phòng (không check-in một phần: thiếu 1 phòng là từ chối) ---
            self._validate_assignment_counts(items, assignments)
            assigned = {}  # room_id -> assignment_id
            for a in assignments:
                item = next(i for i in items if i["booking_item_id"] == a["booking_item_id"])
                room = dao.get_room_for_update(cur, a["room_id"])
                is_upgrade = self._check_room(room, item, a)
                if a["room_id"] in assigned:
                    raise FrontDeskError(f"Phòng {room['room_number']} bị chọn 2 lần.")
                assignment_id = dao.insert_assignment(
                    cur, item["booking_item_id"], room["room_id"], now, admin_id,
                    is_upgrade, a.get("upgrade_reason") if is_upgrade else None)
                assigned[room["room_id"]] = assignment_id
                dao.update_room_status(cur, room["room_id"], "OCCUPIED", now)

            # --- 2. khai báo khách + mã hóa giấy tờ ---
            expected = int(booking["adults"]) + int(booking["children"])
            rules.validate_guests(guests, expected, set(assigned))
            for g in guests:
                enc, ver = (None, None)
                if g.get("document_number"):
                    enc, ver = _encrypt_document(g["document_number"])
                dao.insert_guest(cur, booking_id, assigned[g["room_id"]], g, enc, ver)

            # --- 3. thu nốt tiền còn lại ---
            paid, refunded = dao.get_payment_totals(cur, booking_id)
            net_paid = paid - refunded
            total = int(booking["total_amount"])
            due = max(0, total - net_paid)
            if due > 0:
                self._require_collection(collected_amount, due, payment_method)
                dao.insert_payment(cur, booking_id, self._ref("FD"), payment_method, "BALANCE", due, admin_id, now)
                net_paid += due
            dao.update_booking_money(cur, booking_id, net_paid, max(0, total - net_paid),
                                     "FULLY_PAID" if net_paid >= total else "DEPOSIT_PAID", now)

            # --- 4. đổi trạng thái + lịch sử + audit ---
            dao.update_booking_status(cur, booking_id, "CHECKED_IN", now)
            dao.insert_status_history(cur, booking_id, "CONFIRMED", "CHECKED_IN", admin_id, "Check-in", now)
            dao.insert_audit(cur, admin_id, "BOOKING_STATUS_CHANGED", "BOOKING", booking_id,
                             {"booking_status": "CONFIRMED"},
                             {"booking_status": "CHECKED_IN", "rooms": sorted(assigned)}, "Check-in", now)
            return {"booking_code": booking_code, "status": "CHECKED_IN",
                    "rooms": sorted(assigned), "collected": due}

    # ----------------------------------------------------------------- CHECK-OUT
    def check_out(self, booking_code, admin_id, extra_charges=None,
                  collected_amount=0, payment_method=None, now=None):
        """
        extra_charges: [{"item_type": "MINIBAR", "description": "...", "quantity": 2, "unit_price": 30000}, ...]
        collected_amount: tiền thu tại quầy, phải đúng bằng (còn thiếu + phụ phí) - RBLQH25, kịch bản A3.
        """
        now = now or rules.now_vn()
        extra_charges = extra_charges or []
        with self._transaction() as cur:
            booking = dao.get_booking_for_update(cur, booking_code)
            if not booking:
                raise FrontDeskError("Không tìm thấy booking.")
            if booking["booking_status"] != "CHECKED_IN":
                raise FrontDeskError("Chỉ check-out được booking đang ở trạng thái CHECKED_IN.")
            booking_id = booking["booking_id"]
            total = int(booking["total_amount"])

            incidental = rules.validate_incidentals(extra_charges)
            paid, refunded = dao.get_payment_totals(cur, booking_id)
            net_paid = paid - refunded
            due = rules.balance_due(total, incidental, net_paid)
            if due < 0:
                raise FrontDeskError("Khách đã trả dư, cần Manager xử lý hoàn tiền trước khi check-out.")

            # thu tiền: phần còn thiếu của tiền phòng (BALANCE) + phụ phí (EXTRA_CHARGE)
            if due > 0:
                self._require_collection(collected_amount, due, payment_method)
                room_part = max(0, total - net_paid)
                if room_part:
                    dao.insert_payment(cur, booking_id, self._ref("FD"), payment_method, "BALANCE",
                                       room_part, admin_id, now)
                if due - room_part:
                    dao.insert_payment(cur, booking_id, self._ref("FD"), payment_method, "EXTRA_CHARGE",
                                       due - room_part, admin_id, now)
            # paid_amount = tổng thu thành công - hoàn tiền (gồm cả phụ phí), RBLQH22
            dao.update_booking_money(cur, booking_id, net_paid + due, 0, "FULLY_PAID", now)

            invoice_id, invoice_total = self._issue_invoice(cur, booking, extra_charges, incidental, now)

            # phòng -> NEEDS_CLEANING, đóng assignment
            for a in dao.get_active_assignments(cur, booking_id):
                dao.update_room_status(cur, a["room_id"], "NEEDS_CLEANING", now)
                dao.release_assignment(cur, a["assignment_id"], now)

            dao.update_booking_status(cur, booking_id, "CHECKED_OUT", now, remaining_amount=0)
            dao.insert_status_history(cur, booking_id, "CHECKED_IN", "CHECKED_OUT", admin_id, "Check-out", now)
            dao.insert_audit(cur, admin_id, "BOOKING_STATUS_CHANGED", "BOOKING", booking_id,
                             {"booking_status": "CHECKED_IN"},
                             {"booking_status": "CHECKED_OUT", "invoice_id": invoice_id,
                              "incidental_total": incidental}, "Check-out", now)
            return {"booking_code": booking_code, "status": "CHECKED_OUT",
                    "invoice_id": invoice_id, "invoice_total": invoice_total, "collected": max(due, 0)}

    # ------------------------------------------------------------------- NO-SHOW
    def mark_no_show(self, booking_code, admin_id=None, now=None):
        """admin_id=None nghĩa là job tự động (System Scheduler) gọi."""
        now = now or rules.now_vn()
        with self._transaction() as cur:
            booking = dao.get_booking_for_update(cur, booking_code)
            if not booking:
                raise FrontDeskError("Không tìm thấy booking.")
            # đọc lại trạng thái SAU khi khoá: nếu vừa check-in xong thì bỏ qua (RBLQH28)
            if booking["booking_status"] != "CONFIRMED":
                raise FrontDeskError(f"Booking đang ở trạng thái {booking['booking_status']}, không thể No-show.")
            cutoff = rules.parse_hhmm(dao.get_setting(cur, "NO_SHOW_CUTOFF"))
            rules.no_show_allowed(booking["check_in_date"], now, cutoff)

            booking_id = booking["booking_id"]
            paid, refunded = dao.get_payment_totals(cur, booking_id)
            net_paid = paid - refunded
            first_night = rules.first_night_net(dao.get_night_rates(cur, booking_id))
            fee, refund_total = rules.no_show_fee_and_refund(first_night, net_paid)

            if refund_total > 0:
                parts = rules.allocate_refund(refund_total, dao.get_refundable_payments(cur, booking_id))
                channel_of = {p["payment_id"]: p["payment_channel"]
                              for p in dao.get_refundable_payments(cur, booking_id)}
                for index, (payment_id, amount) in enumerate(parts):
                    dao.insert_refund(cur, booking_id, payment_id, self._ref("RF"), amount,
                                      fee if index == 0 else 0, "No-show", "NO_SHOW",
                                      channel_of[payment_id], admin_id, now)
            # refund PENDING -> payment_status giữ nguyên (RBLQH29); remaining_amount = 0
            dao.update_booking_status(cur, booking_id, "NO_SHOW", now, remaining_amount=0)
            dao.insert_status_history(cur, booking_id, "CONFIRMED", "NO_SHOW", admin_id,
                                      "Quá mốc no-show", now)
            dao.insert_audit(cur, admin_id, "BOOKING_STATUS_CHANGED", "BOOKING", booking_id,
                             {"booking_status": "CONFIRMED"},
                             {"booking_status": "NO_SHOW", "fee": fee, "refund": refund_total},
                             "No-show", now)
            return {"booking_code": booking_code, "status": "NO_SHOW", "fee": fee, "refund": refund_total}

    # ------------------------------------------------------------- hàm phụ trợ
    @staticmethod
    def _ref(prefix):
        return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _require_collection(collected, due, method):
        if method not in rules.FRONT_DESK_PAYMENT_METHODS:
            raise FrontDeskError(f"Phương thức thu tiền phải thuộc {sorted(rules.FRONT_DESK_PAYMENT_METHODS)}.")
        if collected != due:
            raise FrontDeskError(f"Cần thu đúng {due:,} VND, hiện nhập {collected:,} VND.".replace(",", "."))

    @staticmethod
    def _validate_assignment_counts(items, assignments):
        for item in items:
            n = sum(1 for a in assignments if a["booking_item_id"] == item["booking_item_id"])
            if n != item["quantity"]:
                raise FrontDeskError(
                    f"Loại phòng {item['room_type_code']} cần gán {item['quantity']} phòng, mới chọn {n}.")
        known = {i["booking_item_id"] for i in items}
        if any(a["booking_item_id"] not in known for a in assignments):
            raise FrontDeskError("Có phòng gán cho booking_item không thuộc booking này.")

    @staticmethod
    def _check_room(room, item, assignment):
        """Trả về is_upgrade. Chỉ nhận phòng VACANT, đang hoạt động; hạng cao hơn cần lý do (RBLQH04)."""
        if not room or not room["is_active"]:
            raise FrontDeskError("Phòng không tồn tại hoặc đã ngừng hoạt động.")
        if room["room_status"] != "VACANT":
            raise FrontDeskError(f"Phòng {room['room_number']} đang {room['room_status']}, chỉ gán được phòng VACANT.")
        if room["room_type_id"] == item["room_type_id"]:
            return False
        if room["base_price"] <= item["base_price"]:
            raise FrontDeskError(f"Phòng {room['room_number']} không cùng loại và không phải hạng cao hơn.")
        if not assignment.get("upgrade_reason"):
            raise FrontDeskError("Nâng hạng phòng bắt buộc phải có lý do (upgrade_reason).")
        return True

    @staticmethod
    def _issue_invoice(cur, booking, extra_charges, incidental, now):
        booking_id = booking["booking_id"]
        gross = int(booking["total_amount"]) + incidental
        vat = float(dao.get_setting(cur, "VAT_RATE", 0) or 0)
        svc = float(dao.get_setting(cur, "SERVICE_FEE", 0) or 0)
        tax, service_fee = rules.split_inclusive(gross, vat), rules.split_inclusive(gross, svc)
        number = f"INV-{now:%Y%m%d}-{booking_id}"
        invoice_id = dao.insert_invoice(cur, booking_id, number, now, gross - tax - service_fee, tax,
                                        service_fee, int(booking["discount_amount"]), gross)
        for item in dao.get_booking_items(cur, booking_id):
            dao.insert_invoice_item(cur, invoice_id, "ROOM",
                                    f"Tiền phòng {item['quantity']} x {item['room_type_code']}", 1,
                                    int(item["line_total"]), int(item["line_total"]))
        for c in extra_charges:
            dao.insert_invoice_item(cur, invoice_id, c["item_type"], c["description"], c["quantity"],
                                    c["unit_price"], round(c["quantity"] * c["unit_price"]))
        dao.link_payments_to_invoice(cur, booking_id, invoice_id)
        return invoice_id, gross
