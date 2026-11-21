"""Khóa hàng bằng SELECT ... FOR UPDATE trên MySQL/InnoDB.

SQLite chỉ dùng cho unit test và không cung cấp khóa hàng thực sự.
`populate_existing` buộc ORM nạp lại dữ liệu sau khi lấy khóa.
"""
from sqlalchemy.sql import Select


def for_update(stmt: Select, entity=None) -> Select:
    return stmt.with_for_update().execution_options(populate_existing=True)
