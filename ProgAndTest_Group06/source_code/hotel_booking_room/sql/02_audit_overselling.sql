-- KIỂM TRA OVERSELLING trên MySQL 8.0+ / InnoDB (chỉ đọc dữ liệu).
-- Quy tắc: phòng active - phòng bảo trì - booking đã xác nhận/đang ở/hold còn hạn.
USE hotel_booking_system;
SET @now_utc = UTC_TIMESTAMP(3);

-- (A) Kiểm tra số phòng bán theo từng đêm có vượt nguồn cung hay không.
WITH RECURSIVE counted AS (
    SELECT bi.room_type_id, bi.quantity, b.check_in_date, b.check_out_date
    FROM booking AS b
    JOIN booking_item AS bi ON bi.booking_id = b.booking_id
    WHERE b.booking_status IN ('CONFIRMED', 'CHECKED_IN')
       OR (b.booking_status = 'PENDING_PAYMENT' AND b.hold_expires_at > @now_utc)
),
expanded AS (
    SELECT room_type_id, quantity, check_in_date AS stay_date, check_out_date
    FROM counted
    UNION ALL
    SELECT room_type_id, quantity, DATE_ADD(stay_date, INTERVAL 1 DAY), check_out_date
    FROM expanded
    WHERE DATE_ADD(stay_date, INTERVAL 1 DAY) < check_out_date
),
demand AS (
    SELECT room_type_id, stay_date, SUM(quantity) AS booked_rooms
    FROM expanded
    GROUP BY room_type_id, stay_date
),
supply AS (
    SELECT d.room_type_id, d.stay_date, d.booked_rooms,
           (SELECT COUNT(*) FROM room AS r
             WHERE r.room_type_id = d.room_type_id AND r.is_active = 1) AS active_rooms,
           (SELECT COUNT(DISTINCT m.room_id)
              FROM room_maintenance AS m
              JOIN room AS r ON r.room_id = m.room_id
             WHERE r.room_type_id = d.room_type_id AND r.is_active = 1
               AND m.maintenance_status IN ('PLANNED', 'IN_PROGRESS')
               AND d.stay_date BETWEEN m.start_date AND m.end_date) AS maintenance_rooms
    FROM demand AS d
)
SELECT room_type_id, stay_date, booked_rooms, active_rooms, maintenance_rooms,
       booked_rooms - (active_rooms - maintenance_rooms) AS rooms_oversold
FROM supply
WHERE booked_rooms > active_rooms - maintenance_rooms
ORDER BY room_type_id, stay_date;

-- (B) Hold đã quá hạn nhưng job nền chưa dọn (chỉ dùng theo dõi job).
SELECT booking_code, booking_status, hold_expires_at,
       TIMESTAMPDIFF(SECOND, hold_expires_at, @now_utc) AS seconds_overdue
FROM booking
WHERE booking_status = 'PENDING_PAYMENT'
  AND hold_expires_at <= DATE_SUB(@now_utc, INTERVAL 2 MINUTE);

-- (C) Đối chiếu promotion.used_count với lượt redemption thực tế.
SELECT p.promotion_id, p.promo_code, p.used_count,
       COUNT(CASE WHEN r.redemption_status IN ('RESERVED', 'CONSUMED') THEN 1 END) AS real_usage
FROM promotion AS p
LEFT JOIN promotion_redemption AS r ON r.promotion_id = p.promotion_id
GROUP BY p.promotion_id, p.promo_code, p.used_count
HAVING p.used_count <> real_usage;
