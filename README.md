# Hotel Booking System – Software Engineering Project (Group 06)

Hệ thống đặt phòng khách sạn: tìm kiếm & xem phòng, đặt phòng, thanh toán, quản lý đơn / lễ tân
(check-in, check-out, no-show), đánh giá khách sạn, quản trị người dùng và báo cáo thống kê.

Repo này tổng hợp toàn bộ tài liệu, sơ đồ và mã nguồn của nhóm từ tất cả các nhánh
(`main`, `binhan_branch`, `hongphuc_branch`, `thanhtrung_branch`, `thunta7169-patch-1`).

## Cấu trúc thư mục

```
.
├── docs/                         Tài liệu (Word)
│   ├── report/                   Báo cáo chính thức (Bao_cao_Official.docx)
│   ├── requirements/
│   │   ├── functional/           Yêu cầu chức năng
│   │   └── non_functional/       Yêu cầu phi chức năng
│   ├── use_case/                 Đặc tả use case (bản gốc + 2 bản bổ sung), mô tả sơ đồ use case
│   ├── data_design/              Thiết kế dữ liệu
│   ├── dataflow/                 Mô tả sơ đồ luồng dữ liệu (DFD)
│   └── interface_design/         Interface Design Description
│
├── diagrams/                     Sơ đồ (draw.io / PDF / ảnh)
│   ├── usecase_diagram/          Sơ đồ use case tổng quan + 15 sơ đồ use case chi tiết
│   ├── data_model/               ERD tổng + 7 ERD theo nhóm bảng
│   ├── dataflow_diagram/         DFD mức 0, mức 1, mức 2 (đặt phòng, thanh toán, quản lý đơn, đánh giá, quản trị)
│   └── class_diagram/            Sơ đồ lớp
│
└── src/                          Mã nguồn (Python, kiến trúc 3 tầng)
    ├── hotel_booking_room/       FastAPI + SQLAlchemy + SQL Server, cấu hình Docker
    └── hotel_booking_frontdesk/  Nghiệp vụ lễ tân: check-in, check-out, no-show (MySQL, CLI)
```

## Tài liệu & sơ đồ

| Nội dung | Tài liệu | Sơ đồ |
|---|---|---|
| Báo cáo tổng | `docs/report/Bao_cao_Official.docx` | |
| Yêu cầu | `docs/requirements/` | |
| Use case | `docs/use_case/` | `diagrams/usecase_diagram/` |
| Luồng dữ liệu | `docs/dataflow/Dataflow.docx` | `diagrams/dataflow_diagram/` (`.drawio` mở bằng [draw.io](https://app.diagrams.net)) |
| Dữ liệu (ERD) | `docs/data_design/THIẾT KẾ DỮ LIỆU.docx` | `diagrams/data_model/` |
| Lớp | | `diagrams/class_diagram/Class_Diagram.jpg` |
| Giao diện | `docs/interface_design/` | |

Sơ đồ use case chi tiết: Login, Register & Activate Account, Reset Password, Browse Hotel Information,
Search Rooms, View Rooms Detail, Book Room, Process Payment, View & Cancel Booking, Write Hotel Review,
Manage Bookings & Front Desk, Manage Hotel Rooms & Pricing, Manage Users & Reviews,
View Reports & Statistics, Overview.

## Mã nguồn

### `src/hotel_booking_room` – Backend chính

Python · FastAPI · SQLAlchemy · SQL Server 2022. Ba tầng `presentation → business → data_access`,
quy tắc phụ thuộc được kiểm tra bởi `tests/test_architecture.py`.

```bash
cd src/hotel_booking_room
cp .env.example .env              # đặt DB_PASSWORD
docker compose up -d              # SQL Server + app (http://localhost:8000/docs)
# hoặc chạy local:
python -m venv .venv && pip install -r requirements.txt
python -m scripts.init_db && python -m scripts.seed
uvicorn app.main:app --reload
pytest                            # dùng SQLite in-memory
```

Chi tiết: [`src/hotel_booking_room/README.md`](src/hotel_booking_room/README.md)

### `src/hotel_booking_frontdesk` – Nghiệp vụ lễ tân

`business/frontdesk_service.py` (check-in, check-out, no-show), quy tắc thuần trong `frontdesk_rules.py`.

```bash
cd src/hotel_booking_frontdesk
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Chi tiết: [`src/hotel_booking_frontdesk/README.md`](src/hotel_booking_frontdesk/README.md)

> Hai module hiện dùng hệ quản trị CSDL khác nhau (SQL Server và MySQL); cần thống nhất khi tích hợp.

## Thành viên đóng góp

BinhAN1812 · Trang336 · thanhtrung665 (Hồ Thành Trung) · thunta7169 · phucbh8538-ops
