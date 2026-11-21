"""Cấu hình kết nối MySQL. Đọc từ biến môi trường để không lộ mật khẩu lên GitHub.

Khi chạy bằng docker-compose, nhóm Kiến trúc/Docker sẽ truyền các biến này vào.
Chạy trên máy cá nhân thì dùng giá trị mặc định bên dưới (sửa lại cho đúng máy bạn).
"""
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "hotel_booking"),
}


def get_connection():
    """Tạo 1 kết nối MySQL mới. Mỗi thao tác nghiệp vụ dùng 1 kết nối + 1 transaction."""
    import mysql.connector  # import trễ để unit test không cần cài MySQL

    return mysql.connector.connect(**DB_CONFIG)
