"""Tầng Data Access: CHỈ chứa câu lệnh SQL, không chứa quy tắc nghiệp vụ.

Mọi hàm nhận `cur` (cursor kiểu dictionary=True) từ tầng Business để tất cả
nằm trong CÙNG 1 transaction. Tên bảng/cột theo mục VI. Data Model của báo cáo.
Nếu nhóm Database đặt tên khác thì chỉ cần sửa file này.
"""
import json


# ---------- đọc dữ liệu ----------
def get_setting(cur, key, default=None):
    cur.execute("SELECT setting_value FROM system_setting WHERE setting_key = %s", (key,))
    row = cur.fetchone()
    if not row:
        return default
    value = row["setting_value"]
    if isinstance(value, (bytes, str)):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def get_booking_for_update(cur, booking_code):
    """Khoá dòng booking (SELECT ... FOR UPDATE) để check-in và job no-show không chạy chồng nhau (RBLQH28)."""
    cur.execute("SELECT * FROM booking WHERE booking_code = %s FOR UPDATE", (booking_code,))
    return cur.fetchone()


def get_booking_items(cur, booking_id):
    cur.execute(
        """SELECT bi.*, rt.room_type_code, rt.max_adults, rt.max_children, rt.base_price
           FROM booking_item bi JOIN room_type rt ON rt.room_type_id = bi.room_type_id
           WHERE bi.booking_id = %s ORDER BY bi.booking_item_id""",
        (booking_id,),
    )
    return cur.fetchall()


def get_room_for_update(cur, room_id):
    cur.execute(
        """SELECT r.room_id, r.room_number, r.room_type_id, r.room_status, r.is_active, rt.base_price,
                  rt.max_adults, rt.max_children
           FROM room r JOIN room_type rt ON rt.room_type_id = r.room_type_id
           WHERE r.room_id = %s FOR UPDATE""",
        (room_id,),
    )
    return cur.fetchone()


def list_vacant_rooms(cur, room_type_id):
    """Danh sách phòng VACANT của 1 loại phòng (để lễ tân chọn khi check-in)."""
    cur.execute(
        """SELECT room_id, room_number, floor_number FROM room
           WHERE room_type_id = %s AND room_status = 'VACANT' AND is_active = TRUE
           ORDER BY floor_number, room_number""",
        (room_type_id,),
    )
    return cur.fetchall()


def get_night_rates(cur, booking_id):
    cur.execute(
        """SELECT bnr.stay_date, bnr.night_total, bnr.night_discount
           FROM booking_night_rate bnr JOIN booking_item bi ON bi.booking_item_id = bnr.booking_item_id
           WHERE bi.booking_id = %s""",
        (booking_id,),
    )
    return cur.fetchall()


def get_payment_totals(cur, booking_id):
    """Trả về (tổng payment SUCCESS, tổng refund SUCCESS) -> net_paid = a - b (RBLQH22)."""
    cur.execute(
        "SELECT COALESCE(SUM(amount),0) AS s FROM payment WHERE booking_id=%s AND payment_status='SUCCESS'",
        (booking_id,),
    )
    paid = int(cur.fetchone()["s"])
    cur.execute(
        "SELECT COALESCE(SUM(refund_amount),0) AS s FROM refund WHERE booking_id=%s AND refund_status='SUCCESS'",
        (booking_id,),
    )
    refunded = int(cur.fetchone()["s"])
    return paid, refunded


def get_refundable_payments(cur, booking_id):
    """Các payment SUCCESS còn có thể hoàn (amount trừ các refund chưa FAILED), mới nhất trước."""
    cur.execute(
        """SELECT p.payment_id, p.payment_channel, p.amount,
                  p.amount - COALESCE((SELECT SUM(r.refund_amount) FROM refund r
                                       WHERE r.payment_id = p.payment_id AND r.refund_status <> 'FAILED'), 0) AS refundable
           FROM payment p
           WHERE p.booking_id = %s AND p.payment_status = 'SUCCESS'
           ORDER BY p.paid_at DESC, p.payment_id DESC""",
        (booking_id,),
    )
    return cur.fetchall()


def get_active_assignments(cur, booking_id):
    cur.execute(
        """SELECT a.assignment_id, a.room_id FROM booking_room_assignment a
           JOIN booking_item bi ON bi.booking_item_id = a.booking_item_id
           WHERE bi.booking_id = %s AND a.released_at IS NULL""",
        (booking_id,),
    )
    return cur.fetchall()


# ---------- ghi dữ liệu ----------
def insert_assignment(cur, booking_item_id, room_id, assigned_at, admin_id, is_upgrade, upgrade_reason):
    cur.execute(
        """INSERT INTO booking_room_assignment
           (booking_item_id, room_id, assigned_at, assigned_by, is_upgrade, upgrade_reason)
           VALUES (%s,%s,%s,%s,%s,%s)""",
        (booking_item_id, room_id, assigned_at, admin_id, is_upgrade, upgrade_reason),
    )
    return cur.lastrowid


