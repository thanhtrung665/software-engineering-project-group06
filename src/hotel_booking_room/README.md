# Hotel Booking System – Group 06

Kiến trúc 3 tầng (Python · FastAPI · SQLAlchemy · SQL Server).

```
Presentation (app/presentation)   REST API: routers, schemas (pydantic), error handlers
        │  chỉ gọi xuống
Business Logic (app/business)     services, DTO, lỗi nghiệp vụ – KHÔNG biết HTTP, KHÔNG biết SQLAlchemy
        │  chỉ gọi xuống
Data Access (app/data_access)     models (ORM), repositories, UnitOfWork, engine/session
```

`app/composition.py` là composition root: nơi duy nhất nối các tầng (dependency injection).
`app/core` chứa cấu hình và enum dùng chung.

## Quy tắc phụ thuộc (được kiểm tra tự động bởi `tests/test_architecture.py`)
| Tầng | Không được import |
|---|---|
| presentation | `app.data_access`, `sqlalchemy` |
| business | `app.presentation`, `fastapi`, `pydantic`, `sqlalchemy` |
| data_access | `app.presentation`, `app.business`, `fastapi` |

## Cài đặt
1. Cài **ODBC Driver 18 for SQL Server** trên máy (pyodbc cần driver này).
2. `python -m venv .venv` rồi kích hoạt; `pip install -r requirements.txt`
3. `cp .env.example .env` và đặt `DB_PASSWORD`.
4. `docker compose up -d` (SQL Server 2022, cổng 1433).
5. `python -m scripts.init_db` – tạo database `hotel_booking_system` + các bảng.
6. `python -m scripts.seed` – dữ liệu mẫu (tuỳ chọn).
7. `uvicorn app.main:app --reload` → http://localhost:8000/docs
8. `pytest` – test chạy bằng SQLite in-memory, không cần SQL Server.

**SSMS:** Server `localhost,1433` · Authentication: SQL Server Authentication · Login `sa` · tick *Trust server certificate*.

## Thêm một chức năng mới (ví dụ Search rooms)
1. **Data Access:** model (nếu chưa có) → method trong repository → đăng ký repo trong `UnitOfWork`.
2. **Business:** DTO + service chứa quy tắc (kiểm tra ngày, giới hạn 30 đêm/5 phòng, tính giá...); lỗi dùng `app/business/exceptions.py`.
3. **Presentation:** schema pydantic + router, thêm vào `api/v1/router.py`; service lấy qua `composition.py`.
4. Viết test trong `tests/`.

## Ghi chú
- Chuỗi dùng `NVARCHAR` (`Unicode`) để lưu tiếng Việt; database tạo với collation `Vietnamese_100_CI_AS`.
- Timestamp lưu UTC, nghiệp vụ tính theo Asia/Ho_Chi_Minh (theo tài liệu mục VI.5).
- Hiện mới có 5 bảng mẫu: role, account, hotel, room_type, room. Các bảng còn lại thêm dần theo từng use case; khi schema bắt đầu thay đổi nên dùng Alembic thay cho `create_all`.
