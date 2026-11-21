-- DEMO ROW LOCK TRÊN MYSQL/INNODB
-- Mở 2 tab/session MySQL Workbench, chọn database hotel_booking_system.
-- Session A:
START TRANSACTION;
SELECT room_type_id, type_code
FROM room_type
WHERE room_type_id = 1
FOR UPDATE;
-- Giữ transaction mở. Chuyển sang Session B.

-- Session B (sẽ chờ khóa của Session A):
-- START TRANSACTION;
-- SELECT room_type_id, type_code
-- FROM room_type
-- WHERE room_type_id = 1
-- FOR UPDATE;
-- Sau khi kiểm tra, quay lại Session A:
-- COMMIT;
-- Session B sẽ tiếp tục sau khi Session A commit.
