from datetime import datetime
from decimal import Decimal

from sqlalchemy import or_, select, true

from app.data_access.models import DepositLevel, SystemSetting
from .base import BaseRepository


class SettingRepository(BaseRepository[SystemSetting]):
    model = SystemSetting

    def get_all(self) -> dict[str, object]:
        return {s.setting_key: s.setting_value for s in self.session.scalars(select(SystemSetting))}


class DepositLevelRepository(BaseRepository[DepositLevel]):
    model = DepositLevel

    def list_active_percentages(self, now: datetime) -> list[Decimal]:
        stmt = (select(DepositLevel.percentage)
                .where(DepositLevel.is_active == true(), DepositLevel.effective_from <= now,
                       or_(DepositLevel.effective_to.is_(None), DepositLevel.effective_to > now))
                .order_by(DepositLevel.percentage))
        return list(self.session.scalars(stmt))
