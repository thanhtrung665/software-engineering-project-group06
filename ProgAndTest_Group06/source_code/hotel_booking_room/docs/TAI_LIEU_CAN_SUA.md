# Các mục trong `Hotel_Booking_System_Group06.docx` cần sửa để khớp MySQL + Python + Docker

Tài liệu gốc viết theo **MySQL + PHP**. Khi đổi từ SQL Server sang MySQL, hầu hết mục về kiểu dữ liệu/khóa (`TIMESTAMP`, `BOOLEAN`,
`JSON`, `UUID`, `SELECT ... FOR UPDATE`, `NULL UNIQUE`) **đã đúng** với MySQL nên không cần sửa. Chỉ còn các mục dưới đây.
(Danh sách dựa trên các trích dẫn trong bản trước của file này – hãy Ctrl+F lại trong .docx để xác nhận.)
Mức độ: 🔴 sai/gây lỗi khi lập trình · 🟡 nên sửa cho nhất quán.

## A. Công nghệ
| # | Mục | Tìm | Đang viết | Sửa thành | |
|---|---|---|---|---|---|
| A1 | **II → Design Constraints** | `written in PHP` | REST API viết bằng PHP | REST API viết bằng **Python (FastAPI, SQLAlchemy)**, giữ cấu trúc 3 tầng | 🔴 |
| A2 | cùng mục | `Rocky Linux 9` | Linux + Node.js + PHP + MySQL | Docker Compose: Python + **MySQL 8.4** (Node.js chỉ nếu giữ giao diện Next.js) | 🟡 |
| A3 | **II → Reliability** | `Section VI.3.5` | Tham chiếu "Section VI.3.5, RBLQH03" | **Sai tham chiếu**: VI.3 là ERD. RBLQH03 nằm ở **VI.2.5** | 🔴 |
| A4 | **VI.5** – Isolation | `gap-lock` / `REPEATABLE READ` | Dựa vào REPEATABLE READ + gap-lock của InnoDB | Code dùng **READ COMMITTED + `SELECT ... FOR UPDATE` trên ROOM_TYPE** (không dựa gap-lock); `innodb_lock_wait_timeout=10`; chạy lại khi deadlock (**1213**) / hết chờ khóa (**1205**) | 🟡 |
| A5 | **VI.5** – Concurrency control | `if the DBMS supports it` | "lock ROOM_TYPE row with SELECT … FOR UPDATE if the DBMS supports it" | MySQL/InnoDB hỗ trợ: khóa ROOM_TYPE theo **id tăng dần** rồi **tính lại** phòng trống rồi mới tạo hold; mọi luồng khóa cùng thứ tự **ROOM_TYPE → BOOKING** | 🟡 |

## B. Ràng buộc MySQL không biểu diễn được như tài liệu mô tả
| # | Mục | Tìm | Vấn đề | Cách đã làm trong code | |
|---|---|---|---|---|---|
| B1 | **VI.1.2 ACCOUNT** `email`, **VI.2.3 RBLB01** | `LOWER(email)` / `WHERE deleted_at IS NULL` | MySQL **không có partial index** và index theo `LOWER()` | Collation `_ci` đã không phân biệt hoa/thường; cột sinh tự động `active_email_key` (= LOWER(email) nếu chưa xóa mềm, NULL nếu đã xóa) + UNIQUE | 🔴 |
| B2 | **VI.2.3 RBLB12** (mức cọc active duy nhất) | `WHERE is_active` | Như B1 | Cột sinh tự động `active_percentage_key` + UNIQUE | 🔴 |
| B3 | **VI.2.3 RBLB10, RBLB11** và **VI.2.5 RBLQH04** | `exclusion constraint` | "Exclusion constraint" là của PostgreSQL; MySQL không có (khoảng thời gian chồng lấn không biểu diễn được bằng UNIQUE) | Kiểm tra trong service **dưới khóa** (hoặc trigger) | 🟡 |
| B4 | **VI.5** – timestamp | `TIMESTAMP WITH TIME ZONE` | MySQL không có kiểu này (`TIMESTAMP` bị giới hạn đến năm 2038) | Lưu **UTC bằng `DATETIME(6)`**; giờ nghiệp vụ UTC+7 chuyển ở tầng ứng dụng | 🟡 |

## C. Enum sai so với Data Model (nên báo nhóm – không liên quan DBMS)
| # | Mục | Đang viết | Thực tế (Data Model VI.1 – code dùng) |
|---|---|---|---|
| C1 | **IV – Status Conventions**, hàng Payment | "**Pending Refunded**" | `PARTIALLY_REFUNDED` (mục I.Payment & VI.1.25 ghi đúng) |
| C2 | **IV – Status Conventions**, hàng Room; use case 16 | "**Available**" | `VACANT` |
| C3 | **IV – Status Conventions**, hàng Account | "Unactivated / Active / Locked" | `INACTIVE / ACTIVE / LOCKED` |
