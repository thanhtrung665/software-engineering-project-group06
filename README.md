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
│   ├── testing/                  Template Testing Document
│   └── interface_design/         Interface Design Description
│
├── diagrams/                     Sơ đồ (draw.io / PDF / ảnh)
│   ├── usecase_diagram/          Sơ đồ use case tổng quan + 15 sơ đồ use case chi tiết
│   ├── data_model/               ERD tổng + 7 ERD theo nhóm bảng
│   ├── dataflow_diagram/         DFD mức 0, mức 1, mức 2 (đặt phòng, thanh toán, quản lý đơn, đánh giá, quản trị)
│   └── class_diagram/            Sơ đồ lớp
│
└── ProgAndTest_Group06/          Bài nộp Programming & Testing
    ├── source_code/
    │   └── hotel_booking_room/   Python OOP · FastAPI · SQLAlchemy · MySQL 8.4 · Docker
    ├── Testing_Document_Group06.xlsx
    └── evidence/                 Minh chứng sử dụng công cụ & phân công
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

Toàn bộ phần Programming & Testing nằm trong [`ProgAndTest_Group06/`](ProgAndTest_Group06/README.md).

### `ProgAndTest_Group06/source_code/hotel_booking_room`

Python hướng đối tượng · FastAPI · SQLAlchemy · MySQL 8.4. Ba tầng `presentation → business → data_access`
(kiểm tra bởi `tests/test_architecture.py`), cùng các module `frontdesk` (lễ tân) và `payments` (VNPay).

```bash
cd ProgAndTest_Group06/source_code/hotel_booking_room
cp .env.example .env                                # đặt DB_PASSWORD, MYSQL_ROOT_PASSWORD
docker compose up -d --build                        # MySQL + API (http://localhost:8000/docs)
docker compose exec app python -m scripts.init_db   # schema 40 bảng
docker compose exec app python -m scripts.seed
pytest                                              # SQLite in-memory, không cần MySQL
```

Chi tiết: [`ProgAndTest_Group06/source_code/hotel_booking_room/README.md`](ProgAndTest_Group06/source_code/hotel_booking_room/README.md)

## Thành viên đóng góp

BinhAN1812 · Trang336 · thanhtrung665 (Hồ Thành Trung) · thunta7169 · phucbh8538-ops
