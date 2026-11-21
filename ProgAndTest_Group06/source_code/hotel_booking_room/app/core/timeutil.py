"""Múi giờ nghiệp vụ Asia/Ho_Chi_Minh (UTC+7, không có DST).

DB lưu UTC (naive). Dùng offset cố định để không phụ thuộc gói tzdata trên Windows.
"""
from datetime import date, datetime, time, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7), "ICT")


def to_vn(utc_naive: datetime) -> datetime:
    """UTC naive (như lưu trong DB) -> datetime có tz UTC+7."""
    return utc_naive.replace(tzinfo=timezone.utc).astimezone(VN_TZ)


def vn_today(utc_naive: datetime) -> date:
    return to_vn(utc_naive).date()


def vn_local_to_utc_naive(d: date, t: time) -> datetime:
    """Ngày + giờ theo giờ Việt Nam -> UTC naive để so sánh/lưu DB."""
    return datetime.combine(d, t, tzinfo=VN_TZ).astimezone(timezone.utc).replace(tzinfo=None)
