"""Unit of Work: 1 transaction DB cho 1 nghiệp vụ.

Các luồng như giữ phòng / thanh toán (NFR: Reliability) phải chạy trong MỘT transaction:
lỗi giữa chừng -> rollback toàn bộ. Tầng Business dùng UoW, không tự mở session.
"""
from typing import Callable

from sqlalchemy.orm import Session

from .repositories import RoomTypeRepository


class UnitOfWork:
    session: Session
    room_types: RoomTypeRepository

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        self.room_types = RoomTypeRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type:
                self.session.rollback()
        finally:
            self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
