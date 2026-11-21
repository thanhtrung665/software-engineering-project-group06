# Hotel Booking System - Group 06 (Python, Layered Architecture)

Phần của Bình An: `business/frontdesk_service.py` (check-in, check-out, no-show).

## Chạy thử
```
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python -m unittest discover -s tests -v          # test quy tắc nghiệp vụ, không cần database
python -m hotel_booking.presentation.frontdesk_cli   # cần MySQL + biến HOTEL_ID_KEY
```

## Cấu trúc 3 tầng
- `presentation/`  : giao diện (CLI demo; Admin Portal gọi thẳng service)
- `business/`      : quy tắc nghiệp vụ (`frontdesk_rules.py` thuần, `frontdesk_service.py` có transaction)
- `data_access/`   : SQL (`frontdesk_dao.py`)
