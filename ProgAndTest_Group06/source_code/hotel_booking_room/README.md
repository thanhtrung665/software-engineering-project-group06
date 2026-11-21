# Hotel Booking System – Group 06

Kiến trúc 3 tầng, hướng đối tượng (Python · FastAPI · SQLAlchemy · **MySQL 8.4**), chạy bằng Docker Compose.

```
Presentation (app/presentation)   REST API: routers, schemas (pydantic), error handlers
        │  chỉ gọi xuống
Business Logic (app/business)     services, domain objects, DTO, lỗi nghiệp vụ – KHÔNG biết HTTP, KHÔNG biết SQLAlchemy
        │  chỉ gọi xuống
Data Access (app/data_access)     models (ORM), repositories, UnitOfWork, engine/session
```

- `app/composition.py`: composition root – nơi duy nhất nối các tầng (dependency injection).
- `app/core`: cấu hình (`.env`) và enum dùng chung.
- `app/business/domain`: value object `Money`, `StayPeriod`, `RateBook`, `Availability`.

Mỗi chức năng đi qua đủ 3 tầng:

| Chức năng | Presentation | Business | Data Access |
|---|---|---|---|
| Loại phòng | `api/v1/room_types.py` | `services/room_type_service.py` | `repositories/room_type_repository.py` |
| Đặt phòng, giữ phòng | `api/v1/bookings.py` | `services/booking_hold_service.py`, `hold_*_service.py` | `repositories/booking_repository.py`, `inventory_repository.py`… |
| Thanh toán VNPay | `api/v1/payments.py` | `services/payment_service.py`, `refund_service.py` | `repositories/payment_repository.py`, `gateways/vnpay_gateway.py` |
| Lễ tân | `api/v1/front_desk.py` | `frontdesk/frontdesk_service.py`, `frontdesk_rules.py` | `frontdesk/frontdesk_dao.py`, `frontdesk/connection.py` |

Callback thanh toán dùng `HoldConfirmationService` để quyết định booking (còn hạn giữ phòng → CONFIRMED;
trễ nhưng còn phòng → RESTORED; hết phòng / đã hủy / quá mốc no-show → hoàn tiền 100%), cùng một transaction
với việc ghi PAYMENT. Cổng VNPay chỉ được gọi sau khi transaction đã commit.

## Chức năng & API

Tiền tố `/api/v1`. Tạm xác định người dùng bằng header `X-Account-Id` (`app/presentation/security.py` – thay bằng
session khi use case Login hoàn thành).

| Use case | Endpoint |
|---|---|
| Health check | `GET /health` |
| Browse Hotel Information / View Rooms Detail | `GET /room-types`, `GET /room-types/{id}` |
| Book Room – review giá, mã khuyến mãi, tiền cọc | `POST /bookings/quote` |
| Book Room – tạo booking, giữ phòng 15 phút | `POST /bookings` |
| View Booking (kèm đồng hồ đếm ngược) | `GET /bookings/{code}` |
| Cancel Booking (đang Pending Payment) | `POST /bookings/{code}/cancel-pending` |
| Process Payment – VNPay | `POST /payments/vnpay/{code}/create`, `GET /payments/vnpay/return` |
| Manage Bookings and Front Desk | `POST /front-desk/{code}/check-in`, `/check-out`, `/no-show` |

Job nền tự giải phóng phòng giữ quá hạn (cấu hình `HOLD_EXPIRY_*`). Chi tiết cơ chế giữ phòng & chống overselling:
[`docs/ROOM_HOLD.md`](docs/ROOM_HOLD.md).

## Quy tắc phụ thuộc (kiểm tra tự động bởi `tests/test_architecture.py`)
| Tầng | Không được import |
|---|---|
| presentation | `app.data_access`, `sqlalchemy`, `pymysql`, `mysql`, `requests` |
| business | `app.presentation`, `fastapi`, `starlette`, `pydantic`, `sqlalchemy`, `pymysql`, `mysql`, `requests` |
| data_access | `app.presentation`, `app.business`, `fastapi`, `starlette` |

Ngoài ra mọi mã nguồn trong `app/` phải nằm trong `presentation/`, `business/`, `data_access/` hoặc `core/`
(test `test_every_module_belongs_to_a_layer`) – không được thêm module "ngoài kiến trúc".

## Chạy bằng Docker (khuyến nghị)

```bash
cp .env.example .env          # đặt DB_PASSWORD, MYSQL_ROOT_PASSWORD (và VNPAY_*, HOTEL_ID_KEY nếu dùng)
docker compose up -d --build  # mysql + app, tự reload khi sửa code
docker compose exec app python -m scripts.init_db        # tạo/nâng cấp schema 40 bảng (không xóa dữ liệu)
docker compose exec app python -m scripts.verify_schema  # kiểm tra 40 bảng / khóa ngoại
docker compose exec app python -m scripts.seed           # dữ liệu mẫu
```

