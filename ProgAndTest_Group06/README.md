# ProgAndTest_Group06

Bài nộp phần **Programming & Testing** – Hotel Booking System, Group 06.
Python (OOP, kiến trúc 3 tầng) · FastAPI · SQLAlchemy · **MySQL 8.4** · Docker Compose.

## Danh mục bài nộp

| Yêu cầu | Vị trí |
|---|---|
| Source code (.py) | [`source_code/hotel_booking_room/`](source_code/hotel_booking_room/) (backend) · [`source_code/frontend/`](source_code/frontend/) (giao diện, TypeScript) |
| Testing document | [`Testing_Document_Group06.xlsx`](Testing_Document_Group06.xlsx) |
| Docker file | [`source_code/hotel_booking_room/Dockerfile`](source_code/hotel_booking_room/Dockerfile), [`source_code/frontend/Dockerfile`](source_code/frontend/Dockerfile) và [`docker-compose.yml`](source_code/hotel_booking_room/docker-compose.yml) |
| Minh chứng sử dụng công cụ & phân công | [`evidence/PhanCongNhom.png`](evidence/PhanCongNhom.png) (bảng phân công Stage 3–4) và [`evidence/Tool_Usage_and_Task_Assignment_Group06.xlsx`](evidence/Tool_Usage_and_Task_Assignment_Group06.xlsx) (phân công, đóng góp theo Git, công cụ, lịch sử commit) |

```
ProgAndTest_Group06/
├── README.md
├── Testing_Document_Group06.xlsx      Test Cases · Test Data · Test Execution
├── evidence/
│   ├── PhanCongNhom.png
│   └── Tool_Usage_and_Task_Assignment_Group06.xlsx
└── source_code/
    ├── frontend/                      Next.js 16 · React 19: trang chủ, danh sách phòng (+ Dockerfile)
    └── hotel_booking_room/
        ├── Dockerfile, docker-compose.yml   MySQL 8.4 + API + frontend
        ├── app/
        │   ├── presentation/          REST API: routers, schemas (pydantic), error handlers
        │   ├── business/              services (đặt phòng, thanh toán, hoàn tiền), frontdesk/, domain objects
        │   ├── data_access/           ORM models, repositories, UnitOfWork, frontdesk/ (SQL), gateways/ (VNPay)
        │   └── core/                  cấu hình, enum
        ├── scripts/                   init_db, verify_schema, seed, stress_oversell
        ├── sql/                       schema 40 bảng, script audit / demo khóa
        ├── tests/
        └── docs/                      ROOM_HOLD.md, TAI_LIEU_CAN_SUA.md
```

## Chức năng đã cài đặt

| Use case | Nội dung |
|---|---|
| Browse Hotel Information / View Rooms Detail | Danh sách & chi tiết loại phòng đang bán |
| Book Room | Review giá theo từng đêm (BASE/WEEKEND/HOLIDAY/SEASON), mã khuyến mãi, chọn mức cọc; tạo booking và giữ phòng 15 phút; chống bán vượt số phòng khi đặt đồng thời |
| View and Cancel Booking | Xem booking (đồng hồ đếm ngược), hủy booking đang chờ thanh toán |
| Process Payment | Thanh toán cọc qua VNPay, xác thực chữ ký callback, xử lý thanh toán trễ / trùng, hoàn tiền |
| Manage Bookings and Front Desk | Check-in (khung giờ, xếp phòng, khai báo khách), check-out (phụ phí, hóa đơn VAT), no-show (phí đêm đầu, hoàn tiền) |

## Chạy chương trình

```bash
cd source_code/hotel_booking_room
cp .env.example .env                                   # đặt DB_PASSWORD, MYSQL_ROOT_PASSWORD
docker compose up -d --build                           # MySQL 8.4 + API + frontend (http://localhost:3000)
docker compose exec app python -m scripts.init_db      # tạo schema 40 bảng
docker compose exec app python -m scripts.verify_schema
docker compose exec app python -m scripts.seed
# Swagger UI: http://localhost:8000/docs  (header X-Account-Id để xác định người dùng)
```

## Chạy test

```bash
cd source_code/hotel_booking_room
pip install -r requirements.txt
pytest -v                                              # 87 test, SQLite in-memory
docker compose exec -e RUN_MYSQL_TESTS=1 app pytest tests/test_mysql_integration.py -v   # 3 test trên MySQL thật

cd ../frontend
npm install && npx playwright install chromium
npm run test:e2e                                       # 16 test giao diện trên Chromium
```

Kết quả lần chạy ngày 2026-11-21 (Python 3.12.7): **106 test case – 103 Pass, 0 Fail, 3 chưa chạy**
(90 backend + 16 frontend; 3 test tích hợp cần MySQL thật trong Docker). Chi tiết ở sheet *Test Execution* trong Testing Document.
