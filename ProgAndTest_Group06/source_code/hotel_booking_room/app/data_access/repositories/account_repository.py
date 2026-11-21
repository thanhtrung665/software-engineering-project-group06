from sqlalchemy import select

from app.data_access.locking import for_update
from app.data_access.models import Account
from .base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    model = Account

    def get_for_update(self, account_id: int) -> Account | None:
        """Khóa hàng tài khoản để tuần tự hóa các request đặt phòng của CÙNG một User
        (giới hạn 3 booking Pending Payment – UC Book room A5)."""
        return self.session.scalar(
            for_update(select(Account).where(Account.account_id == account_id), Account))
