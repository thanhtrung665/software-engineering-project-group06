"""Nguồn thời gian có thể thay thế (test dịch chuyển thời gian để kiểm tra hết hạn 15 phút)."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime:
        """Thời điểm hiện tại, UTC naive (cùng quy ước lưu trữ với DB)."""


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)