Swagger UI: http://localhost:8000/docs · Log: `docker compose logs -f app`

MySQL Workbench: Hostname `127.0.0.1` · Port `3307` (`MYSQL_HOST_PORT`) · Username `hotel_user` · Password = `DB_PASSWORD`.

> Mật khẩu MySQL chỉ được đặt ở lần tạo volume đầu tiên. Muốn reset: `docker compose down -v` (xóa toàn bộ dữ liệu).

## Chạy API trên máy (MySQL trong Docker)

```bash
python -m venv .venv && .venv\Scripts\activate     # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt                    # PyMySQL thuần Python, không cần driver ODBC
docker compose up -d mysql
# trong .env: DB_SERVER=localhost, DB_PORT=3307
python -m scripts.init_db && python -m scripts.seed
uvicorn app.main:app --reload
```

## Test

```bash
pytest                                             # SQLite in-memory, không cần MySQL
docker compose exec -e RUN_MYSQL_TESTS=1 app pytest tests/test_mysql_integration.py -v   # trên MySQL thật
docker compose exec app python -m scripts.stress_oversell --threads 24 --room-type DELUXE --rounds 3
```

| File test | Nội dung |
|---|---|
| `tests/test_room_types_api.py` | API loại phòng |
| `tests/test_booking_api.py` | API đặt phòng (quote, tạo, xem, hủy) |
| `tests/test_booking_hold.py` | Giữ phòng 15 phút, khuyến mãi, hết hạn, xác nhận thanh toán |
| `tests/test_locking.py` | Đặt phòng đồng thời không bán vượt số phòng |
| `tests/test_mysql_compat.py` | Câu SQL sinh ra hợp lệ trên MySQL, có `FOR UPDATE` |
| `tests/test_mysql_integration.py` | Khóa hàng trên MySQL thật (bật bằng `RUN_MYSQL_TESTS=1`) |
| `tests/test_payment_signature.py` | Kiểm tra chữ ký callback VNPay |
| `tests/test_architecture.py` | Quy tắc phụ thuộc giữa 3 tầng |
| `tests/test_payment_service.py` | Thanh toán VNPay: tạo giao dịch, callback, thanh toán trễ / trùng, hoàn tiền, mã HTTP |
| `tests/test_frontdesk_rules.py` | Quy tắc check-in / check-out / no-show |

## SQL

| File | Dùng để |
|---|---|
| `sql/00_schema_40_tables.sql` | Schema đầy đủ 40 bảng theo đặc tả – `scripts.init_db` dùng file này |
| `sql/01_core_models_schema.sql` | Sinh từ model SQLAlchemy (`python -m scripts.generate_sql`) |
| `sql/02_audit_overselling.sql` | Kiểm tra overselling (mong đợi 0 dòng) |
| `sql/03_demo_lock_mysql.sql` | Demo khóa hàng bằng nhiều tab Workbench |

## Thêm một chức năng mới (ví dụ Search rooms)
1. **Data Access:** model (nếu chưa có) → method trong repository → đăng ký repo trong `UnitOfWork`.
2. **Business:** DTO + service chứa quy tắc; lỗi dùng `app/business/exceptions.py`.
3. **Presentation:** schema pydantic + router, thêm vào `api/v1/router.py`; service lấy qua `composition.py`.
4. Viết test trong `tests/`.

## Quy ước & ghi chú
- Dùng `== true()` / `== false()`, **không** dùng `.is_(True/False)` (trên MySQL sinh `IS 1` – lỗi cú pháp; có test chặn).
- Mọi câu khóa hàng đi qua `app/data_access/locking.py::for_update()`; khóa theo khóa chính / cột unique.
- Deadlock (1213) / hết thời gian chờ khóa (1205) → tự chạy lại transaction tối đa 3 lần (`unit_of_work.py`).
- Database `utf8mb4` / `utf8mb4_unicode_ci`; thời gian lưu UTC (`DATETIME(6)`), nghiệp vụ tính theo Asia/Ho_Chi_Minh.
- MySQL không có partial index: email duy nhất của tài khoản chưa xóa (RBLB01) và mức cọc active duy nhất (RBLB12) dùng
  cột sinh tự động + UNIQUE. Không gán giá trị cho các cột này trong code.
- Cần MySQL **8.0.16+**. Mục tài liệu cần sửa cho khớp code: [`docs/TAI_LIEU_CAN_SUA.md`](docs/TAI_LIEU_CAN_SUA.md).
