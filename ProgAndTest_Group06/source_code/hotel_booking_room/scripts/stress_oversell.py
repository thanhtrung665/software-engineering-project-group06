"""Kiểm chứng chống overselling trên DATABASE THẬT (MySQL/InnoDB trong Docker).

N luồng (mỗi luồng 1 kết nối riêng) cùng đặt phòng cho một đêm xa trong tương lai; số booking thành công
PHẢI đúng bằng số phòng trống, không bao giờ vượt. Sau đó tự hủy các booking thử để trả phòng.

Chạy (đã `python -m scripts.init_db` và `python -m scripts.seed`):
    python -m scripts.stress_oversell --threads 24 --room-type DELUXE --rounds 3
Thoát mã 0 = PASS, 1 = FAIL.
"""
import argparse
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select

from app.business.clock import Clock, SystemClock
from app.business.domain import StayPeriod
from app.business.dto import CreateBookingCommand, RoomSelectionDTO
from app.business.exceptions import BusinessError, RoomSoldOutError, TooManyPendingBookings
from app.business.services import BookingHoldService
from app.business.services.inventory_service import InventoryService
from app.core.timeutil import vn_today
from app.data_access.models import Account, Role
from app.data_access.unit_of_work import UnitOfWork, run_in_transaction


@dataclass
class StressReport:
    capacity: int
    threads: int
    succeeded: int = 0
    sold_out: int = 0
    other_errors: list[str] = field(default_factory=list)
    available_after: int = -1

    @property
    def passed(self) -> bool:
        return (self.succeeded == min(self.capacity, self.threads) and not self.other_errors
                and self.available_after == max(0, self.capacity - self.succeeded))


def _ensure_accounts(session_factory, count: int) -> list[int]:
    ids = []
    with session_factory() as s:
        role_id = s.scalar(select(Role.role_id).where(Role.role_code == "CUSTOMER"))
        for i in range(count):
            email = f"stress{i}@stress.local"
            acc = s.scalar(select(Account).where(Account.email == email))
            if acc is None:
                acc = Account(role_id=role_id, full_name=f"Stress {i}", email=email, phone="0900000000",
                              account_status="ACTIVE", password_hash="SEED_PLACEHOLDER")
                s.add(acc)
                s.flush()
            ids.append(acc.account_id)
        s.commit()
    return ids


def run_round(session_factory, *, threads: int, room_type_code: str, days_ahead: int, clock: Clock) -> StressReport:
    uow_factory = lambda: UnitOfWork(session_factory)          # noqa: E731
    svc = BookingHoldService(uow_factory, clock)
    inventory = InventoryService()
    accounts = _ensure_accounts(session_factory, threads)

    with uow_factory() as uow:
        rt = uow.room_types.get_by_code(room_type_code)
        if rt is None:
            raise SystemExit(f"Không có loại phòng {room_type_code}")
        room_type_id = rt.room_type_id
    check_in = vn_today(clock.now()) + timedelta(days=days_ahead)
    period = StayPeriod(check_in, check_in + timedelta(days=1))

    def free() -> int:
        return run_in_transaction(
            uow_factory, lambda u: min(inventory.availability(u, [room_type_id], period, clock.now())[room_type_id].values()),
            readonly=True)

    capacity = free()
    report = StressReport(capacity=capacity, threads=threads)
    cmd = CreateBookingCommand(period.check_in, period.check_out, (RoomSelectionDTO(room_type_id, 1, 1),),
                               Decimal(20), True)
    barrier, lock, codes = threading.Barrier(threads), threading.Lock(), []

    def attempt(account_id: int) -> None:
        barrier.wait()                                          # tất cả cùng xuất phát
        try:
            code = svc.create_booking(account_id, cmd).booking_code
            with lock:
                report.succeeded += 1
                codes.append((account_id, code))
        except RoomSoldOutError:
            with lock:
                report.sold_out += 1
        except TooManyPendingBookings:
            with lock:
                report.sold_out += 1                            # tài khoản stress còn booking cũ: không phải lỗi tồn kho
        except (BusinessError, Exception) as exc:               # noqa: BLE001
            with lock:
                report.other_errors.append(f"{type(exc).__name__}: {str(exc)[:200]}")

    with ThreadPoolExecutor(threads) as ex:
        list(ex.map(attempt, accounts))
    report.available_after = free()
    for account_id, code in codes:                              # dọn: trả phòng
        svc.cancel_pending_booking(account_id, code, "stress test cleanup")
    return report


def main() -> None:
    from app.data_access.database import get_session_factory
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threads", type=int, default=24)
    ap.add_argument("--room-type", default="DELUXE")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--days-ahead", type=int, default=400, help="đêm thử cách hôm nay bao nhiêu ngày")
    a = ap.parse_args()
    ok = True
    for n in range(1, a.rounds + 1):
        r = run_round(get_session_factory(), threads=a.threads, room_type_code=a.room_type,
                      days_ahead=a.days_ahead, clock=SystemClock())
        print(f"Vòng {n}: phòng trống={r.capacity} | luồng={r.threads} | THÀNH CÔNG={r.succeeded} | "
              f"hết phòng={r.sold_out} | còn trống sau đua={r.available_after} | lỗi khác={len(r.other_errors)} "
              f"-> {'PASS' if r.passed else 'FAIL'}")
        for e in Counter(r.other_errors).most_common(3):
            print("   ", e)
        ok &= r.passed
    print("KẾT QUẢ:", "PASS – không overselling" if ok else "FAIL – CÓ VẤN ĐỀ")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
