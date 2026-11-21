"""Xác định người dùng hiện tại.

TẠM THỜI: đọc header `X-Account-Id` để chạy/test độc lập. Khi use case Login (session/token) hoàn thành,
CHỈ cần thay thân hàm này bằng việc đọc session -> account_id; các router không phải sửa.
"""
from fastapi import Header, HTTPException


def get_current_account_id(x_account_id: int | None = Header(default=None)) -> int:
    if x_account_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return x_account_id
