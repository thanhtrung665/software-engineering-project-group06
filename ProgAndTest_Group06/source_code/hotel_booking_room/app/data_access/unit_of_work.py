"""Unit of Work: 1 transaction DB cho 1 nghiệp vụ.

Các luồng như giữ phòng / thanh toán (NFR: Reliability) phải chạy trong MỘT transaction:
lỗi giữa chừng -> rollback toàn bộ. Tầng Business dùng UoW, không tự mở session.
"""
import logging
import random
import time
from typing import Callable, TypeVar

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from .repositories import (AccountRepository, BookingRepository, DepositLevelRepository,
                           InventoryRepository, PaymentRepository, PromotionRepository, RateRepository,
                           RoomTypeRepository, SettingRepository)

log = logging.getLogger(__name__)
T = TypeVar("T")


class UnitOfWork:
    session: Session
    room_types: RoomTypeRepository
    accounts: AccountRepository
    bookings: BookingRepository
    inventory: InventoryRepository
    promotions: PromotionRepository
    rates: RateRepository
    settings: SettingRepository
    deposit_levels: DepositLevelRepository
    payments: PaymentRepository

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        s = self.session
        self.room_types = RoomTypeRepository(s)
        self.accounts = AccountRepository(s)
        self.bookings = BookingRepository(s)
        self.inventory = InventoryRepository(s)
        self.promotions = PromotionRepository(s)
        self.rates = RateRepository(s)
        self.settings = SettingRepository(s)
        self.deposit_levels = DepositLevelRepository(s)
        self.payments = PaymentRepository(s)
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


_TRANSIENT_MYSQL_CODES = {1213, 1205}


def is_transient_db_error(exc: BaseException) -> bool:
    """Deadlock / serialization failure / khóa bận -> an toàn để chạy lại cả transaction."""
    if not isinstance(exc, DBAPIError):
        return False
    # MySQL trả mã lỗi dạng số trong exc.orig.args[0]:
    #   1213 = ER_LOCK_DEADLOCK (InnoDB chọn transaction này làm nạn nhân)
    #   1205 = ER_LOCK_WAIT_TIMEOUT (chờ khóa quá innodb_lock_wait_timeout)
    orig = getattr(exc, "orig", None)
    args = getattr(orig, "args", ())
    if args and isinstance(args[0], int) and args[0] in _TRANSIENT_MYSQL_CODES:
        return True
    text = str(orig or exc).lower()
    # SQLSTATE 40001 = serialization failure; "database is locked" chỉ xuất hiện ở SQLite (test)
    return any(k in text for k in ("40001", "deadlock found", "lock wait timeout", "database is locked"))


def run_in_transaction(uow_factory: Callable[[], UnitOfWork], work: Callable[[UnitOfWork], T], *,
                       max_attempts: int = 3, readonly: bool = False) -> T:
    """Chạy `work(uow)` trong 1 transaction; commit khi xong, rollback khi lỗi.

    Deadlock/serialization failure (VI.5 – Isolation) -> rollback và chạy lại từ đầu với UoW mới,
    nên `work` phải tính lại mọi thứ từ DB (không dùng số liệu đọc trước đó).
    Lỗi nghiệp vụ (BusinessError) không bị retry.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            with uow_factory() as uow:
                result = work(uow)
                if not readonly:
                    uow.commit()
                return result
        except DBAPIError as exc:
            if attempt >= max_attempts or not is_transient_db_error(exc):
                raise
            log.warning("Transient DB error (attempt %s/%s): %s", attempt, max_attempts, exc)
            time.sleep(random.uniform(0.02, 0.1) * attempt)