def insert_guest(cur, booking_id, assignment_id, g, doc_encrypted, key_version):
    cur.execute(
        """INSERT INTO booking_guest
           (booking_id, assignment_id, full_name, phone, nationality, document_type,
            document_number_encrypted, document_key_version, is_primary_guest)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (booking_id, assignment_id, g["full_name"], g.get("phone"), g.get("nationality"),
         g.get("document_type"), doc_encrypted, key_version, bool(g.get("is_primary"))),
    )


def insert_payment(cur, booking_id, reference, method, purpose, amount, admin_id, paid_at):
    cur.execute(
        """INSERT INTO payment
           (booking_id, payment_reference, gateway_transaction_id, payment_channel, payment_method, payment_purpose,
            amount, payment_status, gateway_signature_valid, processed_by, paid_at, created_at)
           VALUES (%s,%s,%s,'FRONT_DESK',%s,%s,%s,'SUCCESS',1,%s,%s,%s)""",
        (booking_id, reference, reference, method, purpose, amount, admin_id, paid_at, paid_at),
    )
    return cur.lastrowid


def insert_refund(cur, booking_id, payment_id, reference, amount, fee, reason, refund_type,
                  channel, admin_id, requested_at):
    cur.execute(
        """INSERT INTO refund
           (booking_id, payment_id, refund_reference, refund_amount, cancellation_fee, refund_reason,
            refund_type, refund_channel, refund_status, gateway_refund_id, processed_by, requested_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'PENDING',%s,%s,%s)""",
        (booking_id, payment_id, reference, amount, fee, reason, refund_type, channel, reference, admin_id, requested_at),
    )


def update_booking_money(cur, booking_id, paid_amount, remaining_amount, payment_status, now):
    cur.execute(
        """UPDATE booking SET paid_amount=%s, remaining_amount=%s, payment_status=%s, updated_at=%s
           WHERE booking_id=%s""",
        (paid_amount, remaining_amount, payment_status, now, booking_id),
    )


def update_booking_status(cur, booking_id, new_status, now, remaining_amount=None):
    if remaining_amount is None:
        cur.execute("UPDATE booking SET booking_status=%s, updated_at=%s WHERE booking_id=%s",
                    (new_status, now, booking_id))
    else:
        cur.execute(
            "UPDATE booking SET booking_status=%s, remaining_amount=%s, updated_at=%s WHERE booking_id=%s",
            (new_status, remaining_amount, now, booking_id),
        )


def update_room_status(cur, room_id, new_status, now):
    cur.execute("UPDATE room SET room_status=%s, updated_at=%s WHERE room_id=%s", (new_status, now, room_id))


def release_assignment(cur, assignment_id, now):
    cur.execute("UPDATE booking_room_assignment SET released_at=%s WHERE assignment_id=%s", (now, assignment_id))


def insert_status_history(cur, booking_id, old_status, new_status, admin_id, reason, now):
    source = "ADMIN" if admin_id is not None else "SYSTEM_SCHEDULER"  # ràng buộc RBLTT15
    cur.execute(
        """INSERT INTO booking_status_history
           (booking_id, old_status, new_status, changed_by, changed_source, change_reason, changed_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (booking_id, old_status, new_status, admin_id, source, reason, now),
    )


def insert_audit(cur, admin_id, action_code, entity_type, entity_id, before, after, reason, now):
    cur.execute(
        """INSERT INTO audit_log
           (actor_account_id, action_code, entity_type, entity_id, before_data, after_data, reason, created_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (admin_id, action_code, entity_type, str(entity_id),
         json.dumps(before) if before is not None else None,
         json.dumps(after) if after is not None else None, reason, now),
    )


def link_payments_to_invoice(cur, booking_id, invoice_id):
    cur.execute(
        """UPDATE payment SET invoice_id=%s
           WHERE booking_id=%s AND payment_status='SUCCESS' AND invoice_id IS NULL""",
        (invoice_id, booking_id),
    )


def insert_invoice(cur, booking_id, number, issued_at, subtotal, tax, service_fee, discount, total):
    cur.execute(
        """INSERT INTO invoice
           (booking_id, invoice_number, issued_at, subtotal_amount, tax_amount, service_fee,
            discount_amount, total_amount, invoice_status)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'ISSUED')""",
        (booking_id, number, issued_at, subtotal, tax, service_fee, discount, total),
    )
    return cur.lastrowid


def insert_invoice_item(cur, invoice_id, item_type, description, quantity, unit_price, line_total):
    cur.execute(
        """INSERT INTO invoice_item (invoice_id, item_type, description, quantity, unit_price, line_total)
           VALUES (%s,%s,%s,%s,%s,%s)""",
        (invoice_id, item_type, description, quantity, unit_price, line_total),
    )
