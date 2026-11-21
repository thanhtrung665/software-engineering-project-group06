# Cơ chế giữ phòng 15 phút & chống tranh chấp (overselling)

## 1. Khóa hàng trên MySQL
Dự án dùng **MySQL 8 / InnoDB**: `SELECT ... FOR UPDATE` khóa hàng tới hết transaction.
`app/data_access/locking.py::for_update()` là chỗ DUY NHẤT sinh câu khóa (kèm `populate_existing` để ORM nạp lại dữ liệu mới nhất).
Mọi chỗ cần khóa **phải** đi qua hàm này. Điều kiện WHERE của câu khóa phải dùng được index (khóa chính / cột unique) –
vì vậy tra mã khuyến mãi không khóa trước rồi mới khóa theo `promotion_id` (không bọc `LOWER()` trong câu `FOR UPDATE`).

## 2. Luồng tạo booking (UC Book room, bước 7–9) – 1 transaction
```
BEGIN
  1. khóa ACCOUNT của user            -> tuần tự hóa request cùng user (A5: tối đa 3 Pending Payment)
  2. khóa ROOM_TYPE (id tăng dần)     -> "bản ghi điều phối tồn kho" (RBLQH18)
  3. TÍNH LẠI phòng trống từng đêm    -> thiếu => RoomSoldOutError (A3), rollback
  4. tính lại giá, khóa PROMOTION     -> giá đổi so với bước review => PriceChangedError (A6)
  5. INSERT booking(PENDING_PAYMENT, hold_expires_at = now + HOLD_MINUTES) + items + night rates + guest
     + status history + redemption RESERVED
COMMIT   (lỗi giữa chừng => rollback toàn bộ; deadlock => chạy lại tối đa 3 lần)
```
Phòng trống/đêm = phòng active − phòng bảo trì đêm đó − (CONFIRMED + CHECKED_IN + PENDING_PAYMENT **còn hạn**
`hold_expires_at > now`) (RBLQH01/19). Vì vậy hold quá 15 phút tự ngừng chiếm chỗ ngay cả khi job chưa chạy.

## 3. Quy ước khóa chung (tránh deadlock – RBLQH20)
Mọi luồng sửa booking/nhả hold: **ROOM_TYPE (id tăng dần) → BOOKING**. `BookingLocker` làm việc này
cho hết hạn / hủy / xác nhận thanh toán. Luồng tạo thêm ACCOUNT ở đầu và PROMOTION sau ROOM_TYPE.
**Mọi luồng mới** (check-in, bảo trì phòng, Admin hủy…) phải theo cùng thứ tự.

## 3b. Cấu hình cho MySQL (đã áp dụng)
* `build_engine()`: `isolation_level=READ COMMITTED` cố định (mặc định MySQL là REPEATABLE READ; mức này tắt gap-lock khi quét index)
  + `SET SESSION innodb_lock_wait_timeout=10` mỗi kết nối (mặc định MySQL chờ khóa 50 giây).
* Deadlock (lỗi **1213**) và hết thời gian chờ khóa (lỗi **1205**) → tự chạy lại cả transaction tối đa 3 lần (`is_transient_db_error`).
* MySQL không có partial index: `UNIQUE ... WHERE` làm bằng cột sinh tự động (xem README, mục Ghi chú).
* `.is_(True)` trên MySQL sinh `IS 1` (cú pháp sai). `tests/test_mysql_compat.py` dịch mọi câu SQL sang cú pháp MySQL,
  parse bằng sqlglot và chặn `.is_(True/False)` trong toàn bộ `app/`.
* Kiểm chứng trên DB thật: `scripts/stress_oversell.py`, `tests/test_mysql_integration.py`, `sql/02_audit_overselling.sql`.

## 4. Ánh xạ use case ↔ code
| Đặc tả | Code |
|---|---|
| Book room: giữ 15 phút, 1 transaction | `BookingHoldService.create_booking` |
| Book room: review/giá/cọc, A2 mã KM | `BookingHoldService.quote`, `PricingService`, `PromotionService` |
| A1 special requests | `create_booking` (lưu + `special_requests_notice`) |
| A3 hết phòng khi đặt đồng thời | `InventoryService.ensure_available` → `RoomSoldOutError` |
| A4 / Process payment A2: hết hạn | `HoldExpiryService`, `HoldExpiryScheduler` (job nền 30s) |
| A5 tối đa 3 Pending | `create_booking` + khóa ACCOUNT |
| A6 giá đổi | `expected_total_amount` → `PriceChangedError` (409) |
| Đồng hồ đếm ngược | `BookingDTO.hold_remaining_seconds` (tính ở server) |
| Process payment bước 6 (hold → Confirmed) | `HoldConfirmationService.confirm_paid_booking` |
| Process payment A4 (thanh toán trễ) | cùng hàm: `RESTORED` / `REFUND_REQUIRED` (RBLQH21b) |
| Cancel booking A2 (Pending) | `BookingHoldService.cancel_pending_booking` |

## 5. Tích hợp cho người làm Process payment
Gọi trong **cùng UoW** với việc ghi PAYMENT (hàm không commit):
```python
outcome = hold_confirmation.confirm_paid_booking(uow, booking_code)
# CONFIRMED/RESTORED -> ghi PAYMENT SUCCESS, tính paid_amount & payment_status (RBLQH29), gửi email
# ALREADY_CONFIRMED  -> callback trùng: idempotent; phần vượt mức cọc thì hoàn (RBLQH21c)
# REFUND_REQUIRED    -> hoàn 100% tự động + email (RBLQH21 a/b)
```
## 6. Giả định cần nhóm xác nhận
1. Mã KM giới hạn theo loại phòng: booking phải có ít nhất một loại phòng hợp lệ; giảm giá chỉ tính trên các dòng hợp lệ.
2. Giới hạn 3 booking chỉ đếm hold **còn hạn** (hold quá hạn nhưng job chưa quét không chặn user).
3. `end_date` của giá SEASON là inclusive (giống maintenance).
4. Ngoại lệ nâng hạng phòng của RBLQH01 (`is_upgrade`) chưa tính vào tồn kho (thuộc use case Check-in).
